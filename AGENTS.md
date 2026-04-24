# Job Search Assistant

This repository is an AI recruiter workflow. It works with **any AI coding agent** -- Codex, Claude Code, Cursor, Copilot, or similar. **No dependencies, no setup, no API keys.**

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

...run the recruiter workflow described below instead of treating it like a generic coding task.

## Operating Model

- **File reading:** Use your built-in file reading to parse resumes (PDF, DOCX, TXT).
- **Web search:** Use your built-in web search to find real, current job listings.
- **File I/O:** Read and write JSON files directly for the tracker (`job_tracker.json`) and pipeline cache (`.cache/`).
- **Skill documents:** Read the relevant instruction files in `skills/` as you move through each pipeline step.

No scripts, no Python, no dependencies. Everything is done through your native file read/write and web search capabilities.

## Pipeline Cache

Results are cached per-persona between sessions to avoid re-parsing resumes and re-searching. **Always check the cache before starting work.**

Cache files are stored in `.cache/<persona>/` as JSON:
- `.cache/<persona>/profile.json` -- parsed resume (fresh for 30 days)
- `.cache/<persona>/search_strategy.json` -- search queries (fresh for 7 days)
- `.cache/<persona>/search_results.json` -- raw job listings (fresh for 2 days)
- `.cache/<persona>/scored_jobs.json` -- scored results (fresh for 2 days)
- `.cache/active_persona.txt` -- the currently active persona slug

Each cache file has this structure:
```json
{
  "cached_at": "2025-01-15T10:30:00",
  "data": { ... }
}
```

Check the `cached_at` timestamp against the TTL to determine if data is still fresh.

### Multi-Persona Support

Each candidate gets their own cache directory. The persona slug is derived from the candidate's name (e.g., "Gaurav Ratnawat" becomes `gaurav-ratnawat`).

- To switch personas, write the slug to `.cache/active_persona.txt`
- To see what personas exist, list the directories in `.cache/`

## Workflow

Each step has a detailed instruction file. Read it before executing that step.

1. **Parse resume** -- Read `skills/resume-parser/SKILL.md` and follow its instructions.
2. **Generate search strategy** -- Read `skills/job-hunter/SKILL.md`.
3. **Execute job searches** -- Read `skills/job-searcher/SKILL.md`.
4. **Deduplicate and filter** -- Read `skills/job-search-analyst/SKILL.md`.
5. **Score and rank** -- Read `skills/job-scorer/SKILL.md`.
6. **Deliver prioritized list** with application links.
7. **Follow-up actions** as needed:
   - `skills/application-tracker/SKILL.md` -- save/view/update tracked jobs
   - `skills/resume-tailor/SKILL.md` -- customize resume for a target job
   - `skills/cover-letter-writer/SKILL.md` -- write a personalized cover letter
   - `skills/interview-prep/SKILL.md` -- prepare for an interview
   - `skills/ats-analyzer/SKILL.md` -- check if resume will pass ATS filtering for a target job
   - `skills/market-analyzer/SKILL.md` -- score resume compatibility for a regional market (Berlin, DACH, EU, etc.)

## Tracker

The tracker is a JSON file at `job_tracker.json`. Read `skills/application-tracker/SKILL.md` for the full schema and instructions. The agent reads and writes this file directly -- no scripts needed.

## Output Rules

- Find at least 20 relevant jobs unless the user narrows scope further.
- Every included job needs a valid application link.
- Be honest about fit scores; do not inflate.
- Prefer fresher-friendly reasoning when the candidate is early-career.
- Default to location-aware search strategy based on the candidate's resume (city, country, willingness to relocate).
- Present final job lists in a scannable table.
- For applications, provide the user with direct links. Draft emails as local text files only.
- NEVER submit applications on behalf of the user.
- NEVER auto-apply to LinkedIn or Indeed.

## Project Structure

```
skills/                          11 skill instruction documents (read as pipeline steps)
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
.claude/commands/                Slash commands (Claude Code standalone)
commands/                        Slash commands (Claude Code plugin)
.claude-plugin/plugin.json       Claude Code plugin manifest
plugin.md                        Claude Projects orchestrator
skill/SKILL.md                   Installable Claude Code skill
.cache/                          Pipeline cache (gitignored)
job_tracker.json                 Application tracker (gitignored)
```
