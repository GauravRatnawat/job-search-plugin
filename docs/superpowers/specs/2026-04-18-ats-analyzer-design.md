# ATS Compatibility Analyzer — Design Spec

**Date:** 2026-04-18
**Status:** Approved

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

Standalone skill + command. No changes to existing skills or commands. The ATS check is an on-demand diagnostic for a specific job the user is serious about.

**Intended workflow:**
```
/input-resume          → find & score 20+ jobs
/ats-check <job>       → diagnose ATS compatibility for a target role
/tailor-resume <job>   → fix the resume
/ats-check <job>       → re-run to confirm improvement
```

### New Files

| File | Purpose |
|------|---------|
| `skills/ats-analyzer/SKILL.md` | Core ATS analysis logic |
| `commands/ats-check.md` | Plugin slash command |
| `.claude/commands/ats-check.md` | Standalone slash command |

No modifications to existing files.

---

## Skill: `skills/ats-analyzer/SKILL.md`

### Inputs

The skill receives:
1. **Job description** — raw text extracted from a URL, pasted by the user, or looked up from the scored jobs cache by job number
2. **Resume** — the cached parsed profile (`profile.json`) by default, or a fresh resume file if `--resume <path>` is passed

### ATS Scoring Model

Five factors, weighted:

| Factor | Weight | What to check |
|--------|--------|---------------|
| Keyword Match | 40% | Required/preferred keywords from JD found verbatim (or near-verbatim) in resume |
| Section Recognition | 20% | Standard ATS-readable section headers present |
| Formatting Compliance | 20% | No ATS-hostile formatting patterns detected |
| Structural Completeness | 10% | Contact info, consistent date formats, bullets not paragraphs |
| Title/Role Alignment | 10% | Candidate's past titles match what the JD searches for |

**ATS Pass Thresholds:**
- **75%+** → ✅ LIKELY PASS
- **55–74%** → ⚠️ AT RISK
- **<55%** → ❌ LIKELY FILTERED

#### 1. Keyword Match (40%)

Extract from JD:
- **Required keywords:** skills, tools, technologies marked as "required", "must have", or listed in the core responsibilities
- **Preferred keywords:** "nice to have", "preferred", "bonus"

Match against resume text using:
- Exact match: "Kubernetes" found in resume
- Near-exact: abbreviations both ways ("CI/CD" ↔ "continuous integration"), plural forms
- Do NOT use synonym matching (that's the job scorer's job — ATS is literal)

Score: `(required_found / required_total) × 100`
Bonus: each preferred keyword found adds 2 points (capped at 10 bonus points)

#### 2. Section Recognition (20%)

ATS parsers look for these exact or near-exact section headers:

| Standard (recognized) | Non-standard (may fail) |
|----------------------|------------------------|
| Work Experience / Experience | My Journey, Career History, What I've Done |
| Education | Academic Background |
| Skills / Technical Skills | Technical Expertise, My Toolkit, Core Competencies |
| Summary / Professional Summary / Objective | About Me, Who I Am |
| Certifications | Credentials, Achievements |

Flag any non-standard header names detected in the resume.
Missing standard sections (especially Skills, Experience, Education) count as deductions.

#### 3. Formatting Compliance (20%)

Flag these ATS-hostile patterns detected from resume text:

| Pattern | Severity | Why it matters |
|---------|----------|---------------|
| Skills in table/grid format | HIGH | ATS parsers often skip table content entirely |
| Contact info in document header | MEDIUM | Some ATS ignore header/footer content |
| Multiple columns | HIGH | Parsed left-to-right, mixing unrelated content |
| Graphics, icons, logos | MEDIUM | Invisible to text parsers |
| Excessive symbols (★, →, ✓ as bullets) | LOW | May cause encoding issues |
| No bullet points — paragraph-style experience | LOW | Harder for ATS to parse individual achievements |

#### 4. Structural Completeness (10%)

Check for:
- Contact info present (name, email, phone)
- Dates formatted consistently (prefer MM/YYYY)
- Each experience entry has company + title + dates
- Resume has at least a Skills section and Experience section

#### 5. Title/Role Alignment (10%)

Compare the candidate's most recent job titles and target role against the JD's stated job title:
- Exact or near-exact match → 100
- Related title → 70
- Adjacent/different function → 40
- Unrelated → 10

---

## Output Format

```
## ATS Compatibility Report
**Job:** [Company] — [Job Title]
**Resume:** [candidate name] ([cached/provided])

---

**Estimated ATS Pass Rate: XX%**  [✅ LIKELY PASS / ⚠️ AT RISK / ❌ LIKELY FILTERED]

### Keyword Match  (X/Y required keywords — Z%)
✅ Found:    [keyword1], [keyword2], [keyword3], ...
❌ Missing:  [keyword1], [keyword2], ...
⭐ Preferred found:  [keyword1], ...
⭐ Preferred missing: [keyword1], ...

### Section Check
✅ Work Experience — recognized
✅ Education — recognized
✅ Skills — recognized
⚠️  "[Non-standard header]" → rename to "[Standard header]"
❌ No Summary/Objective section detected

### Formatting
✅ No table formatting detected
⚠️  Skills section uses table layout — many ATS skip table content
⚠️  Contact details appear to be in document header

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
| 🟡 MEDIUM | Move skills from table to plain comma-separated list | +4 pts |
| 🟢 LOW | Add 2-line professional summary | +2 pts |

**Estimated score after all fixes: ~XX%**

---

*Note: ATS scores are estimates. Different ATS platforms (Workday, Greenhouse, Taleo) use different algorithms. This analysis targets common parsing behaviors across major platforms.*
```

---

## Commands

### `commands/ats-check.md` (plugin)

```markdown
---
description: Check how well a resume will pass ATS (automated) filtering for a specific job. Input: job description + resume (cached or provided).
allowed-tools: Read, Write, Glob, WebFetch
---

Run an ATS compatibility check for: $ARGUMENTS

Use the `job-search:ats-analyzer` skill.

Get the resume:
- If `--resume <path>` is in $ARGUMENTS, read that file
- Otherwise, read `.cache/active_persona.txt` → `.cache/<persona>/profile.json`
- If no cache exists, ask the user to run /input-resume first

Get the job description:
- If $ARGUMENTS contains a job number, look it up in `.cache/<persona>/scored_jobs.json`
- If $ARGUMENTS is a URL, fetch the page content
- Otherwise treat the argument as raw job description text
```

### `.claude/commands/ats-check.md` (standalone)

Same content — identical behavior for standalone Claude Code users.

---

## Integration Points

- **No changes** to existing skills or commands
- **Natural follow-up** to `/tailor-resume`: run ATS check before and after to measure improvement
- **Cache-aware**: reuses parsed profile from `/input-resume` pipeline

---

## Limitations (to surface in output)

1. ATS algorithms vary — this is an estimate, not a guarantee
2. Formatting detection from text is imperfect (can't see actual document layout)
3. File format (`.docx` vs `.pdf`) matters but can't be checked from cached text
4. Always advise: save as `.docx` when submitting to ATS-heavy companies
