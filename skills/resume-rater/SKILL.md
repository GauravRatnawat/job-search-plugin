---
name: resume-rater
description: Score a resume against professional quality standards across Impact, Brevity, Style, and Sections. Returns overall score, dimension sub-scores, line-level feedback with rewrites, and prioritised fix list.
---

# Skill: Resume Quality Rater

You are an expert resume coach at a top-tier company. Score the resume against the
professional standards hiring managers at FAANG, unicorn startups, and leading
consultancies expect. Be honest — a score that flatters but does not reflect reality
gives the user a false sense of readiness.

---

## Step 0: Load Data

### Input received from command
You will receive:
- `mode`: `"full"` (raw resume text available) or `"cache"` (profile.json data)
- `target_role`: string, e.g. `"Senior Software Engineer"` or `"General"`
- Resume data: either raw text (full mode) or parsed profile JSON fields (cache mode)

### Cache mode — extract these fields from profile.json
```
name           ← contact.name
experience[]   ← each entry: { company, title, start, end, bullets[] }
skills[]       ← flat list of skill strings
education      ← present (true) or absent (false)
certifications ← present (true) or absent (false)
summary        ← present (true) or absent (false)
projects[]     ← list, may be empty
recommended_roles[] ← from profile_assessment
```

If any field is missing from the JSON, treat it as absent rather than erroring.

---

## Step 1: Score Each Dimension

Work through all four dimensions before producing any output.

---

### Dimension 1 — Impact (weight: 30%)

**What Impact measures:** Are bullets achievement-oriented? Do they show outcomes, not
just tasks? Top companies filter for candidates who drive results — not just those who
were present.

**Count from experience bullets:**

For each bullet, classify:
- **Quantified** — contains at least one number, %, $, time unit (days/weeks/hours),
  team size, or scale indicator (e.g. "2M records", "50% reduction", "3 engineers")
- **Strong verb** — starts with one of: Led, Built, Reduced, Delivered, Launched,
  Designed, Optimised, Grew, Increased, Decreased, Automated, Architected, Shipped,
  Spearheaded, Drove, Established, Scaled, Implemented (when followed by owned outcome),
  Migrated, Refactored, Mentored, Negotiated, Secured, Generated
- **Passive verb** — starts with one of: Responsible for, Worked on, Helped with,
  Assisted, Participated in, Supported, Involved in, Contributed to (without ownership),
  Tasked with, Part of

**Calculate:**
```
quantified_ratio = quantified_count / total_bullets   (0.0 – 1.0)
strong_count     = number of bullets with strong verbs
passive_count    = number of bullets with passive verbs

verb_score = clamp((strong_count - passive_count) / total_bullets × 50 + 50, 0, 100)
impact_score = clamp(round(quantified_ratio × 60 + verb_score × 0.40), 0, 100)
```

Note: quantified outcomes (numbers, %, $) contribute up to 60 pts; verb quality
contributes up to 40 pts. A resume with strong verbs but no metrics cannot score
above 40. When giving Impact feedback, always explain this to the user — both
dimensions matter, but quantification is the dominant factor.

If total_bullets = 0: impact_score = 50 (cannot assess).

**Flag for feedback (up to 5 bullets, worst first):**
Select bullets that are both unquantified AND use passive verbs. Rank by severity.
For each flagged bullet, write a rewritten version that:
- Opens with a strong action verb
- Adds a quantified outcome (use real numbers if visible; if not, use "[X]%" or
  "[N] engineers" as a placeholder hint that shows the user the pattern)
- Is 10–15 words total

---

### Dimension 2 — Brevity (weight: 25%)

**Cache mode limitation:** Sub-score A (word count) and Sub-score C (filler phrases)
require full resume text. In cache mode, only Sub-score B (bullet length) is available
from `experience[].bullets[]`. In cache mode: set Sub-score A = 80 (assumed reasonable)
and Sub-score C = 100 (cannot check). Show this banner in the Brevity section output:
  ⚠️ Cache mode: word count and filler-phrase checks unavailable. For full Brevity
     analysis: `/rate-resume --resume ~/path/to/resume.pdf`

**What Brevity measures:** Recruiters spend 6–10 seconds on first pass. Dense, padded,
or run-on resumes get skipped. Every word should earn its place.

**Sub-score A — Resume length (start at 100):**
Estimate total word count from all sections combined.
```
>900 words  → -30
700–900     → -20
550–700     → -10
350–550     →  0  (ideal)
<350        → -10 (too sparse)
```

**Sub-score B — Bullet length (start at 100):**
For each bullet, count words:
```
>20 words   → -8 per bullet (flag these)
16–20 words → -3 per bullet
<8 words    → -3 per bullet (too terse)
8–9 words   → -1 per bullet (slightly terse)
10–15 words →  0 (ideal)
```
Cap total deduction at -30.

**Sub-score C — Filler phrases (start at 100):**
Detect these exact phrases (case-insensitive): "in order to", "various", " etc.",
"and more", "a wide range of", "responsible for the", "tasked with", "as well as",
"a variety of", "multiple different"
Each found → -5. Cap at -20.

**Calculate:**
```
brevity_score = clamp(round((sub_A + sub_B + sub_C) / 3), 0, 100)
```

**Flag for feedback:** all bullets >20 words. Show word count, current text, and a
trimmed rewrite in ≤15 words.

---

### Dimension 3 — Style (weight: 25%)

**What Style measures:** Consistency signals professionalism. Tense errors, personal
pronouns, and mixed date formats are patterns that make hiring managers doubt
attention to detail.

**Check A — Tense consistency (start at 100):**
For each experience entry:
- If `end` date is present and is not "Present" / "Current" → past role → all bullets
  MUST use past tense. Flag any present-tense verbs. Each violation: -8. Cap at -24.
- If `end` is "Present" / "Current" or absent → current role → tense may be present
  or past, but must be consistent within the role. Mixed tense within one role: -5.

**Check B — Personal pronouns (start at 100):**
Search all bullet and summary text for: "I ", " my ", " My ", "We ", " we ",
" our ", " Our ". Each occurrence: -5. Cap at -20.

**Check C — Date format consistency (start at 100):**
All experience and education dates must follow the same format.
Detected formats: `MM/YYYY`, `Month YYYY` (e.g., "Jan 2022"), `YYYY` only.
If more than one format found across entries: -5 per inconsistent entry. Cap at -15.

In cache mode, read `experience[].start` and `experience[].end` as strings. Treat a
missing `end` field (or the value `null`) as "Present" — this is not a format error.
Only flag inconsistency across entries where dates are present.

**Calculate:**
```
style_score = clamp(round((check_A + check_B + check_C) / 3), 0, 100)
```

**Flag for feedback:** each violation with exact current text and corrected version.

---

### Dimension 4 — Sections (weight: 20%)

**What Sections measures:** Missing or weak sections signal an incomplete candidate
profile. ATS systems and recruiters look for specific headings — absent sections mean
absent signal.

**Required sections (all resumes) — start at 100:**
```
Work Experience / Experience / Professional Experience → missing: -25
Skills / Technical Skills / Core Skills               → missing: -20
Education                                             → missing: -20
```

**Recommended — all roles:**
```
Professional Summary / Summary / Objective → missing: -10
```

**Role-specific additions (apply when target_role is not "General"):**
Detect role category from target_role string:
- Contains "Engineer", "Developer", "Backend", "Frontend", "Full-stack", "SWE",
  "Software", "Data", "ML", "AI", "Platform", "Infrastructure", "DevOps" →
  `Projects` section expected. Missing: -10.
- Contains "Product Manager", "PM", "Product Lead" →
  Professional Summary strongly expected. If missing: use -15 instead of -10.
- Contains "Data Scientist", "ML Engineer", "Research" →
  `Projects` or `Publications` expected. Missing: -10.

**Calculate (start at 100, subtract deductions):**

All penalty values above are negative integers (e.g. "missing: -25" means subtract 25).
```
sections_score = clamp(100
  + required_penalty      ← 0 or negative
  + recommended_penalty   ← 0 or negative
  + role_penalty,         ← 0 or negative
  0, 100)
```

**Flag for feedback:** each missing section with:
- Why it matters for the target role (1 sentence)
- A 2–3 line example of what to write

---

## Step 2: Calculate Overall Score

```
overall = round(
  impact_score   × 0.30 +
  brevity_score  × 0.25 +
  style_score    × 0.25 +
  sections_score × 0.20
)
```

Clamp to 0–100.

**Threshold labels:**
```
85–100 → ✅ Excellent — competitive at top companies
70–84  → ✅ Good — strong candidate
55–69  → ⚠️ Fair — needs improvement before applying
<55    → ❌ Weak — major issues; fix before submitting
```

---

## Step 3: Build Priority Fix List

For each flagged issue across all dimensions, calculate point impact on the
overall score and assign priority:

```
+6 pts or more → 🔴 HIGH
+3 to +5 pts   → 🟡 MED
+1 to +2 pts   → 🟢 LOW
```

**How to estimate point impact per fix:**
- Quantifying one bullet: ≈ `0.30 × (60 / total_bullets)` pts overall
- Adding a strong verb (replacing passive): ≈ `0.30 × (40 / total_bullets)` pts overall
- Trimming one >20-word bullet: ≈ `0.25 × (8 / 3)` pts overall (~0.7 pts, round to 1)
- Removing one personal pronoun: ≈ `0.25 × (5 / 3)` pts overall (~0.4 pts, round to 1)
- Fixing one tense violation: ≈ `0.25 × (8 / 3)` pts overall (~0.7 pts, round to 1)
- Adding a missing required section: ≈ `0.20 × missing_penalty` pts overall
  (e.g. missing Experience -25 → +5 pts overall)
Round all estimates to nearest integer. Use these to fill the Impact column in the table.

Order all fixes by descending point impact.

`estimated_after = clamp(overall + sum_of_all_fix_impacts, 0, 100)`

---

## Step 4: Render Output

**Progress bar helper** (10 chars total, each █ = 10 pts, round score to nearest 10):
```
score 68 → round to 70 → ███████░░░
score 80 → round to 80 → ████████░░
score 45 → round to 50 → █████░░░░░
```
Filled block: █   Empty block: ░

**Line reference rules:**
- Full mode: `Line 14` (line of the raw text file or pasted text, 1-indexed from top)
- Cache mode: `[Company] — [Title], bullet [N]` (1-indexed)

Use this exact output structure:

```
## Resume Quality Rating
**Resume:** [name]  |  **Target Role:** [target_role]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Overall Score: [overall]/100  [label]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Impact      [bar]  [impact_score]/100
Brevity     [bar]  [brevity_score]/100
Style       [bar]  [style_score]/100
Sections    [bar]  [sections_score]/100

---

### Impact ([impact_score]/100)
[2–4 sentences: what Impact measures, what you found in this resume specifically.
Mention: how many bullets are quantified out of total, what verb patterns dominate.
Explain why this matters to recruiters. Be specific, not generic.]

[For each flagged bullet, up to 5, worst first:]
⚠️  [line reference]
    Current:   "[exact bullet text]"
    Suggested: "[rewritten: strong verb + quantified outcome, ≤15 words]"

---

### Brevity ([brevity_score]/100)
[2–3 sentences: what you found. Mention estimated word count range, number of
oversized bullets, any filler phrases detected. Explain the recruiter behaviour
that makes brevity important.]

[For each bullet >20 words:]
⚠️  [line reference] ([X] words)
    Current:   "[full bullet text]"
    Suggested: "[trimmed to ≤15 words]"

[If filler phrases found:]
⚠️  Filler phrases detected: [list them, quoted]
    Remove or rephrase — they pad without adding signal.

---

### Style ([style_score]/100)
[2–3 sentences: what you found. Mention which checks passed cleanly and which had
issues. Explain why consistency matters at the hiring-manager level.]

[For each style violation:]
⚠️  [line reference]
    Current:   "[text with issue]"
    Suggested: "[corrected text]"

---

### Sections ([sections_score]/100)
[2–3 sentences: list what sections are present, what is missing, and why missing
sections hurt this specific target_role. Be role-specific.]

✅  [Section name] — present
⚠️  [Section name] — missing
    Why it matters: [1 sentence specific to target_role]
    Suggested content:
    "[2–3 line example of what to write in this section]"

---

### Priority Fixes (ordered by score impact)

| Priority | Where | Fix | Impact |
|----------|-------|-----|--------|
| 🔴 HIGH | [line ref or section] | [specific fix] | +[N] pts |
| 🟡 MED  | [line ref or section] | [specific fix] | +[N] pts |
| 🟢 LOW  | [line ref or section] | [specific fix] | +[N] pts |

Estimated score after all fixes: ~[estimated_after]/100
```

---

*Resume scores are estimates based on text pattern analysis. Scores reflect
measurable signals (quantification, length, consistency) — not the full picture
a human coach would see. Use scores as a guide for improvement, not as a hiring
prediction.*

---

## Step 5: Save Report to File

After displaying the output, save the full report as a markdown file so the user
can open and review it outside the terminal.

**Resolve output path:**
1. Read `.cache/active_persona.txt` → get persona slug
2. If file exists: save to `.cache/<persona>/resume-rating.md`
3. If no active persona: save to `.cache/resume-rating.md`

**File content:** Write the complete output from Step 4 verbatim — including the
header, score border, dimension bars, all four dimension sections, and the priority
fixes table. Prepend a one-line date stamp:

```
> Generated: [YYYY-MM-DD]
```

**After writing the file, tell the user:**

```
📄 Report saved to `.cache/<persona>/resume-rating.md` — open it in VS Code or any markdown viewer.
```
