Prepare for an interview at: $ARGUMENTS

Read `skills/interview-prep/SKILL.md` and follow its full instructions.

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

Identify the target company and role from the argument. If ambiguous, ask which job they mean.

**Output:**
1. **5 Behavioral Questions** with STAR-format answer frameworks using the candidate's ACTUAL experience
2. **5 Technical Questions** tailored to the role's tech stack and domain
3. **Talking Points** — key achievements to weave into any answer
4. **Questions to Ask the Interviewer** — thoughtful, specific to the company/role
5. **Weak Spot Mitigation** — how to address gaps or concerns honestly

**Rules:** Use the candidate's ACTUAL experience for answer frameworks, not fabricated examples. If the role mentions technologies the candidate hasn't used, flag that and suggest how to address it.

If a tracker job ID is provided, also update the tracker status:
```bash
job-tracker update <job_id> Interviewing --notes "Interview prep generated"
```
