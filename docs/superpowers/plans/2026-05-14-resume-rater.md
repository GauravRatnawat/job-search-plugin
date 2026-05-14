# Resume Quality Rater Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/rate-resume` command that scores a resume across Impact, Brevity, Style, and Sections — producing an overall score, dimension breakdown, line-level rewrites, and a prioritised fix list.

**Architecture:** Two new files following existing project conventions: a lightweight command file (`.claude/commands/rate-resume.md`) that handles argument parsing and delegates to a skill file (`skills/resume-rater/SKILL.md`) that contains the full scoring rubric. No external dependencies — reads from `.cache/<persona>/profile.json` when available, falls back to raw resume input.

**Tech Stack:** Markdown instruction files, Claude native file read/write, existing `.cache/` JSON structure.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `.claude/commands/rate-resume.md` | Argument parsing, mode detection, skill invocation |
| Create | `skills/resume-rater/SKILL.md` | Scoring rubrics, output format, all logic |
| Modify | `CLAUDE.md` | Add `/rate-resume` row to the commands table |
| Modify | `job-search.html` | Add `/rate-resume` card to landing page |

---

## Task 1: Create the Slash Command

**Files:**
- Create: `.claude/commands/rate-resume.md`

- [ ] **Step 1: Create the command file**

Write this exact content to `.claude/commands/rate-resume.md`:

```markdown
Rate resume quality for: $ARGUMENTS

Use the `job-search:resume-rater` skill.

## Parse Arguments

Order of operations:

1. Extract `--resume <path>` if present → store path, set **Full Mode**; remove from args
2. Extract `--role "<value>"` if present (may be quoted) → store role override; remove from args
3. Remaining args → ignored (command takes no positional arguments)

## Detect Mode

**Full Mode** (`--resume <path>` provided):
- Read the file at that path directly as raw resume text
- Line numbers are available — use exact line references in output (e.g., `Line 14`)

**Cache Mode** (no `--resume`):
- Read `.cache/active_persona.txt` → get persona slug
- Read `.cache/<persona>/profile.json` → use as resume data
- Line numbers are NOT available — use position references in output
  (e.g., `Google — Backend Engineer, bullet 2`)
- If neither file exists: tell user "No cached profile found. Run /input-resume first,
  or provide your resume with `--resume <path>`."

## Detect Target Role

1. If `--role "<value>"` was provided → use that value
2. Else read `data.profile_assessment.recommended_roles[0]` from `profile.json` cache
3. Else if no cache → use `"General"` (no role-specific adjustments applied)

## Run Analysis

Invoke the `job-search:resume-rater` skill with:
- The resume text (Full Mode) or profile.json data (Cache Mode)
- The mode (Full or Cache)
- The resolved target role
```

- [ ] **Step 2: Verify file exists**

```bash
ls -la .claude/commands/rate-resume.md
```

Expected: file listed, non-zero size.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/rate-resume.md
git commit -m "feat: add /rate-resume slash command"
```

---

## Task 2: Create the Skill

**Files:**
- Create: `skills/resume-rater/SKILL.md`

- [ ] **Step 1: Create the skill directory and file**

```bash
mkdir -p skills/resume-rater
```

Write this exact content to `skills/resume-rater/SKILL.md`:

````markdown
---
name: resume-rater
description: Score a resume against professional quality standards across Impact, Brevity, Style, and Sections. Returns overall score, dimension sub-scores, line-level feedback with rewrites, and prioritised fix list.
---

# Skill: Resume Quality Rater

You are an expert resume coach at a top-tier company. Score the resume against the
professional standards hiring managers at FAANG, unicorn startups, and leading
consultancies expect. Be honest — a score that flatters but doesn't reflect reality
gives the user a false sense of readiness.

---

## Step 0: Load Data

### Input received from command
You will receive:
- `mode`: `"full"` (raw resume text available) or `"cache"` (profile.json data)
- `target_role`: string, e.g. `"Senior Software Engineer"` or `"General"`
- Resume data: either raw text (full mode) or parsed profile JSON fields (cache mode)

### Cache mode — extract these fields from profile.json
```
name          ← contact.name
experience[]  ← each entry: { company, title, start, end, bullets[] }
skills[]      ← flat list of skill strings
education     ← present (true) or absent (false)
certifications← present (true) or absent (false)
summary       ← present (true) or absent (false)
projects[]    ← list, may be empty
recommended_roles[] ← from profile_assessment
```

If any field is missing from the JSON, treat it as absent rather than erroring.

---

## Step 1: Score Each Dimension

Work through all four dimensions before producing any output.

---

### Dimension 1 — Impact (weight: 30%)

**What Impact measures:** Are bullets achievement-oriented? Do they show outcomes, not
just tasks? Top companies filter for candidates who drive results — not just those who
were present.

**Count from experience bullets:**

For each bullet, classify:
- **Quantified** — contains at least one number, %, $, time unit (days/weeks/hours),
  team size, or scale indicator (e.g. "2M records", "50% reduction", "3 engineers")
- **Strong verb** — starts with one of: Led, Built, Reduced, Delivered, Launched,
  Designed, Optimised, Grew, Increased, Decreased, Automated, Architected, Shipped,
  Spearheaded, Drove, Established, Scaled, Implemented (when followed by owned outcome),
  Migrated, Refactored, Mentored, Negotiated, Secured, Generated
- **Passive verb** — starts with one of: Responsible for, Worked on, Helped with,
  Assisted, Participated in, Supported, Involved in, Contributed to (without ownership),
  Tasked with, Part of

**Calculate:**
```
quantified_ratio = quantified_count / total_bullets   (0.0 – 1.0)
strong_count     = number of bullets with strong verbs
passive_count    = number of bullets with passive verbs

verb_score = clamp((strong_count - passive_count) / total_bullets × 50 + 50, 0, 100)
impact_score = clamp(round(quantified_ratio × 60 + verb_score × 0.40), 0, 100)
```

If total_bullets = 0: impact_score = 50 (cannot assess).

**Flag for feedback (up to 5 bullets, worst first):**
Select bullets that are both unquantified AND use passive verbs. Rank by severity.
For each flagged bullet, write a rewritten version that:
- Opens with a strong action verb
- Adds a quantified outcome (use real numbers if visible; if not, use "[X]%" or
  "[N] engineers" as a placeholder hint that shows the user the pattern)
- Is 10–15 words total

---

### Dimension 2 — Brevity (weight: 25%)

**What Brevity measures:** Recruiters spend 6–10 seconds on first pass. Dense, padded,
or run-on resumes get skipped. Every word should earn its place.

**Sub-score A — Resume length (start at 100):**
Estimate total word count from all sections combined.
```
>900 words  → -30
700–900     → -20
550–700     → -10
350–550     → 0 (ideal)
<350        → -10 (too sparse)
```

**Sub-score B — Bullet length (start at 100):**
For each bullet, count words:
```
>20 words   → -8 per bullet (flag these)
16–20 words → -3 per bullet
<8 words    → -3 per bullet (too terse)
10–15 words → 0 (ideal)
```
Cap total deduction at -30.

**Sub-score C — Filler phrases (start at 100):**
Detect these exact phrases (case-insensitive): "in order to", "various", " etc.",
"and more", "a wide range of", "responsible for the", "tasked with", "as well as",
"a variety of", "multiple different"
Each found → -5. Cap at -20.

**Calculate:**
```
brevity_score = clamp(round((sub_A + sub_B + sub_C) / 3), 0, 100)
```

**Flag for feedback:** all bullets >20 words. Show word count, current text, and a
trimmed rewrite in ≤15 words.

---

### Dimension 3 — Style (weight: 25%)

**What Style measures:** Consistency signals professionalism. Tense errors, personal
pronouns, and mixed date formats are patterns that make hiring managers doubt
attention to detail.

**Check A — Tense consistency (start at 100):**
For each experience entry:
- If `end` date is present and is not "Present" / "Current" → past role → all bullets
  MUST use past tense. Flag any present-tense verbs. Each violation: -8. Cap at -24.
- If `end` is "Present" / "Current" or absent → current role → tense may be present
  or past, but must be consistent within the role. Mixed tense within one role: -5.

**Check B — Personal pronouns (start at 100):**
Search all bullet and summary text for: "I ", " my ", " My ", "We ", " we ",
" our ", " Our ". Each occurrence: -5. Cap at -20.

**Check C — Date format consistency (start at 100):**
All experience and education dates must follow the same format.
Detected formats: `MM/YYYY`, `Month YYYY` (e.g., "Jan 2022"), `YYYY` only.
If more than one format found across entries: -5 per inconsistent entry. Cap at -15.

**Calculate:**
```
style_score = clamp(round((check_A + check_B + check_C) / 3), 0, 100)
```

**Flag for feedback:** each violation with exact current text and corrected version.

---

### Dimension 4 — Sections (weight: 20%)

**What Sections measures:** Missing or weak sections signal an incomplete candidate
profile. ATS systems and recruiters look for specific headings — absent sections mean
absent signal.

**Required sections (all resumes) — start at 100:**
```
Work Experience / Experience / Professional Experience → missing: -25
Skills / Technical Skills / Core Skills               → missing: -20
Education                                             → missing: -20
```

**Recommended — all roles:**
```
Professional Summary / Summary / Objective → missing: -10
```

**Role-specific additions (apply when target_role is not "General"):**
Detect role category from target_role string:
- Contains "Engineer", "Developer", "Backend", "Frontend", "Full-stack", "SWE",
  "Software", "Data", "ML", "AI", "Platform", "Infrastructure", "DevOps" →
  `Projects` section expected. Missing: -10.
- Contains "Product Manager", "PM", "Product Lead" →
  Professional Summary strongly expected. If missing: use -15 instead of -10.
- Contains "Data Scientist", "ML Engineer", "Research" →
  `Projects` or `Publications` expected. Missing: -10.

**Calculate:**
```
sections_score = clamp(100 + required_penalty + recommended_penalty + role_penalty, 0, 100)
```

**Flag for feedback:** each missing section with:
- Why it matters for the target role
- A 2–3 line example of what to write

---

## Step 2: Calculate Overall Score

```
overall = round(
  impact_score  × 0.30 +
  brevity_score × 0.25 +
  style_score   × 0.25 +
  sections_score× 0.20
)
```

Clamp to 0–100.

**Threshold labels:**
```
85–100 → ✅ Excellent — competitive at top companies
70–84  → ✅ Good — strong candidate
55–69  → ⚠️ Fair — needs improvement before applying
<55    → ❌ Weak — major issues; fix before submitting
```

---

## Step 3: Build Priority Fix List

For each flagged issue across all dimensions, calculate point impact on the
overall score and assign priority:

```
+6 pts or more → 🔴 HIGH
+3 to +5 pts   → 🟡 MED
+1 to +2 pts   → 🟢 LOW
```

Order all fixes by descending point impact.

`estimated_after = clamp(overall + sum_of_all_fix_impacts, 0, 100)`

---

## Step 4: Render Output

**Progress bar helper** (10 chars, each █ = 10 pts, round score to nearest 10):
```
score 68 → 70 → ███████░░░
score 80 → 80 → ████████░░
score 45 → 50 → █████░░░░░
```

**Line reference rules:**
- Full mode: `Line 14`
- Cache mode: `[Company] — [Title], bullet [N]` (1-indexed)

Use this exact output structure:

```
## Resume Quality Rating
**Resume:** [name]  |  **Target Role:** [target_role]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Overall Score: [overall]/100  [label]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Impact      [bar]  [impact_score]/100
Brevity     [bar]  [brevity_score]/100
Style       [bar]  [style_score]/100
Sections    [bar]  [sections_score]/100

---

### Impact ([impact_score]/100)
[2–4 sentences: what Impact measures, what you found in this resume specifically.
Mention: how many bullets are quantified out of total, what verb patterns dominate.
Explain why this matters to recruiters. Be specific, not generic.]

[For each flagged bullet, up to 5, worst first:]
⚠️  [line reference]
    Current:   "[exact bullet text]"
    Suggested: "[rewritten: strong verb + quantified outcome, ≤15 words]"

---

### Brevity ([brevity_score]/100)
[2–3 sentences: what you found. Mention estimated word count range, number of
oversized bullets, any filler phrases detected. Explain the recruiter behaviour
that makes brevity important.]

[For each bullet >20 words:]
⚠️  [line reference] ([X] words)
    Current:   "[full bullet text]"
    Suggested: "[trimmed to ≤15 words]"

[If filler phrases found:]
⚠️  Filler phrases detected: [list them, quoted]
    Remove or rephrase — they pad without adding signal.

---

### Style ([style_score]/100)
[2–3 sentences: what you found. Mention which checks passed cleanly and which had
issues. Explain why consistency matters at the hiring-manager level.]

[For each style violation:]
⚠️  [line reference]
    Current:   "[text with issue]"
    Suggested: "[corrected text]"

---

### Sections ([sections_score]/100)
[2–3 sentences: list what sections are present, what is missing, and why missing
sections hurt this specific target_role. Be role-specific.]

✅  [Section name] — present
⚠️  [Section name] — missing
    Why it matters: [1 sentence specific to target_role]
    Suggested content:
    "[2–3 line example of what to write in this section]"

---

### Priority Fixes (ordered by score impact)

| Priority | Where | Fix | Impact |
|----------|-------|-----|--------|
| 🔴 HIGH | [line ref or section] | [specific fix] | +[N] pts |
| 🟡 MED  | [line ref or section] | [specific fix] | +[N] pts |
| 🟢 LOW  | [line ref or section] | [specific fix] | +[N] pts |

Estimated score after all fixes: ~[estimated_after]/100
```
````

- [ ] **Step 2: Verify file exists and is non-empty**

```bash
wc -l skills/resume-rater/SKILL.md
```

Expected: 200+ lines.

- [ ] **Step 3: Commit**

```bash
git add skills/resume-rater/SKILL.md
git commit -m "feat: add resume-rater skill with Impact/Brevity/Style/Sections rubric"
```

---

## Task 3: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add the new command to the commands table**

In `CLAUDE.md`, find this line in the Commands table:
```
| `/market-check "<role>" --market <market>` | Score resume compatibility for a regional market (Berlin, DACH, Netherlands, etc.) |
```

Add a new row immediately after it:
```
| `/rate-resume` | Score resume quality: Impact, Brevity, Style, Sections — with line-level rewrites and fix list |
```

Also update the project structure section. Find:
```
.claude/commands/           8 slash commands (input-resume, tailor-resume, cover-letter, interview-prep, tracker, apply, ats-check, market-check)
skills/                     11 skill instruction documents
```

Replace with:
```
.claude/commands/           9 slash commands (input-resume, tailor-resume, cover-letter, interview-prep, tracker, apply, ats-check, market-check, rate-resume)
skills/                     12 skill instruction documents
```

And add to the skills list:
```
  resume-rater/SKILL.md
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: register /rate-resume command and resume-rater skill in CLAUDE.md"
```

---

## Task 4: Manual Smoke Test

**Files:** none created — this is a verification task.

This project has no automated test framework — the "test" is running the command
and verifying the output matches the spec.

- [ ] **Step 1: Prepare a minimal test resume as text**

Create a temporary file at `/tmp/test-resume.txt` with this content:

```
Jane Doe | jane@example.com | github.com/janedoe

SUMMARY
Experienced software engineer with 5 years building backend systems.

EXPERIENCE

Google — Senior Backend Engineer | Jan 2021 – Present
- Responsible for managing a team of engineers on infrastructure projects
- Worked on backend systems to improve performance
- Led migration of authentication service to OAuth 2.0, reducing login errors by 35%

Startup XYZ — Software Engineer | Mar 2018 – Dec 2020
- I helped with data pipeline development using Python and Airflow
- Assisted in building a REST API using Django
- Developed and implemented a comprehensive logging and monitoring solution that significantly improved the observability of our distributed systems architecture

SKILLS
Python, Django, Go, PostgreSQL, Docker, Kubernetes, AWS

EDUCATION
B.Sc. Computer Science — University of Example, 2018
```

- [ ] **Step 2: Run the command in full mode**

In Claude Code, run:
```
/rate-resume --resume /tmp/test-resume.txt --role "Senior Software Engineer"
```

- [ ] **Step 3: Verify output structure**

Check that the response contains ALL of the following:
- [ ] Header with `Overall Score: XX/100` inside the `━━━` border
- [ ] Four dimension bars: Impact, Brevity, Style, Sections
- [ ] `### Impact` section with explanatory paragraph AND at least one flagged bullet with Current/Suggested
- [ ] `### Brevity` section — the long bullet (line with "comprehensive logging") should be flagged
- [ ] `### Style` section — "I helped" pronoun and tense issue in Startup XYZ past role should be flagged
- [ ] `### Sections` section — should flag missing Projects for Senior SWE role
- [ ] `### Priority Fixes` table with at least 3 rows
- [ ] `Estimated score after all fixes: ~XX/100` line

- [ ] **Step 4: Run in cache mode (if profile.json cache exists)**

If `.cache/` contains an active persona with `profile.json`, run:
```
/rate-resume
```

Verify:
- [ ] Output uses `[Company] — [Role], bullet N` references (no `Line N`)
- [ ] Target role is auto-populated from cache
- [ ] Score is produced without requiring user to paste resume

- [ ] **Step 5: Cleanup**

```bash
rm /tmp/test-resume.txt
```

---

## Task 5: Update Landing Page

**Files:**
- Modify: `job-search.html`

- [ ] **Step 1: Find the commands section**

Open `job-search.html` and search for the `/market-check` card or command entry.
The landing page lists commands as cards or table rows — find the pattern used.

- [ ] **Step 2: Add the `/rate-resume` entry**

Add a new card or row following the same HTML pattern as the existing commands.
Use this content:

```
Command: /rate-resume
Label: NEW
Short description: Score your resume against professional standards — Impact,
  Brevity, Style, Sections. Get an overall score, line-level rewrites, and
  a prioritised fix list.
```

Update the command count displayed on the page (currently shows 9 commands — change
to 10) and skills count (currently shows 11 — change to 12).

- [ ] **Step 3: Commit**

```bash
git add job-search.html
git commit -m "feat: add /rate-resume to landing page, update command and skill counts"
```

---

## Done

After all tasks complete:

- `/rate-resume` command exists at `.claude/commands/rate-resume.md`
- `job-search:resume-rater` skill exists at `skills/resume-rater/SKILL.md`
- `CLAUDE.md` lists the new command and skill
- Landing page reflects 10 commands / 12 skills
- Manual smoke test passed (verified all output sections present)

**Future work (not in scope here):** Integrate rating into `/input-resume` pipeline as a compact summary after profile parse — see spec section "Future: Pipeline Integration".
