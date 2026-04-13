**Before doing anything, check the pipeline cache:**

```bash
job-cache status
```

This shows the active persona and which pipeline stages have cached data.

To work with a different person's data, switch persona first:
```bash
job-cache use <name>
```

---

## If a fresh `profile` cache exists:

Skip resume parsing entirely. Load the cached profile:

```bash
job-cache load profile
```

Show the user a brief summary: "Using cached profile for [name] ([location], [level]). Last parsed: [date]. Run `/input-resume --force <path>` to re-parse."

Then jump to **Step 2** (or later, depending on what else is cached).

## If a fresh `scored_jobs` cache exists:

Skip searching and scoring. Load the cached scored jobs:

```bash
job-cache load scored_jobs
```

Present the cached prioritized list to the user. Offer: "These results are [age] old. Run `/input-resume --refresh <path>` to search for new listings."

---

## Full Pipeline (when cache is empty, stale, or `--force` flag is used)

Read the resume at $ARGUMENTS (if it's a file path, use the Read tool; if it's pasted text, analyze it directly).

### Step 1: Parse & Analyze
1. Read `skills/resume-parser/SKILL.md` and follow its instructions.
2. Extract the full structured profile + strategic assessment.
3. **Cache the result** (persona slug is auto-derived from the candidate's name):

```bash
job-cache save profile '<JSON of structured profile>'
```

The profile JSON must include: `name`, `location`, `level`, `years`, `primary_domain`, `skills` (categorized), `experience` (company/title/domain), `target_roles`, `target_domains`, `target_locations`.

The persona slug is auto-derived from the `name` field (e.g. "Gaurav Ratnawat" → `gaurav-ratnawat`). To save for a specific persona explicitly:
```bash
job-cache save profile '<json>' -p <persona-slug>
```

### Step 2: Hunt for Jobs
1. Check if `search_results` cache is fresh — if so, skip to Step 3.
2. Read `skills/job-hunter/SKILL.md` and `skills/job-searcher/SKILL.md`.
3. Generate a multi-query search strategy. Cache it:

```bash
job-cache save search_strategy '<JSON of search queries>'
```

4. Use web search to find real listings. Run at least 5-7 different searches.
5. **Cache raw results:**

```bash
job-cache save search_results '<JSON array of job listings>'
```

### Step 3: Analyze & Score
1. Check if `scored_jobs` cache is fresh — if so, skip to Step 4.
2. Read `skills/job-search-analyst/SKILL.md` to deduplicate and filter.
3. Read `skills/job-scorer/SKILL.md` to score every job /100 across 5 dimensions.
4. **Cache scored results:**

```bash
job-cache save scored_jobs '<JSON array of scored jobs>'
```

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
- `/tracker save` to save results to Excel tracker
- `/apply` to submit a supported application

---

**Flags:**
- `--force` — re-parse the resume even if cached
- `--refresh` — keep cached profile but re-search for new jobs
- No flag — use all available fresh cache, only run what's missing

**Rules:** Be honest about fit scores. Location-aware search (adapt to candidate's city/country). Fresher-aware (internships and projects count). Every job needs an application link or don't include it. Minimum 20 jobs.
