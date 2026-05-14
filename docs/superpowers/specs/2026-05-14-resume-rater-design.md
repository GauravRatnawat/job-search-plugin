# Resume Quality Rater — Design Spec

**Date:** 2026-05-14
**Status:** Approved
**Command:** `/rate-resume`

---

## Overview

A standalone command that scores a resume against professional quality standards,
mirroring the UX of resumeworded.com. Outputs an overall score, four dimension
sub-scores, line-level feedback with before/after rewrites, and a prioritised fix
list with estimated score impact.

Designed as standalone first; pipeline integration with `/input-resume` is a
planned future step.

---

## Architecture

Two new files:

| File | Purpose |
|------|---------|
| `skills/resume-rater/SKILL.md` | Scoring rubric, dimension weights, output format instructions |
| `.claude/commands/rate-resume.md` | Slash command that invokes the skill |

No external dependencies. Follows existing project patterns (pure skill + command,
cache read via file, Claude native write).

---

## Input Resolution

Resolved in this order:

1. `.cache/<persona>/profile.json` — auto-read if fresh (zero friction for returning users)
2. `--role "Senior SWE"` flag — overrides cached target role for scoring adjustments
3. `--resume ~/path/to/cv.pdf` — forces raw resume re-parse, bypasses cache
4. No cache, no flag — prompt user to paste resume text

**Command syntax:**
```
/rate-resume                              # cache + cached target role
/rate-resume --role "Senior SWE"          # override role
/rate-resume --resume ~/path/to/cv.pdf    # force raw resume
```

---

## Scoring Dimensions

Overall score = weighted sum of four dimensions, clamped to 0–100.

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| Impact | 30% | Quantified bullets, strong action verbs, achievement orientation |
| Brevity | 25% | Resume length, bullet conciseness (<15 words ideal), no filler phrases |
| Style | 25% | Tense consistency, no personal pronouns ("I"/"my"), date format consistency |
| Sections | 20% | Required sections present and logically ordered |

**Overall = Impact×0.30 + Brevity×0.25 + Style×0.25 + Sections×0.20**

### Impact scoring detail
- Count bullets with at least one measurable outcome (number, %, $, time)
- Score = (quantified_bullets / total_bullets) × 100, adjusted for verb quality
- Strong verbs (Led, Built, Reduced, Delivered) add points; passive verbs (Responsible for,
  Worked on, Helped with) deduct points

### Brevity scoring detail
- Ideal resume: 1 page for <8 years experience, 2 pages for 8+ years
- Bullet ideal length: <15 words. Deduct for bullets >20 words
- Filler phrases ("in order to", "various", "etc.") each deduct points

### Style scoring detail
- Past roles must use past tense; current role may use present or past (consistent)
- Personal pronouns ("I", "my", "we") each deduct points
- Date format must be consistent across all entries (MM/YYYY or Month YYYY)

### Sections scoring detail (role-aware)
Required sections for all roles: Experience, Skills, Education
Role-specific requirements:
- **SWE / Engineering roles:** Projects section expected; missing = penalty
- **PM / Product roles:** Professional Summary strongly expected; missing = penalty
- **All roles:** Professional Summary recommended; missing = minor penalty

---

## Score Thresholds

| Score | Label | Meaning |
|-------|-------|---------|
| 85–100 | Excellent | Competitive at top companies |
| 70–84 | Good | Strong candidate |
| 55–69 | Fair | Needs improvement before applying |
| <55 | Weak | Major issues — fix before submitting anywhere |

---

## Line Reference Behaviour

Feedback must cite where each issue appears. Two modes:

- **Full resume mode** (`--resume` flag provided): cite exact line number — `Line 14`
- **Cache mode** (reading from `profile.json`): cite by position — `[Company] — [Role], bullet 2`

The skill must detect which mode is active and use the appropriate locator. Never
show `Line N` when only the cache is available.

---

## Output Format

```
## Resume Quality Rating
**Resume:** [Name]  |  **Target Role:** [role or "General"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Overall Score: 74/100  ⚠️ Fair
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Impact      ████████░░  68/100
Brevity     ████████░░  80/100
Style       ███████░░░  75/100
Sections    ████████░░  72/100

---

### Impact (68/100)
[2–4 sentence explanation of what this dimension measures and what was found.
Explain WHY it matters to recruiters/hiring managers.]

⚠️  Line [N] — [Company, Role]
    Current:   "[exact bullet text]"
    Suggested: "[rewritten bullet with metric + strong verb]"

[repeat for each flagged bullet, up to 5 most impactful]

---

### Brevity (80/100)
[explanation]

⚠️  Line [N] — [Company, Role] ([X] words)
    Current:   "[long bullet]"
    Suggested: "[concise version]"

---

### Style (75/100)
[explanation]

⚠️  Line [N] — [Company, Role]
    Current:   "[issue text]"
    Suggested: "[corrected text]"

---

### Sections (72/100)
[explanation of what sections are present, what is missing, why each missing
section matters for the target role]

✅  [Section] — present
⚠️  [Section] — missing or weak
    Suggested: [example content or structure]

---

### Priority Fixes (ordered by score impact)

| Priority | Where | Fix | Impact |
|----------|-------|-----|--------|
| 🔴 HIGH | Lines X, Y, Z | [fix description] | +N pts |
| 🟡 MED  | Line X | [fix description] | +N pts |
| 🟢 LOW  | [section] | [fix description] | +N pts |

Estimated score after all fixes: ~XX/100
```

---

## Future: Pipeline Integration

When integrating into `/input-resume`:
- Run rating automatically after profile parse
- Show a compact summary (overall score + top 3 fixes only)
- Full report still available on demand via `/rate-resume`
- Cache the rating result alongside `profile.json`

---

## Files to Create

| File | Action |
|------|--------|
| `skills/resume-rater/SKILL.md` | Create new |
| `.claude/commands/rate-resume.md` | Create new |
