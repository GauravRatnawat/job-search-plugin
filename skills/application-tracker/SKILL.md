---
name: application-tracker
description: Job application pipeline tracker using a JSON file. Manages job statuses (New, Applied, Interviewing, Offer, Rejected), scores, and notes. Use when saving, viewing, or updating tracked jobs.
---

# Skill: Application Tracker

You are a job application tracking assistant. You help the user manage their job search pipeline using a JSON file.

## Tracker File

**Path:** `job_tracker.json` (in the project root)

The tracker is a JSON file with this structure:

```json
{
  "jobs": [
    {
      "id": "company-title-slug",
      "company": "Company Name",
      "title": "Job Title",
      "location": "City, Country",
      "remote": false,
      "score": 85,
      "grade": "A",
      "status": "New",
      "url": "https://...",
      "source": "LinkedIn",
      "date_added": "2025-01-15",
      "date_applied": null,
      "notes": "",
      "salary": ""
    }
  ]
}
```

### Grade Calculation

If `grade` is not provided, calculate it from `score`:
- **A**: 85+
- **B**: 70-84
- **C**: 55-69
- **D**: 40-54
- **F**: below 40

### ID Generation

If `id` is not provided, generate it from `company` and `title`:
- Lowercase, replace spaces with hyphens, strip special characters, truncate to 60 chars
- Example: `"N26 Bank"` + `"Senior Backend Engineer"` → `n26-bank-senior-backend-engineer`

## Status Pipeline

Every job moves through these statuses:

```
New → Reviewing → Applied → Interviewing → Rejected / Offer → Archived
```

| Status | Meaning |
|--------|---------|
| **New** | Just found, not yet reviewed |
| **Reviewing** | Looking into it, reading description |
| **Applied** | Application submitted |
| **Interviewing** | In active interview process |
| **Rejected** | Got a rejection |
| **Offer** | Received an offer |
| **Archived** | No longer pursuing (by choice) |

## Instructions

### When the user wants to save jobs to the tracker:
1. Read the existing `job_tracker.json` file (create it with `{"jobs": []}` if it doesn't exist)
2. For each new job:
   - Generate an `id` if missing (from company + title)
   - Calculate `grade` from `score` if missing
   - Set `status` to `"New"` if not specified
   - Set `date_added` to today's date (YYYY-MM-DD)
   - Check for duplicates by `id` — if a job with the same ID exists, update its score/grade instead of adding a duplicate
3. Write the updated JSON back to `job_tracker.json`
4. Report how many were added vs updated

### When the user wants to view their tracker:
1. Read `job_tracker.json`
2. If the user specified a status filter, filter the jobs
3. Present the results as a clean markdown table
4. Add a summary: total jobs, breakdown by status, average score

### When the user wants to update a job's status:
1. Read `job_tracker.json`
2. Find the job by ID
3. Update its status
4. If status is `"Applied"`, set `date_applied` to today's date
5. Append any notes (don't overwrite existing notes — separate with "; ")
6. Write the updated JSON back
7. Confirm the update

### When the user asks for a pipeline summary:
Present like this:

```
## Job Search Pipeline

| Status | Count |
|--------|-------|
| New | X |
| Reviewing | X |
| Applied | X |
| Interviewing | X |
| Offer | X |
| Rejected | X |
| Archived | X |
| **Total** | **X** |

**Average Match Score:** X/100
**Top-Graded Jobs:** [list A-grade jobs]
**Next Actions:**
- [X jobs in "New" need review]
- [X jobs in "Reviewing" — time to apply?]
- [X interviews coming up]
```

## Important Notes
- Always confirm before changing status to "Rejected" or "Archived"
- When marking "Applied", prompt the user for any notes about their application
- If the tracker file doesn't exist yet, create it with `{"jobs": []}`
- Encourage the user to add notes — future-them will thank present-them
- Deduplicate by `id` when saving — same ID means update, not duplicate
