#!/usr/bin/env bash
set -euo pipefail

# --- Preflight ---
if ! command -v gum &>/dev/null; then
  echo "gum is required. Install it with: brew install gum"
  exit 1
fi
if ! command -v python3 &>/dev/null; then
  echo "python3 is required (should be pre-installed on macOS)"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

# --- Argument parsing ---
# Usage: view.sh [profile_name] [A|B|C|all]
# Profile name = any arg that isn't a grade letter
PROFILE_ARG=""
GRADE_FILTER="all"

for arg in "$@"; do
  case "${arg^^}" in
    A|B|C|D|F|ALL) GRADE_FILTER="${arg^^}" ;;
    *) PROFILE_ARG="$arg" ;;
  esac
done

# --- Resolve profile ---
# Priority: explicit arg → active_persona.txt → gum choose from available
PERSONA=$(python3 - "$ROOT" "$PROFILE_ARG" <<'PYEOF'
import sys, json
from pathlib import Path

root = Path(sys.argv[1])
arg  = sys.argv[2].strip()
cache = root / ".cache"

# Get all available profiles (dirs with scored_jobs or at least profile.json)
profiles = sorted([
    d.name for d in cache.iterdir()
    if d.is_dir() and d.name != "__pycache__" and (
        (d / "scored_jobs.json").exists() or (d / "profile.json").exists()
    )
]) if cache.exists() else []

if arg:
    # Fuzzy match: exact first, then startswith
    if arg in profiles:
        print(arg); sys.exit(0)
    matches = [p for p in profiles if p.startswith(arg.lower())]
    if matches:
        print(matches[0]); sys.exit(0)
    # Not found — still pass it through, will surface as NO_DATA
    print(arg); sys.exit(0)

# No arg: use active_persona.txt
active_file = cache / "active_persona.txt"
if active_file.exists():
    active = active_file.read_text().strip()
    if active in profiles:
        print(active); sys.exit(0)

# Multiple profiles with no active set — let shell handle the pick
if profiles:
    print("\n".join(["__PICK__"] + profiles))
else:
    print("__NONE__")
PYEOF
)

# Interactive profile picker when multiple exist and none specified
if [[ "$PERSONA" == __PICK__* ]]; then
  PROFILES=$(echo "$PERSONA" | tail -n +2)
  PERSONA=$(echo "$PROFILES" | gum choose --header "Select a profile:")
fi

if [ "$PERSONA" = "__NONE__" ] || [ -z "$PERSONA" ]; then
  gum style \
    --border rounded --padding "1 2" --border-foreground 212 \
    "No job data found." \
    "" \
    "Run /input-resume <path> first, then /tracker save to save results."
  exit 0
fi

# --- Load & merge data via python3 ---
JOBS_JSON=$(python3 - "$ROOT" "$PERSONA" "$GRADE_FILTER" <<'PYEOF'
import json, sys
from pathlib import Path

root         = Path(sys.argv[1])
persona      = sys.argv[2]
grade_filter = sys.argv[3].upper()

# Load scored jobs
scored = {}
sj_path = root / ".cache" / persona / "scored_jobs.json"
if sj_path.exists():
    data = json.loads(sj_path.read_text())
    for j in data.get("data", {}).get("jobs", []):
        scored[j["id"]] = j

# Load tracker
tracker = {}
tj_path = root / "job_tracker.json"
if tj_path.exists():
    data = json.loads(tj_path.read_text())
    for j in data.get("jobs", []):
        tracker[j["id"]] = j

if not scored and not tracker:
    print("NO_DATA")
    sys.exit(0)

# Merge: scored is primary, tracker fills in status/notes/dates
all_ids = list(scored.keys()) or list(tracker.keys())
merged = []
for jid in all_ids:
    s = scored.get(jid, {})
    t = tracker.get(jid, {})
    job = {**s, **{k: v for k, v in t.items() if k in ("status", "date_applied", "notes", "salary")}}
    if "status" not in job:
        job["status"] = "New"
    if "score" not in job and "score" in t:
        job["score"] = t["score"]
    if "grade" not in job and "grade" in t:
        job["grade"] = t["grade"]
    merged.append(job)

merged.sort(key=lambda j: j.get("score", 0), reverse=True)

if grade_filter != "ALL":
    merged = [j for j in merged if j.get("grade", "").upper() == grade_filter]

print(json.dumps(merged))
PYEOF
)

if [ "$JOBS_JSON" = "NO_DATA" ]; then
  gum style \
    --border rounded --padding "1 2" --border-foreground 212 \
    "No job data found for profile: $PERSONA" \
    "" \
    "Run /input-resume <path> first, then /tracker save to save results."
  exit 0
fi

JOB_COUNT=$(python3 -c "import json,sys; print(len(json.loads(sys.stdin.read())))" <<< "$JOBS_JSON")

if [ "$JOB_COUNT" -eq 0 ]; then
  gum style --border rounded --padding "1 2" "No jobs found for grade filter: $GRADE_FILTER"
  exit 0
fi

# --- Build TSV for gum table ---
build_tsv() {
  python3 - "$1" <<'PYEOF'
import json, sys
jobs = json.loads(sys.argv[1])
print("Score\tGrade\tCompany\tTitle\tLocation\tStatus")
for j in jobs:
    company  = j.get("company",  "")[:22]
    title    = j.get("title",    "")[:30]
    location = j.get("location", "")[:18]
    print(f"{j.get('score',0)}\t{j.get('grade','?')}\t{company}\t{title}\t{location}\t{j.get('status','New')}")
PYEOF
}

TSV=$(build_tsv "$JOBS_JSON")

# --- Main loop ---
while true; do
  gum style --foreground 212 --bold \
    "  Job Search  $(gum style --faint "profile: $PERSONA  |  $JOB_COUNT jobs  |  filter: $GRADE_FILTER")"
  echo ""

  SELECTED=$(echo "$TSV" | gum table \
    --widths 6,6,24,32,20,12 \
    --height 20 \
    --print)

  [ -z "$SELECTED" ] && break

  SEL_SCORE=$(echo "$SELECTED" | cut -f1)
  SEL_COMPANY=$(echo "$SELECTED" | cut -f3)

  JOB=$(python3 - "$JOBS_JSON" "$SEL_SCORE" "$SEL_COMPANY" <<'PYEOF'
import json, sys
jobs = json.loads(sys.argv[1])
score, company = int(sys.argv[2]), sys.argv[3].strip()
for j in jobs:
    if j.get("score") == score and j.get("company", "").startswith(company[:10]):
        print(json.dumps(j)); sys.exit(0)
for j in jobs:
    if j.get("company", "").startswith(company[:10]):
        print(json.dumps(j)); sys.exit(0)
print("{}")
PYEOF
)

  [ "$JOB" = "{}" ] && { gum style --foreground 196 "Could not find job details."; continue; }

  DETAIL=$(python3 - "$JOB" <<'PYEOF'
import json, sys
j = json.loads(sys.argv[1])

def bar(v):
    filled = round(v / 5)
    return "█" * filled + "░" * (20 - filled) + f"  {v}"

s      = j.get("scoring", {})
match  = ", ".join(j.get("matching_skills", [])) or "(none)"
miss   = ", ".join(j.get("missing_skills",  [])) or "(none)"
remote  = "Yes" if j.get("remote") else "No"
applied = j.get("date_applied") or "—"
notes   = j.get("notes") or "(none)"

lines = [
    f"{j.get('company','')} — {j.get('title','')}",
    f"Score: {j.get('score')}/100  Grade: {j.get('grade')}  |  {j.get('location','')}  |  Remote: {remote}",
    f"Status: {j.get('status','New')}  |  Applied: {applied}  |  Source: {j.get('source','')}",
    "",
    "── Scoring Breakdown ──────────────────────────",
    f"  Skill Match    {bar(s.get('skill_match',0))}",
    f"  Experience     {bar(s.get('experience_level',0))}",
    f"  Relevance      {bar(s.get('description_relevance',0))}",
    f"  Location       {bar(s.get('location',0))}",
    f"  Title Fit      {bar(s.get('title',0))}",
    "",
    f"  Matching: {match}",
    f"  Missing:  {miss}",
    "",
    f"  Verdict: {j.get('verdict','')}",
    "",
    f"  Notes: {notes}",
]
print("\n".join(lines))
PYEOF
)

  clear
  gum style --border rounded --padding "1 2" --border-foreground 212 --width 72 "$DETAIL"
  echo ""

  JOB_URL=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('url',''))" "$JOB")
  JOB_ID=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('id',''))" "$JOB")

  ACTION=$(gum choose "Open URL" "Change Status" "Back to List" "Quit")

  case "$ACTION" in
    "Open URL")
      if [ -n "$JOB_URL" ]; then
        open "$JOB_URL" 2>/dev/null || xdg-open "$JOB_URL" 2>/dev/null || echo "URL: $JOB_URL"
        gum style --foreground 212 "Opened: $JOB_URL"
        sleep 1
      else
        gum style --foreground 196 "No URL available for this job."
        sleep 1
      fi
      ;;
    "Change Status")
      NEW_STATUS=$(gum choose "New" "Reviewing" "Applied" "Interviewing" "Rejected" "Offer" "Archived")
      python3 - "$ROOT" "$JOB_ID" "$NEW_STATUS" <<'PYEOF'
import json, sys
from datetime import date
root, job_id, new_status = sys.argv[1], sys.argv[2], sys.argv[3]

tj_path = f"{root}/job_tracker.json"
try:
    with open(tj_path) as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"jobs": []}

for j in data["jobs"]:
    if j["id"] == job_id:
        j["status"] = new_status
        if new_status == "Applied" and not j.get("date_applied"):
            j["date_applied"] = str(date.today())
        break

with open(tj_path, "w") as f:
    json.dump(data, f, indent=2)
PYEOF
      gum style --foreground 212 "Status updated to: $NEW_STATUS"
      JOBS_JSON=$(python3 -c "
import json, sys
jobs = json.loads(sys.argv[1])
for j in jobs:
    if j.get('id') == sys.argv[2]:
        j['status'] = sys.argv[3]
print(json.dumps(jobs))
" "$JOBS_JSON" "$JOB_ID" "$NEW_STATUS")
      TSV=$(build_tsv "$JOBS_JSON")
      sleep 1
      ;;
    "Quit")
      break
      ;;
  esac
  clear
done
