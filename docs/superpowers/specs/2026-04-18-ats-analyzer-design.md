# ATS Compatibility Analyzer — Design Spec

**Date:** 2026-04-18  
**Revised:** 2026-04-19  
**Status:** Approved (v2 — post-review)

---

## Context

Most companies use Applicant Tracking Systems (ATS) — Workday, Greenhouse, Taleo, Lever — to automatically filter resumes before a human ever reads them. Studies estimate ~75% of resumes get rejected at this stage. The job-search plugin currently scores jobs semantically (human-like fit scoring) but has no ATS-specific analysis.

This feature adds a dedicated ATS compatibility check: given a job description and a resume, estimate how likely the resume is to pass automated filtering and provide actionable fixes.

**This is distinct from the existing job scorer:**

| | Job Scorer | ATS Analyzer |
|---|---|---|
| Perspective | Human recruiter — semantic, holistic | Machine parser — exact, mechanical |
| Keyword matching | Synonym-aware | Exact/near-exact only |
| Formatting | Ignored | Core concern |
| Output | "Should you apply?" | "Will the software let you through?" |

---

## Architecture

### Approach

Standalone skill + command. No changes to existing pipeline behavior. The ATS check is an on-demand diagnostic for a specific job the user is serious about.

**Intended workflow:**
```
/input-resume          → find & score 20+ jobs
/ats-check <job>       → diagnose ATS compatibility for a target role
/tailor-resume <job>   → fix the resume
/ats-check <job>       → re-run to confirm improvement
```

**Files added:**

| File | Action |
|------|--------|
| `skills/ats-analyzer/SKILL.md` | New — core ATS analysis logic |
| `commands/ats-check.md` | New — plugin slash command (with frontmatter) |
| `.claude/commands/ats-check.md` | New — standalone slash command (no frontmatter) |
| `README.md` | Update — add `ats-check` to commands table |
| `CLAUDE.md` | Update — add `ats-check` to commands table |
| `skill/SKILL.md` | Update — add `ats-analyzer` to skill table |
| `plugin.md` | Update — add `ats-analyzer` to skill list |
| `AGENTS.md` | Update — add `ats-analyzer` to skill inventory |

---

## Two-Mode Operation (Issue #1)

The depth of ATS analysis depends on what resume input is available.

### Full Mode — source resume file provided

Triggered when: `--resume <path>` is passed OR user pastes raw resume text.

Can check:
- ✅ Keyword match
- ✅ Section header recognition (detects "Technical Expertise" vs "Technical Skills")
- ✅ Formatting compliance (table layout, column structure, symbols)
- ✅ Structural completeness
- ✅ Title/role alignment

### Limited Mode — cached `profile.json` only

Triggered when: no `--resume` flag, only `profile.json` is available.

Can check:
- ✅ Keyword match (against skills, experience bullets in profile)
- ✅ Structural completeness (contact info, dates, sections present in cache)
- ✅ Title/role alignment
- ⚠️ Section recognition — **partial only**: can verify Skills, Experience, Education data exists in profile, but cannot detect non-standard header names
- ❌ Formatting compliance — cannot detect tables, columns, graphics from normalized JSON

**Required behavior:** When running in Limited Mode, the output must display a banner:

```
⚠️  LIMITED MODE — using cached profile only
   Formatting and section header checks unavailable.
   For full analysis: /ats-check <job> --resume ~/path/to/resume.pdf
```

Profile fields available in Limited Mode:
- `contact` — name, email, phone (structural completeness)
- `skills` — flat list (keyword matching)
- `experience[]` — company, title, dates, bullets (keyword + title alignment + date format check)
- `education` — present/absent (section completeness)
- `certifications` — present/absent
- `profile_assessment` — target roles (title alignment)

---

## Job Description Resolution (Issue #2)

`scored_jobs.json` contains summaries only — no raw JD text. The `url` field often points to generic careers pages, ATS board URLs, or search results.

### Resolution order for `$ARGUMENTS`:

1. **Job number (e.g. `3`)** — look up job in `scored_jobs.json` → get `url`
   - Attempt `WebSearch` using `"<company> <title> job description"` to find the actual posting
   - If found: extract JD text and proceed
   - If not found or generic page: **ask the user to paste the job description**

2. **URL** — use `WebSearch` to fetch job posting content from that URL
   - If content retrieved: proceed
   - If inaccessible: ask the user to paste the JD

3. **Raw text** — treat everything in `$ARGUMENTS` (after stripping `--resume` flag) as the JD directly

4. **No arguments** — ask the user: "Please paste the job description or provide a job number."

**Ambiguous case — job number but generic URL:**  
If job `url` is a board link (`linkedin.com/jobs`, `indeed.com/jobs`, `careers.company.com` without a specific posting ID), skip URL resolution and ask the user to paste the JD directly rather than searching.

---

## Argument Parsing (Issue #5)

Parse `$ARGUMENTS` in this order:

1. **Extract `--resume <path>`** — if present, store path separately; remove from args
2. **Remaining args** — classify:
   - Pure integer → job number
   - Starts with `http://` or `https://` → URL
   - Anything else → raw JD text (may be a job title, company name, or pasted description)

**Explicit examples:**

| Input | Behavior |
|-------|----------|
| `/ats-check 3` | Job #3 from cache; cached resume |
| `/ats-check 3 --resume ~/resume.docx` | Job #3; provided resume file |
| `/ats-check https://company.com/job/123` | Fetch URL; cached resume |
| `/ats-check --resume ~/resume.pdf https://co.com/job` | Fetch URL; provided resume |
| `/ats-check Senior Backend at Stripe` | Treat as raw JD text; cached resume |
| `/ats-check` (no args) | Ask user for JD; cached resume |
| `/ats-check 3` but URL is generic | Search for JD; if not found, ask user to paste |

---

## Scoring Model

Five factors, weighted:

| Factor | Weight | Full Mode | Limited Mode |
|--------|--------|-----------|--------------|
| Keyword Match | 40% | ✅ | ✅ |
| Section Recognition | 20% | ✅ | ⚠️ partial |
| Formatting Compliance | 20% | ✅ | ❌ skipped |
| Structural Completeness | 10% | ✅ | ✅ |
| Title/Role Alignment | 10% | ✅ | ✅ |

**In Limited Mode:** Formatting Compliance (20%) is skipped and its weight redistributed: +10% to Keyword Match (now 50%), +5% to Section Recognition (now 25%), +5% to Structural Completeness (now 15%).

**ATS Pass Thresholds:**
- **75%+** → ✅ LIKELY PASS
- **55–74%** → ⚠️ AT RISK
- **<55%** → ❌ LIKELY FILTERED

### 1. Keyword Match

Extract from JD:
- **Required keywords:** skills, tools, technologies in core responsibilities or marked "required"/"must have"
- **Preferred keywords:** "nice to have", "preferred", "bonus"

Match against resume using **exact and near-exact only** (no synonyms — ATS is literal):
- Exact: "Kubernetes" in resume
- Near-exact: abbreviation variants ("CI/CD" ↔ "continuous integration"), plurals

Score: `(required_found / required_total) × 100`  
Bonus: each preferred keyword found adds 2 pts, capped at +10

### 2. Section Recognition

Standard ATS-readable headers:

| Standard (recognized) | Non-standard (may fail) |
|----------------------|------------------------|
| Work Experience / Experience | My Journey, Career History |
| Education | Academic Background |
| Skills / Technical Skills | Technical Expertise, My Toolkit |
| Summary / Professional Summary / Objective | About Me, Who I Am |
| Certifications | Credentials, Achievements |

Full Mode: detect from raw resume text.  
Limited Mode: confirm sections exist in profile JSON, but cannot detect header naming issues.

### 3. Formatting Compliance *(Full Mode only)*

| Pattern | Severity |
|---------|----------|
| Skills in table/grid | HIGH |
| Multiple columns | HIGH |
| Contact info in document header/footer | MEDIUM |
| Graphics, icons, logos | MEDIUM |
| Excessive non-standard symbols (★, →) as bullets | LOW |
| Paragraph-style experience (no bullets) | LOW |

### 4. Structural Completeness

- Contact info present (name, email, phone)
- Dates formatted consistently (MM/YYYY preferred)
- Each experience entry has company + title + dates
- Skills section and Experience section both present

### 5. Title/Role Alignment

Compare candidate's most recent titles + target roles against JD title:
- Exact/near-exact → 100
- Related → 70
- Adjacent → 40
- Unrelated → 10

---

## Output Format

```
## ATS Compatibility Report
**Job:** [Company] — [Job Title]
**Resume:** [candidate name] (Full Mode / Limited Mode)

⚠️  LIMITED MODE — using cached profile only            ← show only in Limited Mode
   For full analysis: /ats-check <job> --resume ~/resume.pdf

---

**Estimated ATS Pass Rate: XX%**  [✅ LIKELY PASS / ⚠️ AT RISK / ❌ LIKELY FILTERED]

### Keyword Match  (X/Y required — Z%)
✅ Found:             [keyword1], [keyword2], ...
❌ Missing:           [keyword1], [keyword2], ...
⭐ Preferred found:   [keyword1], ...
⭐ Preferred missing: [keyword1], ...

### Section Check
✅ Work Experience — recognized
✅ Education — recognized
⚠️  "Technical Expertise" → rename to "Technical Skills"   ← Full Mode only
❌ No Summary/Objective section

### Formatting  ← Full Mode only, omit section in Limited Mode
✅ No table layout detected
⚠️  Skills in table format — ATS may skip this content
⚠️  Contact details in document header

### Structural Completeness
✅ Contact info present
✅ Consistent date formats
⚠️  2 experience entries missing end dates

---

### Priority Fixes (ordered by ATS impact)

| Priority | Fix | Impact |
|----------|-----|--------|
| 🔴 HIGH | Add "microservices" to N26 experience bullet | +6 pts |
| 🔴 HIGH | Add "CI/CD" to Skills section | +6 pts |
| 🟡 MEDIUM | Rename "Technical Expertise" → "Technical Skills" | +4 pts |
| 🟡 MEDIUM | Move skills from table to plain text list | +4 pts |
| 🟢 LOW | Add a 2-line professional summary | +2 pts |

**Estimated score after all fixes: ~XX%**

---
*ATS scores are estimates. Algorithms vary across Workday, Greenhouse, Taleo, and Lever.
Save your resume as .docx for best ATS compatibility.*
```

---

## Command Files (Issue #4)

### `commands/ats-check.md` — plugin (with frontmatter)

```markdown
---
description: Check how well a resume passes ATS automated filtering for a specific job. Accepts job number, URL, or pasted JD. Uses cached resume by default; override with --resume <path>.
allowed-tools: Read, Write, Glob, WebSearch
---

Run ATS compatibility check for: $ARGUMENTS

Use the `job-search:ats-analyzer` skill.

Parse arguments:
1. Extract --resume <path> if present (Full Mode); otherwise use cached profile (Limited Mode)
2. Classify remaining args: integer → job number, URL → fetch, else → raw JD text
3. If job number: look up in scored_jobs.json, search for JD via WebSearch; if not found, ask user to paste
4. If no args: ask user for job description

Get resume:
- --resume <path>: read that file directly
- Default: read .cache/active_persona.txt → .cache/<persona>/profile.json
- If no cache: ask user to run /input-resume first
```

### `.claude/commands/ats-check.md` — standalone (no frontmatter)

```markdown
Run ATS compatibility check for: $ARGUMENTS

Use the job-search:ats-analyzer skill.

Parse arguments:
1. Extract --resume <path> if present (Full Mode); otherwise use cached profile (Limited Mode)
2. Classify remaining args: integer → job number, URL → fetch, else → raw JD text
3. If job number: look up in scored_jobs.json, search for JD via WebSearch; if not found, ask user to paste
4. If no args: ask user for job description

Get resume:
- --resume <path>: read that file directly
- Default: read .cache/active_persona.txt → .cache/<persona>/profile.json
- If no cache: ask user to run /input-resume first
```

---

## Limitations (surface in output footer)

1. ATS algorithms vary — this is an estimate across common platform behaviors
2. Limited Mode cannot detect formatting issues (tables, columns, header placement)
3. File format (`.docx` vs `.pdf`) matters but cannot be verified from cached text — always advise `.docx`
4. Generic job board URLs (LinkedIn, Indeed) may not yield full JD text — user paste is the reliable fallback
