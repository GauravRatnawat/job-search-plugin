# Job Search Assistant

An **AI recruiter and job hunting assistant** that works with any AI coding agent. Analyzes resumes in depth, proactively hunts for jobs via web search, scores every match with fit scores out of 100, and delivers prioritized application lists with verified links.

## How to Use

This repo supports multiple AI platforms. Pick the one you use:

| Platform | Entry Point | Setup |
|----------|-------------|-------|
| **Codex** | Open the repo in Codex. It reads `AGENTS.md` automatically. | `pip install -r scripts/requirements.txt` |
| **Claude Code (standalone)** | Clone the repo and open it. Claude reads `CLAUDE.md` + `.claude/commands/`. | `pip install -r scripts/requirements.txt` |
| **Claude Code (plugin)** | `claude plugin install job-search` or `claude --plugin-dir /path/to/repo` | Auto-installed via hooks |
| **Claude Projects** | Paste `plugin.md` into project knowledge. | `pip install -r scripts/requirements.txt` |
| **Claude Code (skill)** | `ln -sf /path/to/repo/skill ~/.claude/skills/job-search` | `pip install -r scripts/requirements.txt` |
| **Cursor / Copilot / Other** | Open the repo. The agent reads `AGENTS.md`. | `pip install -r scripts/requirements.txt` |

**Prerequisites:** Python 3.8+

## What It Does

1. Share your resume (paste text or provide a file path)
2. The agent parses it, identifies your skills/strengths/gaps, and generates target roles
3. The agent searches the web with multiple queries across job boards
4. Every job is scored /100 across 5 dimensions (skill match, experience, relevance, location, title)
5. You get a prioritized list: HIGH (70+), MEDIUM (55-69), STRETCH (40-54)
6. Follow up with tailored resumes, cover letters, interview prep, and application tracking

## Commands

For Claude Code plugin users, commands are namespaced as `/job-search:<command>`.
For standalone Claude Code users, commands are available as `/<command>`.
For Codex and other agents, just ask in natural language.

| Command | What It Does |
|---------|-------------|
| `input-resume <path>` | Full pipeline: parse resume, hunt 20+ jobs, score, deliver prioritized list |
| `tailor-resume <job>` | Rewrite resume for a specific job from the scored list |
| `cover-letter <job>` | Write a personalized cover letter (<400 words) |
| `interview-prep <company>` | Generate behavioral + technical questions with STAR frameworks |
| `tracker <command>` | Manage Excel tracker: save, view, update, summary |
| `apply <job_id or url>` | Inspect and submit supported applications |

## Pipeline Cache

Results are cached per-persona between sessions to avoid re-parsing resumes and re-searching:

```bash
# Claude Code plugin users
job-cache status

# Standalone / Codex users
python scripts/cache.py status
```

Stages: `profile` (30d TTL), `search_strategy` (7d), `search_results` (2d), `scored_jobs` (2d).

Each candidate gets isolated cache storage. The persona slug is auto-derived from the profile name. Switch between candidates with `use <name>`.

## Application Automation

Supports:
- Email draft generation (`.eml` files you send yourself)
- Greenhouse-hosted application submission

Guardrails:
- Email targets create local drafts only
- Only Greenhouse real submissions require `--confirm`
- LinkedIn and Indeed are blocked
- Updates the tracker to `Applied` after a successful submission

## Scoring System

| Dimension | Weight | What It Evaluates |
|-----------|--------|-------------------|
| Skill Match | 30% | Required vs candidate skills (+ synonyms) |
| Experience Level | 25% | Seniority fit (fresher-aware) |
| Description Relevance | 25% | Domain, responsibilities, dealbreakers |
| Location | 10% | Geographic compatibility |
| Title | 10% | Job title vs experience trajectory |

## Project Structure

```
.claude-plugin/
  plugin.json                    Plugin manifest (Claude Code plugin)
.claude/commands/                Slash commands (standalone Claude Code)
  input-resume.md
  tailor-resume.md
  cover-letter.md
  interview-prep.md
  tracker.md
  apply.md
commands/                        Slash commands (Claude Code plugin)
  input-resume.md
  tailor-resume.md
  cover-letter.md
  interview-prep.md
  tracker.md
  apply.md
skills/                          9 AI skills (pipeline steps)
  resume-parser/SKILL.md
  job-hunter/SKILL.md
  job-searcher/SKILL.md
  job-scorer/SKILL.md
  job-search-analyst/SKILL.md
  application-tracker/SKILL.md
  resume-tailor/SKILL.md
  cover-letter-writer/SKILL.md
  interview-prep/SKILL.md
bin/                             CLI wrappers (auto-added to PATH by plugin)
  job-tracker                    Excel tracker I/O
  job-apply                      Application helper
  job-cache                      Pipeline cache manager
hooks/
  hooks.json                     Auto-install Python deps on session start
scripts/                         Python implementations
  tracker.py
  apply.py
  cache.py
  requirements.txt
skill/SKILL.md                   Installable Claude Code skill
AGENTS.md                        Codex / generic agent instructions
CLAUDE.md                        Standalone Claude Code instructions
plugin.md                        Claude Projects orchestrator
```

## License

MIT
