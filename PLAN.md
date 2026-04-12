# AI Job Search Assistant — MCP Server Implementation Plan

## Overview
Claude MCP server (Python, stdio transport) that parses a resume, searches job boards, ranks results, tracks everything in Excel, and (V2) auto-applies. Purely conversational — no UI.

## Reference Projects
- https://github.com/santifer/career-ops — scoring framework, portal scanning
- https://github.com/neonwatty/job-apply-plugin — ATS automation (V2 wrap)
- https://github.com/imon333/Job-apply-AI-agent — CV tailoring, pipeline pattern
- https://github.com/stickerdaniel/linkedin-mcp-server — MCP tool design patterns

## Tech Stack
- Python 3.11+, stdio MCP transport
- `mcp` (Anthropic MCP Python SDK)
- `pdfminer.six` + `pypdf` for PDF parsing
- `python-docx` for DOCX
- `sentence-transformers` (all-MiniLM-L6-v2) + `scikit-learn` for scoring
- `openpyxl` for Excel
- `httpx` async HTTP for job APIs
- `tenacity` for retries, `filelock` for Excel safety
- Job APIs: Adzuna, JSearch (RapidAPI), Arbeitnow, RemoteOK (NO LinkedIn/Indeed)

## Project Structure
```
job-search-mcp/
├── src/job_search_mcp/
│   ├── server.py                  # MCP entry point, tool registration
│   ├── tools/
│   │   ├── resume_tools.py        # parse_resume tool
│   │   ├── search_tools.py        # search_jobs tool
│   │   ├── scoring_tools.py       # rank_jobs tool
│   │   ├── tracker_tools.py       # update_tracker, view_tracker, update_job_status
│   │   └── apply_tools.py         # (V2) attempt_apply
│   ├── parsers/
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   └── resume_extractor.py
│   ├── search/
│   │   ├── base.py
│   │   ├── adzuna.py
│   │   ├── jsearch.py
│   │   ├── arbeitnow.py
│   │   └── remoteok.py
│   ├── scoring/
│   │   └── matcher.py
│   ├── tracker/
│   │   └── excel_manager.py
│   └── models/
│       ├── resume.py
│       └── job.py
├── tests/
│   ├── test_parsers.py
│   ├── test_scoring.py
│   └── test_tracker.py
├── .env.example
├── pyproject.toml
└── README.md
```

## Phase 1: MCP Scaffold + Resume Parsing
### Tasks
- [ ] Create pyproject.toml with all dependencies
- [ ] Create src/job_search_mcp/__init__.py
- [ ] Create models/resume.py — ResumeProfile dataclass
- [ ] Create models/job.py — JobListing dataclass
- [ ] Create parsers/pdf_parser.py — pdfminer.six primary, pypdf fallback
- [ ] Create parsers/docx_parser.py — python-docx extraction
- [ ] Create parsers/resume_extractor.py — raw text → ResumeProfile (regex + skills taxonomy)
- [ ] Create tools/resume_tools.py — parse_resume MCP tool
- [ ] Create server.py — MCP server entry point with parse_resume registered
- [ ] Create .env.example
- [ ] Write tests/test_parsers.py
- [ ] Verify: `python -m job_search_mcp.server` starts without error

## Phase 2: Job Search Integration
### Tasks
- [ ] Create search/base.py — abstract JobSource with async search()
- [ ] Create search/adzuna.py — Adzuna REST client
- [ ] Create search/jsearch.py — JSearch/RapidAPI client
- [ ] Create search/arbeitnow.py — Arbeitnow free EU client
- [ ] Create search/remoteok.py — RemoteOK free client
- [ ] Create tools/search_tools.py — search_jobs MCP tool (fans out async, deduplicates)
- [ ] Register search_jobs in server.py
- [ ] Write tests/test_search.py (mock HTTP)
- [ ] Verify: search returns normalized JobListing list

## Phase 3: Scoring and Ranking
### Tasks
- [ ] Create scoring/matcher.py — hybrid scorer
  - Skill match (40%): exact + fuzzy against skills taxonomy
  - Semantic similarity (40%): sentence-transformers cosine sim, TF-IDF fallback
  - Location match (10%): string match, Remote wildcard
  - Title match (10%): rapidfuzz against preferred_titles
  - Output: A-F letter grade + numeric 0-100 (inspired by career-ops)
- [ ] Create tools/scoring_tools.py — rank_jobs MCP tool
- [ ] Register rank_jobs in server.py
- [ ] Write tests/test_scoring.py
- [ ] Verify: ranked output sorted by score, min_score filter works

## Phase 4: Excel Tracker
### Tasks
- [ ] Create tracker/excel_manager.py
  - Schema: ID | Company | Title | Location | Remote | Match Score | Grade | Status | URL | Source | Date Added | Date Applied | Notes | Salary Range
  - Dedup: ID = sha256(company+title+url)[:12]
  - Status values: New | Reviewing | Applied | Interviewing | Rejected | Offer | Archived
  - Formatting: freeze row, autofilter, conditional color by status
  - File locking via filelock
- [ ] Create tools/tracker_tools.py — update_tracker, view_tracker, update_job_status
- [ ] Register tracker tools in server.py
- [ ] Write tests/test_tracker.py
- [ ] Verify: upsert adds new, updates existing, no duplicates

## Phase 5: CV Tailoring Tool (from imon333 reference)
### Tasks
- [ ] Create tools/cv_tools.py — tailor_resume(job_id, resume_profile) → tailored text
- [ ] Create tools/cv_tools.py — generate_cover_letter(job_id, resume_profile) → cover letter text
- [ ] Register in server.py
- [ ] Verify: returns tailored content string for given job

## Phase 6 (V2): Application Automation
### Tasks
- [ ] Evaluate wrapping neonwatty/job-apply-plugin
- [ ] Create tools/apply_tools.py — attempt_apply with user confirmation
- [ ] Implement EmailApplyHandler
- [ ] Implement GreenhouseHandler
- [ ] Register in server.py

## Scoring Framework (A-F, inspired by career-ops)
- A: 85-100 — Strong match, apply immediately
- B: 70-84 — Good match, worth applying
- C: 55-69 — Partial match, consider with modifications
- D: 40-54 — Weak match, low priority
- F: 0-39 — Poor match, skip

## Job APIs (MVP cost: $0)
| API | Auth | Limit |
|-----|------|-------|
| Adzuna | App ID + Key | 250/day free |
| JSearch (RapidAPI) | API Key | 500/month free |
| Arbeitnow | None | Unlimited |
| RemoteOK | None | Rate-limited |

## Risks
- API rate limits: mitigate with 24h disk cache, tenacity retries
- PDF layout complexity: pdfminer → pypdf → ask user to paste
- Auto-apply ToS: only email/Greenhouse, never LinkedIn/Indeed
- sentence-transformers 85MB: opt-in, TF-IDF always available
- Excel concurrent access: filelock + write-to-temp-then-rename
