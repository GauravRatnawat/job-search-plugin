# Job Search Assistant

Your **AI-powered job search companion**. Tell it your background, and it finds real jobs, scores every match against your profile, and helps you apply — tailored resume, cover letter, interview prep, and all.

**No dependencies. No setup. No API keys.**

## What It Does For You

1. Share your resume — paste text or drop a file path
2. AI analyzes your skills, experience, and target roles
3. AI searches the web across multiple job boards and finds 20+ real listings
4. Every job is scored /100 so you know exactly where to focus your energy
5. Get a prioritized list: jobs you should apply to today vs. stretch goals
6. Tailor your resume for any role, generate a cover letter, prep for interviews — all in one place

## Quick Start

```
# Step 1: Install (one-time)
/plugin marketplace add GauravRatnawat/job-search-plugin
/plugin install job-search@job-search-plugin

# Step 2: Drop your resume
/job-search:input-resume ~/path/to/resume.pdf

# Step 3: AI finds and scores 20+ jobs — then follow up
/job-search:tailor-resume 3          # tailor resume for job #3
/job-search:cover-letter 3           # write a cover letter
/job-search:interview-prep Google    # prep for that interview
/job-search:tracker save             # save results to tracker
/job-search:view                     # browse jobs in interactive TUI (brew install gum first)
```

## Commands

| Command | What It Does |
|---------|-------------|
| `/job-search:input-resume <path or text>` | Start here — AI finds and scores 20+ jobs matched to your profile |
| `/job-search:tailor-resume <job>` | Rewrite your resume to fit a specific role |
| `/job-search:cover-letter <job>` | Write a personalized cover letter (<400 words) |
| `/job-search:interview-prep <company>` | Get behavioral + technical questions with answer frameworks |
| `/job-search:tracker <save\|view\|update\|summary>` | Track your applications |
| `/job-search:apply <job or url>` | Get the direct link + draft an email application |
| `/job-search:view [A\|B\|C]` | Browse jobs interactively — scores, links, status updates (requires `gum`) |

## How Jobs Are Scored

Every job is rated /100 across 5 dimensions so you spend time on the right opportunities:

| What | Weight | How |
|------|--------|-----|
| Skill match | 30% | Your skills vs. what the job needs (including synonyms) |
| Experience level | 25% | Are you under/over/exactly qualified? |
| Role relevance | 25% | Does the job description actually match your domain? |
| Location | 10% | Remote, hybrid, or in your city |
| Title fit | 10% | Is this a logical next step for your career? |

Results are grouped as:
- **HIGH (70+)** — Apply today
- **MEDIUM (55–69)** — Worth it with a tailored resume
- **STRETCH (40–54)** — Aspirational, good to keep an eye on

## Privacy & Guardrails

- Never submits applications on your behalf
- Never auto-applies to LinkedIn or Indeed
- Email drafts are saved as local files only — you send them yourself
- All data stays on your machine (cached in `.cache/`, tracked in `job_tracker.json`)

## License

MIT
