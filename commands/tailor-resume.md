---
description: Rewrite the candidate's resume to target a specific job from the scored list
allowed-tools: Read, Write, Glob
---

Tailor the candidate's resume for: $ARGUMENTS

Use the `job-search:resume-tailor` skill and follow its full instructions.

**Get the candidate's profile** from the pipeline cache:

Read `.cache/active_persona.txt` to get the persona slug, then read `.cache/<persona>/profile.json` and use the `data` field.

If no cached profile exists, ask the user to share their resume first (or run `/input-resume <path>`).

**Get the scored job list** (to resolve job references by number/company):

Read `.cache/<persona>/scored_jobs.json` and use the `data` field.

Identify the target job from the argument — it can be a job number from the scored list, a company name, a job title, or a URL. If ambiguous, ask which job they mean.

**Output:**
1. Rewritten professional summary targeting this specific role
2. Reordered and rephrased skills section mirroring the job description keywords
3. Adjusted experience bullets emphasizing relevant achievements
4. ATS optimization tips for this specific job
5. Gap analysis: what the job wants that the candidate doesn't have, with suggestions

**Rules:** NEVER fabricate experience, skills, or achievements. Only rephrase and reorder what already exists. If there's a genuine gap, disclose it honestly.
