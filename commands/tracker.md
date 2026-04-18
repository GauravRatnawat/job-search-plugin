Manage the job application tracker. Command: $ARGUMENTS

Use the `job-search:application-tracker` skill for pipeline rules, status definitions, and the JSON file format.

**Tracker file:** `job_tracker.json`

**Supported commands** (parse from $ARGUMENTS):

- **save** — Save the scored jobs to the tracker.
  1. Check if cached scored jobs exist by reading `.cache/<persona>/scored_jobs.json`
  2. Build a JSON array from the cached (or in-conversation) job search results
  3. Read the existing `job_tracker.json` (or create it with `{"jobs": []}`)
  4. For each job: generate ID from company+title if missing, calculate grade from score if missing, set status to "New", set date_added to today
  5. Deduplicate by ID — if a job with the same ID exists, update score/grade only
  6. Write the updated tracker back to `job_tracker.json`
  7. Report how many were added vs updated

  Each job needs: `company`, `title`, `location`, `url`, `source`, `score`. The `id` and `grade` are auto-generated if missing.

- **view** [status] — View tracked jobs, optionally filtered by status:
  1. Read `job_tracker.json`
  2. Filter by status if specified
  3. Present as a markdown table

- **update** <job_id> <status> [notes] — Update a job's status:
  1. Read `job_tracker.json`
  2. Find the job by ID, update its status
  3. If status is "Applied", set `date_applied` to today
  4. Append notes (don't overwrite existing)
  5. Write back to `job_tracker.json`

  Valid statuses: New, Reviewing, Applied, Interviewing, Rejected, Offer, Archived.

- **summary** — Pipeline summary with counts by status and grade:
  1. Read `job_tracker.json`
  2. Count jobs by status and grade
  3. Calculate average score
  4. Present the summary

If $ARGUMENTS is empty or just "save", load the scored jobs from cache and save them. If ambiguous, ask what the user wants to do.
