---
name: market-analyzer
description: Market compatibility analyzer. Evaluates a resume against a target role in a specific regional market (Berlin, Germany, DACH, Europe, Remote-EU). Checks language fit, CV format conventions, visa/work authorization, local certifications, stack preferences, salary benchmarks, cultural framing, and recommended job boards. Produces a 0-100 market-fit score with a priority fix list. Use when the user wants to assess resume readiness for a specific regional market.
---

# Skill: Market Compatibility Analyzer

You are assessing how well a candidate's resume is positioned for a **specific job role in a specific regional market**. This is NOT a job-fit score (that is the Job Scorer skill) and NOT an ATS mechanical check (that is the ATS Analyzer skill). This is **market readiness**: regional language norms, CV format conventions, visa pathways, local certifications, stack expectations, salary alignment, and cultural framing.

---

## Mode Detection

**Full Mode** — raw resume file was provided via `--resume <path>`:
- All 8 dimensions available: language quality assessable from writing, CV format detectable, photo/DOB presence visible

**Limited Mode** — only `profile.json` cache is available:
- CV Format dimension: partial only (cannot detect photo, DOB, actual header names, layout)
- Language quality: cannot assess from structured data alone — flag as low confidence
- **Display this banner at the top of output:**
  ```
  ⚠️  LIMITED MODE — using cached profile only
     CV format and language quality checks unavailable.
     For full analysis: /market-check "<role>" --market <market> --resume ~/path/to/resume.pdf
  ```

Profile fields available in Limited Mode:
- `contact` — name, location (infer nationality/region signals)
- `skills` — flat list (stack matching)
- `experience[]` — titles, companies, dates, bullets
- `education` — degree, institution, location (language + local qualification signals)
- `certifications` — list (local cert matching)
- `profile_assessment` — target roles, level, industry fit

---

## Step 1: Resolve Market

Map the user-provided market input to a canonical market using this alias table:

| Input | Resolves to | Notes |
|-------|-------------|-------|
| `berlin` | **Berlin** | English-friendly tech hub; startup-heavy |
| `germany`, `de`, `ger`, `munich`, `hamburg`, `frankfurt`, `cologne` | **Germany** | Mixed English/German; enterprise-heavy outside Berlin |
| `dach`, `dach-region` | **DACH** | Germany + Austria + Switzerland combined norms |
| `austria`, `at`, `vienna`, `graz` | **Austria** | German-dominant; formal |
| `switzerland`, `ch`, `zurich`, `bern`, `geneva` | **Switzerland** | Highest pay; strict work permits; multilingual |
| `europe`, `eu`, `pan-eu`, `pan-europe` | **Europe** | Generic EU norms; English assumed |
| `remote-eu`, `remote-europe`, `eu-remote` | **Remote EU** | EU-only remote; tax/contract complexity |
| `netherlands`, `nl`, `amsterdam`, `rotterdam` | **Netherlands** | English-friendly; 30% ruling available |
| `france`, `fr`, `paris` | **France** | French preferred; formal |
| `spain`, `es`, `madrid`, `barcelona` | **Spain** | Spanish preferred outside tech hubs |
| `portugal`, `pt`, `lisbon` | **Portugal** | English OK in tech; NHR tax regime |

If input does not match any alias: respond with "Market not recognised. Supported markets: berlin, germany, dach, austria, switzerland, europe, remote-eu, netherlands, france, spain, portugal. Re-run with a supported market."

---

## Step 2: Score the Resume (8 Dimensions)

### Weight Table

| Dimension | Full Mode | Limited Mode |
|-----------|----------:|-------------:|
| Language Fit | 20% | 25% |
| Visa & Work Authorization | 20% | 25% |
| CV Format | 15% | 5% |
| Local Certifications | 10% | 10% |
| Stack & Tech Preferences | 10% | 10% |
| Salary Benchmark Alignment | 10% | 10% |
| Cultural Framing | 10% | 10% |
| Job Board Coverage | 5% | 5% |

In Limited Mode, CV Format drops from 15% to 5% (only partial checks possible). Redistribute 10%: +5% to Language Fit, +5% to Visa & Work Authorization.

---

### Dimension 1: Language Fit

Use this market × role-type matrix to determine language requirement:

| Market | IC/Engineer role | Management/Senior | Customer-facing |
|--------|-----------------|-------------------|-----------------|
| Berlin | English usually sufficient | B2 German often preferred | B2–C1 German |
| Germany (non-Berlin) | B2 German expected | C1 German expected | C1 German required |
| DACH | B2 German expected | C1 German expected | C1 German required |
| Austria | C1 German expected | C1 German required | C1 German required |
| Switzerland | B2 German/French/Italian by region | C1 expected | C1 required |
| Europe / Remote-EU | English sufficient | English sufficient | Varies by country |
| Netherlands | English fine; Dutch a plus | Dutch preferred | Dutch often required |
| France | B2 French expected | C1 French required | C1 French required |
| Portugal | English OK in tech | Portuguese preferred | Portuguese required |

**Assess resume language signals:**
- Explicit language listings (e.g., "German: B2", "Deutsch: Fließend") → use stated level
- Education location (e.g., degree from German university → infer at least B2 German)
- Prior work experience in region → infer functional language ability
- Resume written in target language → positive signal
- No language signals + non-EU name/education → flag gap

**Score:**
- Required language clearly present at required level → 100
- Required language present but below required level → 60
- No language signal, English role in English-friendly market → 80
- No language signal, German/French required role → 30
- Resume explicitly lists wrong level → 40

In Limited Mode: if no language data in profile.json, mark "low confidence" and score at 50% with a recommendation to add language certifications.

---

### Dimension 2: Visa & Work Authorization

Assess from location, nationality signals, and education:

| Signal | Score |
|--------|-------|
| EU/EEA/Swiss citizenship (inferred or stated) | 100 |
| UK citizen + role in EU (post-Brexit) | 70 (Blue Card eligible if salary threshold met) |
| Non-EU but Blue Card eligible salary signal | 65–75 |
| Non-EU, unclear salary, STEM background | 50 |
| Non-EU, no STEM flag, likely below Blue Card threshold | 25 |
| Remote-EU role, non-EU candidate | 20 (complex tax/entity issues) |

**Blue Card salary thresholds (2025):**
- Germany general: €45,300/yr gross
- Germany STEM/IT shortage: €40,770/yr gross
- Austria: €40,000/yr gross
- Netherlands (Highly Skilled Migrant): €5,688/mo (age 30+) or €4,171/mo (under 30)

If visa pathway is ambiguous, say so explicitly and recommend the candidate verify with BAMF (DE), IND (NL), or national immigration authority.

---

### Dimension 3: CV Format *(Full Mode only for most checks)*

**Regional CV format expectations:**

| Market | Photo | DOB/Marital | Length | Format style |
|--------|-------|-------------|--------|--------------|
| Germany/Austria | Expected (traditional); optional (modern tech) | Optional but common | 2 pages + Anlagen OK | Tabular Lebenslauf or European chronological |
| Switzerland | Common | Common | 2 pages | Formal, structured |
| Berlin tech startups | Not expected | Not expected | 1–2 pages | Anglo-style bullet resume OK |
| Netherlands | Not expected | Not expected | 1–2 pages | Anglo or European, concise |
| France | Expected | Common | 1–2 pages | Curriculum Vitae format |
| Europe (generic) | Europass accepted | Optional | 2 pages | Europass or structured |
| Remote-EU | Not expected | Not expected | 1–2 pages | Anglo-style fine |

**Full Mode checks:**
- Photo present? Compare to market expectation → flag gap
- DOB/marital status present? Compare to market norm → flag if missing where expected or present where inadvisable
- Resume length appropriate?
- Tabular vs bullet style matches market norm?
- Written in appropriate language (or offers translated version)?

**Limited Mode:** Only check length and language from profile data. Score at 60 base with note that format cannot be fully assessed.

---

### Dimension 4: Local Certifications & Qualifications

Check for market-valued certifications missing from the resume:

**Germany / DACH:**
- Degree recognition: non-EU degree holders may need Anerkennung (anabin database)
- German language: Goethe-Zertifikat, TestDaF, Deutsche Sprachprüfung
- Tech certifications locally valued: AWS (Germany-specific demand), ISTQB, SAFe/Scrum (enterprise), ITIL v4
- Finance/insurance: IDD, MaRisk awareness, BaFin-related compliance certs

**Switzerland:**
- Swiss Federal Diploma (Eidgenössisches Fachausweis) respected
- FINMA-regulated roles: Series-equivalent Swiss qualifications
- SVEB for training roles

**Netherlands:**
- BIG register for healthcare
- Financial roles: AFM/DNB awareness
- Generally international certs accepted

**Europe broadly:**
- GDPR/DPO cert valued across all markets for data roles
- ISO 27001 LI/LA for security roles
- PRINCE2 / PMP for PM roles

**Score:**
- All commonly required local certs present → 100
- 1 key cert missing → 75
- 2+ key certs missing → 50
- Several missing, degree recognition unclear → 25

---

### Dimension 5: Stack & Tech Preferences

Market × domain stack norms (use as defaults; WebSearch for niche/current data):

**Germany / DACH:**
- Enterprise backend: Java/Spring Boot, Kotlin rising, .NET in finance/insurance
- Startups (Berlin especially): Go, TypeScript/React, Python, Rust emerging
- Data: dbt + Snowflake/BigQuery, Apache Airflow, Spark for large-scale
- DevOps: Kubernetes/Helm, Terraform, GitLab CI (common in German enterprise)
- SAP: extremely common in German corporate; worth flagging if absent for enterprise roles

**Netherlands:**
- Fintech/banking: Python, Kafka, Spark
- Scale-ups: Node.js, React, AWS-native
- Data: Databricks common

**Switzerland:**
- Banking/finance: Java, .NET, COBOL still present in legacy
- Medtech/pharma: Python, R, SAS

**Berlin startups specifically:**
- TypeScript/Node + React full-stack dominant
- Go for infra/backend services
- Python for ML/data teams

**Score:**
- 80%+ of role-relevant stack present → 100
- 60–79% match → 75
- 40–59% match → 50
- <40% match → 25
- Strong mismatch (e.g., no Java for German enterprise Java role) → 10

---

### Dimension 6: Salary Benchmark Alignment

Built-in bands by market × seniority (2025 benchmarks, gross annual):

| Market | Junior | Mid | Senior | Lead/Principal |
|--------|--------|-----|--------|----------------|
| Berlin | €40–55k | €55–75k | €75–95k | €95–130k |
| Germany (non-Berlin) | €45–60k | €60–80k | €80–110k | €110–145k |
| Munich | €50–65k | €65–85k | €85–115k | €115–155k |
| Switzerland (Zurich) | CHF 90–110k | CHF 110–140k | CHF 130–165k | CHF 155–200k |
| Netherlands | €40–55k | €55–75k | €70–95k | €90–125k |
| Austria (Vienna) | €38–52k | €50–68k | €65–88k | €85–115k |
| Remote-EU | €45–60k | €60–80k | €75–100k | €95–135k |

**Score:**
- Profile's implied salary expectation aligns with market band for their level → 100
- Slightly above market (10–20% over) → 70
- Significantly above market (20%+ over) or below Blue Card threshold when visa needed → 40
- No salary signal in resume (most common) → 80 (neutral — flag bands as informational)

In Limited Mode: use `profile_assessment.level` to pick the band. If level absent, score 75 and note bands.

---

### Dimension 7: Cultural Framing

Assess tone and self-presentation style against market norms:

**Germany / Austria / Switzerland:**
- Preferred: factual, credential-led, chronological, understated
- Avoid: US-style superlatives ("passionate", "rockstar", "ninja"), excessive self-promotion
- Titles and degrees matter — list them fully (Dr., Dipl.-Ing., M.Sc.)
- Gaps in employment: German market expects Lücken to be addressed
- Anschreiben (cover letter) still expected in many traditional companies

**Netherlands:**
- Direct, concise, no filler
- Results with numbers valued
- Personality comes through more than in DE

**France:**
- Formal structure; career narrative matters
- Grandes Écoles carry significant weight
- Photo and civil status traditionally included

**Berlin tech startups:**
- Anglo-style achievement-led bullets with metrics fine
- Informal tone acceptable
- Side projects, open-source, GitHub valued highly

**Remote-EU:**
- Anglo-style standard
- Async communication signals valued
- Timezone overlap for EU hours important to state

**Score:**
- Resume tone matches market norms well → 100
- Minor tone mismatches (slight over-promotion in DE) → 75
- Notable mismatch (heavy US startup superlatives for German enterprise) → 45
- Significant mismatch (Lebenslauf for US-style Berlin startup or vice versa) → 25

In Limited Mode: assess from experience bullet phrasing and job titles in profile.json.

---

### Dimension 8: Job Board Coverage

Informational dimension — checks whether the candidate is aware of / positioned for the right boards.

| Market | Primary boards | Secondary / niche |
|--------|---------------|------------------|
| Berlin | LinkedIn, Berlinstartupjobs.com, Honeypot/Hired | Arbeitnow.com, Startup Jobs DE, angel.co |
| Germany | StepStone.de, Xing, LinkedIn | Monster DE, Kimeta, Indeed DE |
| DACH | StepStone, Xing, LinkedIn | karriere.at (AT), jobs.ch (CH) |
| Austria | karriere.at, willhaben Jobs, LinkedIn | Xing, StepStone AT |
| Switzerland | jobs.ch, jobup.ch, LinkedIn | Xing, Michael Page, Hays |
| Netherlands | LinkedIn, Magnet.me, Indeed NL | Honeypot, Glassdoor NL |
| Remote-EU | Arbeitnow.com, EU Remote Jobs, WeWorkRemotely | RemoteOK (filtered), Himalayas |

**Score:** This dimension is always informational — scored 50 by default (boards are recommendation only, not a resume gap). Include board list in output regardless of score.

---

## Step 3: Calculate Final Score

```
final_score = sum(dimension_score × weight) for each active dimension
```

Clamp to 0–100. Round to nearest integer.

**Verdict bands:**
- 75+ → ✅ LIKELY HIRED (strong market fit — apply with light polish)
- 55–74 → ⚠️ WORTH POLISHING (addressable gaps — fix top issues before applying)
- <55 → ❌ NEEDS MAJOR REWORK (significant market readiness gaps)

---

## Step 4: Build Priority Fix List

For each gap, estimate point impact and assign priority:

| Impact | Priority |
|--------|----------|
| +8 pts or more | 🔴 HIGH |
| +4 to +7 pts | 🟡 MEDIUM |
| +1 to +3 pts | 🟢 LOW |

Order by descending point impact. Calculate estimated score after all fixes applied.

Fix examples:
- No German language signal for Germany non-Berlin role: add Goethe cert or note "German: B2 (in progress)" → estimate +12 pts
- US-style superlatives for German enterprise role: reframe as factual credential statements → estimate +8 pts
- Missing SAP exposure for German enterprise backend role: add any SAP integration work or note familiarity → estimate +6 pts
- Photo absent for traditional German application: add professional photo to Lebenslauf → estimate +5 pts
- Not listed on Xing: create profile and add to resume → estimate +2 pts

---

## Step 5: Output

Use this exact format:

```
## Market Compatibility Report
**Role:** [Job Title]
**Market:** [Resolved Market — e.g., "Berlin (Germany)"]
**Resume:** [candidate name or "Unknown"] ([Full Mode / Limited Mode])

⚠️  LIMITED MODE — using cached profile only            ← show only in Limited Mode
   CV format and language quality checks unavailable.
   For full analysis: /market-check "<role>" --market <market> --resume ~/path/to/resume.pdf

---

**Market Fit Score: XX%**  [✅ LIKELY HIRED / ⚠️ WORTH POLISHING / ❌ NEEDS MAJOR REWORK]

### Language Fit  (XX/100)
Required: [e.g., B2 German for non-Berlin Germany engineering role]
Signal: [what the resume shows — explicit cert, inferred from education, none]
Gap: [what's missing or flagged]

### Visa & Work Authorization  (XX/100)
[Pathway: EU citizen / Blue Card eligible / unclear — with threshold context if relevant]
[Note visa authority to verify if borderline]

### CV Format  (XX/100)   ← Full Mode only for most checks; Limited Mode shows partial
Photo: [present/absent — market expectation]
DOB/Marital: [present/absent — market expectation]
Length: [X pages — market expectation]
Style: [tabular/bullet — market expectation]
⚠️  [flag any mismatches]   or   ✅ Format aligned with market norms

### Local Certifications  (XX/100)
✅ Found: [cert1], [cert2], ...
❌ Missing / Recommended: [cert1 — why it matters in this market], ...

### Stack & Tech Preferences  (XX/100)
✅ Matched: [skill1], [skill2], ...
❌ Gaps for this market/role: [skill1], [skill2], ...

### Salary Benchmark  (XX/100)
Market range for [level] in [market]: [range]
Resume signal: [stated / implied / none]
[Alignment note — informational if no salary data in resume]

### Cultural Framing  (XX/100)
[Tone assessment — factual/credentialed vs achievement-led vs superlative-heavy]
[Specific phrases or patterns to change if needed]

### Recommended Job Boards for [Market]
- [Board 1] — [brief note]
- [Board 2] — [brief note]
- [Board 3] — [brief note]

---

### Priority Fixes (ordered by market-fit impact)

| Priority | Fix | Impact |
|----------|-----|--------|
| 🔴 HIGH | [Fix description] | +X pts |
| 🟡 MEDIUM | [Fix description] | +X pts |
| 🟢 LOW | [Fix description] | +X pts |

**Estimated score after all fixes: ~XX%**

---
*Market data uses 2025 benchmarks. Salary ranges are gross annual estimates. Visa thresholds change — verify with BAMF (DE), IND (NL), or the relevant national immigration authority.*
```

---

## Limitations

Always show this footer verbatim:

```
*Market data uses 2025 benchmarks. Salary ranges are gross annual estimates. Visa thresholds change — verify with BAMF (DE), IND (NL), or the relevant national immigration authority.*
```
