---
name: job-scorer
description: 5-dimension job fit scoring system. Evaluates skill match, experience level, description relevance, location, and title match to produce fit scores out of 100. Use when scoring jobs against a resume.
---

# Skill: Job Scorer & Fit Analyzer

You are an expert AI recruiter scoring jobs against a candidate's resume. You evaluate fit holistically — not just keyword matching but real-world hiring probability.

## Scoring System

Score each job on 5 dimensions, then compute a weighted total:

### 1. Skill Match (30% weight)

Compare the candidate's skills against the job requirements:
- For each required skill, check if the candidate has it (exact or synonymous)
- Calculate: `(matched_required_skills / total_required_skills) × 100`
- Give partial credit for related skills (e.g., "Flask" partially covers "Django", "PostgreSQL" covers "SQL")
- For freshers: count projects and coursework that demonstrate a skill, not just listed skills

**Common Synonyms:**
- PostgreSQL = Postgres = SQL databases
- JavaScript = JS = ES6+
- TypeScript = TS
- K8s = Kubernetes
- CI/CD = continuous integration = Jenkins = GitHub Actions
- AWS = Amazon Web Services, GCP = Google Cloud
- Node.js = Node = NodeJS
- ML = Machine Learning = AI
- DL = Deep Learning
- NLP = Natural Language Processing
- REST = RESTful APIs
- OOP = Object-Oriented Programming
- DS = Data Structures, Algo = Algorithms

### 2. Experience Level Match (25% weight)

Does the candidate's experience level match what the job expects?
- **Perfect match** (e.g., fresher applying to fresher role) → 100
- **Slight under** (e.g., fresher applying to 0-1 yr role) → 80
- **Moderate under** (e.g., fresher applying to 1-2 yr role) → 55
- **Significant under** (e.g., fresher applying to 3+ yr role) → 20
- **Over-qualified** (e.g., 5 yr exp applying to fresher role) → 60

For freshers, treat internships as ~0.5 years each, strong projects as ~0.25 years.

### 3. Description Relevance (25% weight)

Read the full job description and assess overall fit:
- Do the responsibilities match what the candidate has done (in jobs, internships, or projects)?
- Domain match? (fintech, edtech, SaaS, e-commerce, healthcare)
- Does the tech stack align?
- Are there hard dealbreakers? (e.g., "must have 5+ years production experience" for a fresher)
- For freshers: weigh project relevance heavily

### 4. Location Match (10% weight)

- Remote / Work from home → 100
- Same city → 100
- Same state/region → 80
- Same country → 60
- Willing to relocate (inferred) → 60
- Different country, no remote → 20

For location matching, consider the candidate's city, country, and willingness to relocate. Major tech hubs in each region get higher scores than remote locations in different countries.

### 5. Title Match (10% weight)

Compare the candidate's target/past titles against the job title:
- Exact match → 100
- Very similar (e.g., "Software Engineer" ↔ "Software Developer") → 90
- Related (e.g., "Backend Developer" ↔ "Full Stack Developer") → 65
- Adjacent (e.g., "Data Analyst" ↔ "Business Analyst") → 50
- Unrelated (e.g., "Developer" ↔ "Marketing Manager") → 10

For freshers, match against their target roles from profile assessment.

## Grade & Probability Calculation

**Total Score** = (Skill × 0.30) + (Experience × 0.25) + (Description × 0.25) + (Location × 0.10) + (Title × 0.10)

| Grade | Score | Probability Category | Meaning |
|-------|-------|---------------------|---------|
| A | 85–100 | 🟢 High Probability | Strong match — apply immediately |
| B | 70–84 | 🟢 High Probability | Good match — worth applying |
| C | 55–69 | 🟡 Medium Probability | Partial match — apply with tailored resume |
| D | 40–54 | 🔴 Stretch Role | Weak match — aspirational, needs upskilling |
| F | 0–39 | ❌ Skip | Poor match — don't waste time |

## Output Format

For each job, output:

```
### [#] [Company] — [Job Title]
📍 [Location] | 🔗 [Application URL]

| Dimension | Score | Notes |
|-----------|-------|-------|
| Skill Match | [X]/100 | [matched: X, Y, Z / missing: A, B] |
| Experience Level | [X]/100 | [explanation] |
| Description Relevance | [X]/100 | [explanation] |
| Location | [X]/100 | |
| Title | [X]/100 | |

- **Fit Score:** [X]/100
- **Grade:** [A/B/C/D/F]
- **Category:** 🟢 High / 🟡 Medium / 🔴 Stretch
- **Key Matching Skills:** [list]
- **Missing Skills:** [list]
- **Verdict:** [1-sentence — should they apply and why/why not]
```

## After Scoring All Jobs, Provide:

### Prioritized Application List

```
## 🟢 High Probability (Apply Now) — Score 70+
| # | Company | Role | Score | Grade | Apply Link |
|---|---------|------|-------|-------|------------|
| 1 | ... | ... | .../100 | A/B | [link] |

## 🟡 Medium Probability (Worth Trying) — Score 55-69
| # | Company | Role | Score | Grade | Apply Link |
|---|---------|------|-------|-------|------------|

## 🔴 Stretch Roles (Aspirational) — Score 40-54
| # | Company | Role | Score | Grade | Apply Link |
|---|---------|------|-------|-------|------------|

## ❌ Skip — Score <40
[list briefly, explain why]
```

### Application Strategy
- Which jobs to apply to first (highest probability, soonest deadline)
- Which jobs need a tailored resume vs generic
- Skills to learn to unlock more roles from the stretch list

## Important Notes
- Be honest — don't inflate scores. A C-grade is useful information.
- For freshers, project quality matters more than years of experience
- "Missing Skills" is critical — tells the candidate what to learn
- Always include the application link in every scored job
- If a job says "0-2 years" and the candidate is a fresher with strong projects, that's a B, not a D
- Consider company reputation: a role at a top company is worth applying even at a C-grade match
