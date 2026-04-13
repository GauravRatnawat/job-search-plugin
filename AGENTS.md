# Job Search Assistant

This repository is an AI recruiter workflow. It works with **any AI coding agent** — Codex, Claude Code, Cursor, Copilot, or similar.

For Claude Code plugin users, see `.claude-plugin/plugin.json`. For Claude Projects users, see `plugin.md`.

## What to Do

When the user wants to:
- analyze a resume
- find matching jobs
- score and rank opportunities
- tailor a resume
- write a cover letter
- prepare for an interview
- save or update applications in the tracker
- prepare or submit supported applications

...run the recruiter workflow described below instead of treating it like a generic coding task.

## Operating Model

- **File reading:** Use your built-in file reading to parse resumes (PDF, DOCX, TXT).
- **Web search:** Use your built-in web search to find real, current job listings.
- **Python scripts:** Use `python scripts/tracker.py` for Excel tracker I/O, `python scripts/apply.py` for supported applications, and `python scripts/cache.py` for pipeline caching.
- **Skill documents:** Read the relevant instruction files in `skills/` as you move through each pipeline step.

## Setup

```bash
pip install -r scripts/requirements.txt   # openpyxl + filelock
```

No API keys are required. Web search and file reading are your built-in capabilities.

## Pipeline Cache

Results are cached per-persona between sessions to avoid re-parsing resumes and re-searching. **Always check the cache before starting work.**

```bash
python scripts/cache.py status                    # What's cached for active persona?
python scripts/cache.py load <stage>              # Load cached data
python scripts/cache.py save <stage> '<json>'     # Save stage data (auto-derives persona from profile name)
python scripts/cache.py clear [stage]             # Clear one or all stages
python scripts/cache.py personas                  # List all personas
python scripts/cache.py use <name>                # Switch active persona
python scripts/cache.py status -p <name>          # Check a specific persona
```

Stages: `profile` (30d TTL), `search_strategy` (7d), `search_results` (2d), `scored_jobs` (2d).

## Workflow

Each step has a detailed instruction file. Read it before executing that step.

1. **Parse resume** — Read `skills/resume-parser/SKILL.md` and follow its instructions.
2. **Generate search strategy** — Read `skills/job-hunter/SKILL.md`.
3. **Execute job searches** — Read `skills/job-searcher/SKILL.md`.
4. **Deduplicate and filter** — Read `skills/job-search-analyst/SKILL.md`.
5. **Score and rank** — Read `skills/job-scorer/SKILL.md`.
6. **Deliver prioritized list** with application links.
7. **Follow-up actions** as needed:
   - `skills/application-tracker/SKILL.md` — save/view/update tracked jobs
   - `skills/resume-tailor/SKILL.md` — customize resume for a target job
   - `skills/cover-letter-writer/SKILL.md` — write a personalized cover letter
   - `skills/interview-prep/SKILL.md` — prepare for an interview

## Tracker Commands

Run from the repo root:

```bash
python scripts/tracker.py save '[{...}]'
python scripts/tracker.py view
python scripts/tracker.py view --status Applied
python scripts/tracker.py update <id> Applied --notes "Applied via career page"
python scripts/tracker.py summary
```

## Application Commands

```bash
python scripts/apply.py inspect <job_id_or_url>
python scripts/apply.py apply <job_id_or_url> --name "..." --email "..." --phone "..." --resume /path/resume.pdf --consent --confirm
```

Tracker file: `./job_tracker.xlsx`

## Output Rules

- Find at least 20 relevant jobs unless the user narrows scope further.
- Every included job needs a valid application link.
- Be honest about fit scores; do not inflate.
- Prefer fresher-friendly reasoning when the candidate is early-career.
- Default to location-aware search strategy based on the candidate's resume (city, country, willingness to relocate).
- Present final job lists in a scannable table.
- Email targets should generate local drafts instead of sending mail directly.
- Require explicit confirmation before any real submission.
- Block auto-apply for LinkedIn and Indeed.
- Support only email drafts and Greenhouse submissions.

## Project Structure

```
skills/                          9 skill instruction documents (read as pipeline steps)
  resume-parser/SKILL.md
  job-hunter/SKILL.md
  job-searcher/SKILL.md
  job-scorer/SKILL.md
  job-search-analyst/SKILL.md
  application-tracker/SKILL.md
  resume-tailor/SKILL.md
  cover-letter-writer/SKILL.md
  interview-prep/SKILL.md
scripts/                         Python helper scripts
  cache.py                       Pipeline cache (save/load/status/clear)
  tracker.py                     Excel tracker (save/view/update/summary)
  apply.py                       Application helper (email drafts + Greenhouse)
  requirements.txt               Dependencies: openpyxl, filelock
.claude/commands/                Slash commands (Claude Code standalone)
commands/                        Slash commands (Claude Code plugin)
bin/                             CLI wrappers (auto-added to PATH by plugin)
.claude-plugin/plugin.json       Claude Code plugin manifest
plugin.md                        Claude Projects orchestrator
skill/SKILL.md                   Installable Claude Code skill
```
