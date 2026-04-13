# Job Search Assistant

This project is an AI recruiter workflow for Claude Code. Codex and other agents should use `AGENTS.md`.

## Commands

| Command | What It Does |
|---------|-------------|
| `/input-resume <path or text>` | Full pipeline: parse resume, hunt 20+ jobs, score, deliver prioritized list |
| `/tailor-resume <job>` | Rewrite resume for a specific job from the scored list |
| `/cover-letter <job>` | Write a personalized cover letter (<400 words) |
| `/interview-prep <company/role>` | Generate 5 behavioral + 5 technical questions with answer frameworks |
| `/tracker <command>` | Manage Excel tracker: save, view, update, summary |
| `/apply <job_id or url>` | Inspect and submit a supported application (email draft or Greenhouse) |

## Quick Start

1. `/input-resume` then paste or provide a file path to your resume
2. Claude runs: resume analysis, web job search, scoring, prioritized list
3. Use follow-up commands for tailoring, cover letters, interview prep, tracking, or applying

On subsequent runs, cached data is reused automatically. Check with:
```bash
python scripts/cache.py status
```

## Pipeline Cache

Results are cached per-persona between runs to avoid re-parsing resumes and re-searching for jobs:

```bash
python scripts/cache.py status                    # What's cached for active persona?
python scripts/cache.py load <stage>              # Load cached data
python scripts/cache.py save <stage> '<json>'     # Save stage data (auto-derives persona from profile name)
python scripts/cache.py clear [stage]             # Clear one or all stages
python scripts/cache.py personas                  # List all personas
python scripts/cache.py use <name>                # Switch active persona
```

Stages: `profile` (30d TTL), `search_strategy` (7d), `search_results` (2d), `scored_jobs` (2d).

## Tracker Script

```bash
python scripts/tracker.py save '[{...}]'
python scripts/tracker.py view
python scripts/tracker.py view --status Applied
python scripts/tracker.py update <id> Applied --notes "..."
python scripts/tracker.py summary
```

Tracker file: `./job_tracker.xlsx`

## Setup

```bash
pip install -r scripts/requirements.txt   # openpyxl + filelock
```

No API keys required. Web search and file reading are Claude's built-in capabilities.

## Project Structure

```
.claude/commands/           6 slash commands (input-resume, tailor-resume, cover-letter, interview-prep, tracker, apply)
skills/                     9 skill instruction documents
  resume-parser/SKILL.md
  job-hunter/SKILL.md
  job-searcher/SKILL.md
  job-scorer/SKILL.md
  job-search-analyst/SKILL.md
  application-tracker/SKILL.md
  resume-tailor/SKILL.md
  cover-letter-writer/SKILL.md
  interview-prep/SKILL.md
scripts/                    Python helper scripts
  cache.py                  Pipeline cache (save/load/status/clear)
  tracker.py                Excel tracker (save/view/update/summary)
  apply.py                  Application helper (email drafts + Greenhouse)
skill/SKILL.md              Installable Claude Code skill (orchestrator)
AGENTS.md                   Codex / generic agent instructions
plugin.md                   Claude Projects orchestrator
.cache/                     Cached pipeline state (gitignored)
```

## Install as Skill

```bash
ln -sf "$(pwd)/skill" ~/.claude/skills/job-search
```
