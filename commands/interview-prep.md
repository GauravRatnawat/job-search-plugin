Prepare for an interview at: $ARGUMENTS

Use the `job-search:interview-prep` skill and follow its full instructions.

**Get the candidate's profile** from the pipeline cache:

Read `.cache/active_persona.txt` to get the persona slug, then read `.cache/<persona>/profile.json` and use the `data` field.

If no cached profile exists, ask the user to share their resume first (or run `/input-resume <path>`).

**Get the scored job list** (to resolve job references by number/company):

Read `.cache/<persona>/scored_jobs.json` and use the `data` field.

Identify the target company and role from the argument. If ambiguous, ask which job they mean.

**Output:**
1. **5 Behavioral Questions** with STAR-format answer frameworks using the candidate's ACTUAL experience
2. **5 Technical Questions** tailored to the role's tech stack and domain
3. **Talking Points** — key achievements to weave into any answer
4. **Questions to Ask the Interviewer** — thoughtful, specific to the company/role
5. **Weak Spot Mitigation** — how to address gaps or concerns honestly

**Rules:** Use the candidate's ACTUAL experience for answer frameworks, not fabricated examples. If the role mentions technologies the candidate hasn't used, flag that and suggest how to address it.

If a tracker job ID is provided, also update the tracker:
1. Read `job_tracker.json`
2. Find the job by ID and set its status to "Interviewing"
3. Add notes: "Interview prep generated"
4. Write back to `job_tracker.json`
