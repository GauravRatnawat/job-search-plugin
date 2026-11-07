# Resume Quality Rater Plan

## Scope

`/rate-resume` scores Impact, Brevity, Style, Sections. Show overall score, four bars, rewrites, and fix list with point gains. Keep command standalone. Pipeline hook stays future work.

## Sources

* [Design spec](../specs/2026-05-14-resume-rater-design.md) holds design and future pipeline scope.
* [Command](../../../.claude/commands/rate-resume.md) owns args, input mode, role lookup, and missing input guards.
* [Skill](../../../skills/resume-rater/SKILL.md) owns score math, weights, labels, output, and report save.
* [Host guide](../../../CLAUDE.md) lists command and skill.
* [Site](../../index.html) lists ten commands and twelve skills, with resume rating and saved reports.

## Key Choices

* Use native file read and write. No new deps.
* Read `--resume` first, then `--role`. Ignore stray positional args.
* Full mode reads raw resume and cites exact lines. Cache mode reads active persona profile and cites company, role, bullet. Never claim raw line numbers from cache.
* Role flag wins. Else use first cached recommended role. Else use `General` with no role tweaks.
* Missing profile fields count as absent. Keep missing input guards in command.
* Score all four parts before output. Keep math and caps in skill, not copied here.
* Keep honest scores. Rank fixes by point gain. Keep full report on demand.
* Future pipeline hook: run after parse, show score and top three fixes, cache rating with profile. See [future scope](../specs/2026-05-14-resume-rater-design.md#future-pipeline-integration).

## Manual Check

Keep full check below. Run on command or rubric changes. This doc trim claims no new check run.

## Task 4: Manual Smoke Test

**Files:** none created — this is a verification task.

This project has no automated test framework — the "test" is running the command
and verifying the output matches the spec.

- [ ] **Step 1: Prepare a minimal test resume as text**

Create a temporary file at `/tmp/test-resume.txt` with this content:

```
Jane Doe | jane@example.com | github.com/janedoe

SUMMARY
Experienced software engineer with 5 years building backend systems.

EXPERIENCE

Google — Senior Backend Engineer | Jan 2021 – Present
- Responsible for managing a team of engineers on infrastructure projects
- Worked on backend systems to improve performance
- Led migration of authentication service to OAuth 2.0, reducing login errors by 35%

Startup XYZ — Software Engineer | Mar 2018 – Dec 2020
- I helped with data pipeline development using Python and Airflow
- Assisted in building a REST API using Django
- Developed and implemented a comprehensive logging and monitoring solution that significantly improved the observability of our distributed systems architecture

SKILLS
Python, Django, Go, PostgreSQL, Docker, Kubernetes, AWS

EDUCATION
B.Sc. Computer Science — University of Example, 2018
```

- [ ] **Step 2: Run the command in full mode**

In Claude Code, run:
```
/rate-resume --resume /tmp/test-resume.txt --role "Senior Software Engineer"
```

- [ ] **Step 3: Verify output structure**

Check that the response contains ALL of the following:
- [ ] Header with `Overall Score: XX/100` inside the `━━━` border
- [ ] Four dimension bars: Impact, Brevity, Style, Sections
- [ ] `### Impact` section with explanatory paragraph AND at least one flagged bullet with Current/Suggested
- [ ] `### Brevity` section — the long bullet (line with "comprehensive logging") should be flagged
- [ ] `### Style` section — "I helped" pronoun and tense issue in Startup XYZ past role should be flagged
- [ ] `### Sections` section — should flag missing Projects for Senior SWE role
- [ ] `### Priority Fixes` table with at least 3 rows
- [ ] `Estimated score after all fixes: ~XX/100` line

- [ ] **Step 4: Run in cache mode (if profile.json cache exists)**

If `.cache/` contains an active persona with `profile.json`, run:
```
/rate-resume
```

Verify:
- [ ] Output uses `[Company] — [Role], bullet N` references (no `Line N`)
- [ ] Target role is auto-populated from cache
- [ ] Score is produced without requiring user to paste resume

- [ ] **Step 5: Cleanup**

```bash
rm /tmp/test-resume.txt
```

---
