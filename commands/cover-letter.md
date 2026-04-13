Write a cover letter for: $ARGUMENTS

Read `skills/cover-letter-writer/SKILL.md` and follow its full instructions.

**Get the candidate's profile** from the pipeline cache (uses active persona):
```bash
job-cache load profile
```
If no cached profile exists, ask the user to share their resume first (or run `/input-resume <path>`).
To use a different person's data: `job-cache load profile -p <persona>`

**Get the scored job list** (to resolve job references by number/company):
```bash
job-cache load scored_jobs
```

Identify the target job from the argument — it can be a job number from the scored list, a company name, a job title, or a URL. If ambiguous, ask which job they mean.

**Output:** A complete, personalized cover letter under 400 words.

**Rules:**
- Use specific details from BOTH the resume and the job description
- No cliches ("I am writing to express my interest", "passionate team player", "fast learner")
- Sound human, not AI-generated
- If the candidate has a genuine gap, don't mention it — focus on strengths
- Address the hiring manager by name if known, otherwise use the team name
