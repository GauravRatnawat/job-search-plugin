---
description: Write a personalized cover letter under 400 words for a specific job
allowed-tools: Read, Write, Glob
---

Write a cover letter for: $ARGUMENTS

Use the `job-search:cover-letter-writer` skill and follow its full instructions.

**Get the candidate's profile** from the pipeline cache:

Read `.cache/active_persona.txt` to get the persona slug, then read `.cache/<persona>/profile.json` and use the `data` field.

If no cached profile exists, ask the user to share their resume first (or run `/input-resume <path>`).

**Get the scored job list** (to resolve job references by number/company):

Read `.cache/<persona>/scored_jobs.json` and use the `data` field.

Identify the target job from the argument — it can be a job number from the scored list, a company name, a job title, or a URL. If ambiguous, ask which job they mean.

**Output:** A complete, personalized cover letter under 400 words.

**Rules:**
- Use specific details from BOTH the resume and the job description
- No cliches ("I am writing to express my interest", "passionate team player", "fast learner")
- Sound human, not AI-generated
- If the candidate has a genuine gap, don't mention it — focus on strengths
- Address the hiring manager by name if known, otherwise use the team name
