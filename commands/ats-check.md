---
description: Check how well a resume passes ATS automated filtering for a specific job. Accepts job number, URL, or pasted JD. Uses cached resume by default; override with --resume <path>.
allowed-tools: Read, Write, Glob, WebSearch
---

Run ATS compatibility check for: $ARGUMENTS

Use the `job-search:ats-analyzer` skill.

## Parse Arguments

Order of operations:

1. Extract `--resume <path>` if present → store path, set **Full Mode**; remove from args
2. Classify remaining args:
   - Pure integer (e.g. `3`) → **job number**
   - Starts with `http://` or `https://` → **URL**
   - Empty → **no args**
   - Anything else → **raw JD text**

## Get Job Description

**Job number:**
1. Read `.cache/active_persona.txt` → get persona slug. If file does not exist: tell user "No scored jobs found. Run /input-resume first."
2. Read `.cache/<persona>/scored_jobs.json` → find job by position in list (1-indexed). If file does not exist: tell user "No scored jobs found. Run /input-resume first."
3. Get `url` field from that job
4. If URL contains a job/posting ID token (e.g., a numeric ID segment like `/view/12345` or `/job/67890`):
   - Use WebSearch: `"<company> <title> job description"` to find the actual JD text
   - If found: extract JD text and proceed
   - If not found or only generic results returned: ask user "I couldn't retrieve the full job description. Please paste it here."
5. If URL is a bare board root without a posting ID (e.g., `linkedin.com/jobs`, `indeed.com/jobs`, `careers.company.com` with no specific posting path): ask user to paste JD directly — "Please paste the job description for this role."

**URL:**
- Use WebSearch to fetch job posting content from that URL
- If content retrieved: proceed
- If inaccessible: ask user to paste the JD

**Raw JD text:** treat entire remaining args as the job description

**No args:** ask "Please paste the job description or provide a job number from your scored list."

## Get Resume

**Full Mode** (`--resume <path>` was provided):
- Read the file at that path directly

**Limited Mode** (no `--resume`):
- Read `.cache/active_persona.txt` → get persona slug
- Read `.cache/<persona>/profile.json` → use this as resume data
- If no cache exists: tell user "No cached profile found. Run /input-resume first, or provide your resume with --resume <path>."

## Run Analysis

Invoke the `job-search:ats-analyzer` skill with:
- The job description text
- The resume text (Full Mode) or profile.json data (Limited Mode)
- The mode (Full or Limited)
- Company name and job title (for the report header)
