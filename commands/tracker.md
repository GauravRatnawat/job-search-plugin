Manage the job application tracker. Command: $ARGUMENTS

Read `skills/application-tracker/SKILL.md` for pipeline rules and status definitions.

**Supported commands** (parse from $ARGUMENTS):

- **save** — Save the scored jobs to the tracker. First load from cache:
  ```bash
  job-cache load scored_jobs
  ```
  Build a JSON array from the cached (or in-conversation) job search results and run:
  ```bash
  job-tracker save '<JSON array>'
  ```
  Each job needs: `company`, `title` (or `role`), `location`, `url`, `source`, `score`. The `id` and `grade` are auto-generated if missing.

- **view** [status] — View tracked jobs, optionally filtered by status:
  ```bash
  job-tracker view
  job-tracker view --status Applied
  ```

- **update** <job_id> <status> [notes] — Update a job's status:
  ```bash
  job-tracker update <job_id> <status> --notes "<notes>"
  ```
  Valid statuses: New, Reviewing, Applied, Interviewing, Rejected, Offer, Archived.

- **summary** — Pipeline summary with counts by status and grade:
  ```bash
  job-tracker summary
  ```

If $ARGUMENTS is empty or just "save", load the scored jobs from cache and save them. If ambiguous, ask what the user wants to do.
