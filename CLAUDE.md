# Job Search Assistant

This project is an AI recruiter workflow for Claude Code. Codex and other agents should use `AGENTS.md`.

**No dependencies, no setup, no API keys.** Everything is done through Claude's native file read/write and web search capabilities.

## Commands

| Command | What It Does |
|---------|-------------|
| `/input-resume <path or text>` | Full pipeline: parse resume, hunt 20+ jobs, score, deliver prioritized list |
| `/tailor-resume <job>` | Rewrite resume for a specific job from the scored list |
| `/cover-letter <job>` | Write a personalized cover letter (<400 words) |
| `/interview-prep <company/role>` | Generate 5 behavioral + 5 technical questions with answer frameworks |
| `/tracker <command>` | Manage job tracker: save, view, update, summary |
| `/apply <job_id or url>` | Look up a job and help the user apply |
| `/ats-check <job>` | Estimate how likely your resume passes ATS filtering for a specific role |
| `/market-check "<role>" --market <market>` | Score resume compatibility for a regional market (Berlin, DACH, Netherlands, etc.) |

## Quick Start

1. `/input-resume` then paste or provide a file path to your resume
2. Claude runs: resume analysis, web job search, scoring, prioritized list
3. Use follow-up commands for tailoring, cover letters, interview prep, tracking, or applying

On subsequent runs, cached data is reused automatically from `.cache/`.

## Pipeline Cache

Results are cached per-persona between runs in `.cache/<persona>/` as JSON files:

| File | TTL | What It Stores |
|------|-----|---------------|
| `profile.json` | 30 days | Parsed resume: skills, experience, target roles |
| `search_strategy.json` | 7 days | Generated search queries and board list |
| `search_results.json` | 2 days | Raw job listings from web searches |
| `scored_jobs.json` | 2 days | Scored and ranked job list |

Each file is a JSON object with `cached_at` (ISO timestamp) and `data` (the payload). The active persona slug is stored in `.cache/active_persona.txt`.

## Tracker

The job tracker is a JSON file at `job_tracker.json`. See `skills/application-tracker/SKILL.md` for the full schema. Claude reads and writes this file directly.

## Project Structure

```
.claude/commands/           8 slash commands (input-resume, tailor-resume, cover-letter, interview-prep, tracker, apply, ats-check, market-check)
skills/                     11 skill instruction documents
  resume-parser/SKILL.md
  job-hunter/SKILL.md
  job-searcher/SKILL.md
  job-scorer/SKILL.md
  job-search-analyst/SKILL.md
  application-tracker/SKILL.md
  resume-tailor/SKILL.md
  cover-letter-writer/SKILL.md
  interview-prep/SKILL.md
  ats-analyzer/SKILL.md
  market-analyzer/SKILL.md
skill/SKILL.md              Installable Claude Code skill (orchestrator)
AGENTS.md                   Codex / generic agent instructions
plugin.md                   Claude Projects orchestrator
.cache/                     Cached pipeline state (gitignored)
job_tracker.json            Application tracker (gitignored)
```

## Install as Skill

```bash
ln -sf "$(pwd)/skill" ~/.claude/skills/job-search
```
