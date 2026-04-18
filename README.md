# Job Search Assistant

An **AI recruiter and job hunting assistant** that works with any AI coding agent. Analyzes resumes in depth, proactively hunts for jobs via web search, scores every match /100, and delivers prioritized application lists with verified links.

**No dependencies. No setup. No API keys.** Pure skill instructions + native file I/O.

## Quick Start (Claude Code)

```
# 1. Install the plugin
/plugin marketplace add GauravRatnawat/job-search-plugin
/plugin install job-search@job-search-plugin

# 2. Run the full pipeline
/job-search:input-resume path/to/resume.pdf

# 3. Follow up
/job-search:tailor-resume <job number>
/job-search:cover-letter <job number>
/job-search:interview-prep <company>
```

## Install on Any Platform

| Platform | How to Install | How to Use |
|----------|---------------|------------|
| **Claude Code (plugin)** | `/plugin marketplace add GauravRatnawat/job-search-plugin` then `/plugin install job-search@job-search-plugin` | `/job-search:<command>` |
| **Claude Code (skill)** | `ln -sf /path/to/repo/skill ~/.claude/skills/job-search` | `/job-search` then chat |
| **Claude Code (standalone)** | Clone repo, run `claude` from inside it | `/<command>` |
| **Claude Projects** | Paste `plugin.md` into project knowledge | Chat naturally |
| **Codex / Cursor / Copilot** | Clone repo, open it in your agent | Chat naturally — agent reads `AGENTS.md` |

## What It Does

1. Share your resume (paste text or provide a file path)
2. The agent parses it, identifies your skills/strengths/gaps, and generates target roles
3. The agent searches the web with multiple queries across job boards
4. Every job is scored /100 across 5 dimensions (skill match, experience, relevance, location, title)
5. You get a prioritized list: HIGH (70+), MEDIUM (55-69), STRETCH (40-54)
6. Follow up with tailored resumes, cover letters, interview prep, and application tracking

## Commands

| Plugin (`/job-search:`) | Standalone (`/`) | What It Does |
|------------------------|-----------------|--------------|
| `/job-search:input-resume <path>` | `/input-resume <path>` | Full pipeline: parse resume, hunt 20+ jobs, score, deliver prioritized list |
| `/job-search:tailor-resume <job>` | `/tailor-resume <job>` | Rewrite resume for a specific job from the scored list |
| `/job-search:cover-letter <job>` | `/cover-letter <job>` | Write a personalized cover letter (<400 words) |
| `/job-search:interview-prep <company>` | `/interview-prep <company>` | Generate behavioral + technical questions with STAR frameworks |
| `/job-search:tracker <command>` | `/tracker <command>` | Manage tracker: save, view, update, summary |
| `/job-search:apply <job_id or url>` | `/apply <job_id or url>` | Help with an application (provide URL, draft email) |

For Codex and other agents, just ask in natural language.

## Pipeline Cache

Results are cached per-persona between sessions as JSON files in `.cache/<persona>/`:

| File | TTL | Content |
|------|-----|---------|
| `profile.json` | 30 days | Parsed resume profile |
| `search_strategy.json` | 7 days | Generated search queries |
| `search_results.json` | 2 days | Raw job listings |
| `scored_jobs.json` | 2 days | Scored and ranked results |

Each candidate gets isolated cache storage. The persona slug is derived from the profile name.

## Application Support

The agent helps you apply by:
- Providing direct application URLs
- Showing your profile details for easy copy-pasting
- Drafting email applications as local text files
- Suggesting tailored resumes and cover letters for each role

Guardrails:
- NEVER submits applications on your behalf
- NEVER auto-applies to LinkedIn or Indeed
- Email applications create local drafts only

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
.claude/commands/                Slash commands (standalone Claude Code)
commands/                        Slash commands (Claude Code plugin)
.claude-plugin/plugin.json       Plugin manifest
.claude-plugin/marketplace.json  Marketplace definition (enables /plugin marketplace add)
skill/SKILL.md                   Installable Claude Code skill
AGENTS.md                        Codex / generic agent instructions
CLAUDE.md                        Standalone Claude Code instructions
plugin.md                        Claude Projects orchestrator
.cache/                          Pipeline cache (gitignored)
job_tracker.json                 Application tracker (gitignored)
```

## License

MIT
