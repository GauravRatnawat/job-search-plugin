---
description: Parse a resume, hunt 20+ jobs via web search, score every match /100, and deliver a prioritized application list
allowed-tools: Read, Write, Glob, WebSearch
---

**Before doing anything, check the pipeline cache.**

Read the file `.cache/active_persona.txt` to get the current persona slug. If it doesn't exist, that's fine — a new persona will be created from the resume.

Then check if cached data exists for the active persona by reading files in `.cache/<persona>/`:
- `.cache/<persona>/profile.json` — parsed resume (fresh for 30 days)
- `.cache/<persona>/search_strategy.json` — search queries (fresh for 7 days)
- `.cache/<persona>/search_results.json` — raw job listings (fresh for 2 days)
- `.cache/<persona>/scored_jobs.json` — scored results (fresh for 2 days)

Each cache file has this structure:
```json
{
  "cached_at": "2025-01-15T10:30:00",
  "data": { ... }
}
```

Check the `cached_at` timestamp against the TTL to determine freshness.

To work with a different person's data, write their persona slug to `.cache/active_persona.txt`.

---

## If a fresh `profile` cache exists:

Skip resume parsing entirely. Read `.cache/<persona>/profile.json` and use the `data` field.

Show the user a brief summary: "Using cached profile for [name] ([location], [level]). Last parsed: [date]. Run `/input-resume --force <path>` to re-parse."

Then jump to **Step 2** (or later, depending on what else is cached).

## If fresh `scored_jobs` cache exists:

Skip searching and scoring. Read `.cache/<persona>/scored_jobs.json` and use it.

Present the cached prioritized list to the user. Offer: "These results are [age] old. Run `/input-resume --refresh <path>` to search for new listings."

---

## Full Pipeline (when cache is empty, stale, or `--force` flag is used)

Read the resume at $ARGUMENTS (if it's a file path, use the Read tool; if it's pasted text, analyze it directly).

### Step 1: Parse & Analyze
1. Use the `job-search:resume-parser` skill and follow its instructions.
2. Extract the full structured profile + strategic assessment.
3. **Cache the result** — derive the persona slug from the candidate's name (e.g. "Gaurav Ratnawat" → `gaurav-ratnawat`):
   - Create directory `.cache/<persona>/` if it doesn't exist
   - Write `.cache/<persona>/profile.json`:
     ```json
     {
       "cached_at": "<current ISO timestamp>",
       "data": { <structured profile JSON> }
     }
     ```
   - Write the persona slug to `.cache/active_persona.txt`

The profile JSON must include: `name`, `location`, `level`, `years`, `primary_domain`, `skills` (categorized), `experience` (company/title/domain), `target_roles`, `target_domains`, `target_locations`.

### Step 2: Hunt for Jobs
1. Check if `.cache/<persona>/search_results.json` exists and is fresh — if so, skip to Step 3.
2. Use the `job-search:job-hunter` skill and `job-search:job-searcher` skill.
3. Generate a multi-query search strategy. Cache it by writing `.cache/<persona>/search_strategy.json`.
4. Use web search to find real listings. Run at least 5-7 different searches.
5. Cache raw results by writing `.cache/<persona>/search_results.json`.

### Step 3: Analyze & Score
1. Check if `.cache/<persona>/scored_jobs.json` exists and is fresh — if so, skip to Step 4.
2. Use the `job-search:job-search-analyst` skill to deduplicate and filter.
3. Use the `job-search:job-scorer` skill to score every job /100 across 5 dimensions.
4. Cache scored results by writing `.cache/<persona>/scored_jobs.json`.

### Step 4: Deliver Prioritized List
Present 20+ jobs organized as:
- **HIGH PROBABILITY (Score 70+)** — Apply immediately
- **MEDIUM PROBABILITY (Score 55-69)** — Worth trying with tailored resume
- **STRETCH ROLES (Score 40-54)** — Aspirational

Every job must include: company, role, location, type, fit score /100, and application link.

### Step 5: Suggest Next Steps
Recommend application order, skills to learn, and offer follow-up actions:
- `/tailor-resume` to customize resume for a specific job
- `/cover-letter` to write a personalized cover letter
- `/interview-prep` to prepare for an interview
- `/tracker save` to save results to the tracker
- `/apply` to submit a supported application

---

**Flags:**
- `--force` — re-parse the resume even if cached
- `--refresh` — keep cached profile but re-search for new jobs
- No flag — use all available fresh cache, only run what's missing

**Rules:** Be honest about fit scores. Location-aware search (adapt to candidate's city/country). Fresher-aware (internships and projects count). Every job needs an application link or don't include it. Minimum 20 jobs.
