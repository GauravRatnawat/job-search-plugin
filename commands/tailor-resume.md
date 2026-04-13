Tailor the candidate's resume for: $ARGUMENTS

Read `skills/resume-tailor/SKILL.md` and follow its full instructions.

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

**Output:**
1. Rewritten professional summary targeting this specific role
2. Reordered and rephrased skills section mirroring the job description keywords
3. Adjusted experience bullets emphasizing relevant achievements
4. ATS optimization tips for this specific job
5. Gap analysis: what the job wants that the candidate doesn't have, with suggestions

**Rules:** NEVER fabricate experience, skills, or achievements. Only rephrase and reorder what already exists. If there's a genuine gap, disclose it honestly.
