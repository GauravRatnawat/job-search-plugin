# Job Search Assistant

An AI recruiter workflow distributed as agent instructions. Drop in your resume, get back targeted roles, scored jobs, tailored applications, and interview prep — all from your AI agent. **No API keys. No setup. No external services.**

This document is the **canonical orchestrator** (per AD-1 of the architecture spine). Companion entry points (`plugin.md` for Claude Projects, `skill/SKILL.md` for skill-mode install, `.claude-plugin/plugin.json` for Claude Code plugin) defer to it for orchestration rules.

## Canonical Orchestrator (AD-1)

`AGENTS.md` is the single source of truth for these orchestration rules:

- **Auto-trigger** the pipeline (AD-9)
- **Cache-first** orchestration (AD-1, AD-8)
- **Intent routing** to skills (AD-3, AD-10)
- **Capability map** for every skill (AD-3)
- **Multi-agent tier** support (AD-11)
- **Output rules** contract (FR-7.1 through FR-7.9 + AD-19)

`plugin.md` and `skill/SKILL.md` are thin shims that reference this file. Adding a new invariant once, here, is sufficient — downstream surfaces inherit it.

## Multi-Agent Support (AD-11)

Three tiers, declared honestly per release:

| Tier | Hosts | Verification |
|---|---|---|
| **Tier 1 — CI-verified** | Claude Code | Full eval suite (per AD-13) runs against this host each release. |
| **Tier 2 — Declared compatible** | Codex, Cursor, opencode | Spot-checked manually each release; no CI. |
| **Tier 3 — Best-effort** | Copilot, Gemini, Aider, Crush, Warp, and any agent that reads `AGENTS.md` | Runs via this file; no testing claim per release. |

Tier promotion requires evidence (CI runs for Tier 1, spot-test record for Tier 2). When in doubt about your host, you are Tier 3 — proceed but expect rough edges where slash commands and plugin manifests don't apply.

## What to Do

When the user wants to:

- analyze a resume
- find matching jobs
- score and rank opportunities
- tailor a resume
- write a cover letter
- prepare for an interview
- check ATS compatibility for a target role
- score regional market fit (e.g. DACH, EU)
- save or update applications in the tracker

...run the recruiter workflow described below instead of treating it like a generic coding task.

## Auto-trigger Rule (AD-9)

The full pipeline (parse resume → strategic assessment → search → score → deliver) **auto-runs only when the candidate provides a resume with no other instruction.** Any other intent (tailor, cover letter, interview prep, tracker, market check, apply, view, persona switch) requires an explicit slash command or free-text intent match per the Intent Routing table below.

The candidate does not need to invoke each pipeline step manually when sharing a resume.

## Operating Model

- **File reading:** Use your built-in file reading to parse resumes (PDF, DOCX, TXT).
- **Web search:** Use your built-in web search to find real, current job listings.
- **File I/O:** Read and write JSON files directly for the tracker (`job_tracker.json`) and pipeline cache (`.cache/`).
- **Skill documents:** Read the relevant instruction files in `skills/` as you move through each pipeline step.

No scripts, no Python, no dependencies. Everything is done through your native file read/write and web search capabilities. (Per PRD NFR-1, NFR-2, NFR-3 and AD-5 zero non-native deps.)

## Skill Capabilities (AD-3)

Every `skills/<name>/SKILL.md` declares its `capability` (and `subcapability` where it shares a bucket with other skills). The orchestrator routes user intent to capabilities, not skill names.

**Capability enum:** `parse | hunt | search | score | analyze | tailor | write | prep | check | track | apply | view | admin`

**Skill → capability map (v1):**

| Skill | Capability | Subcapability |
|---|---|---|
| `skills/resume-parser` | `parse` | — |
| `skills/job-hunter` | `hunt` | — |
| `skills/job-searcher` | `search` | — |
| `skills/job-scorer` | `score` | — |
| `skills/job-search-analyst` | `analyze` | `dedupe-filter` |
| `skills/market-analyzer` | `analyze` | `regional-market` |
| `skills/resume-rater` | `analyze` | `resume-quality` |
| `skills/resume-tailor` | `tailor` | — |
| `skills/cover-letter-writer` | `write` | — |
| `skills/interview-prep` | `prep` | — |
| `skills/ats-analyzer` | `check` | — |
| `skills/application-tracker` | `track` | — |

`subcapability:` is required only when multiple skills share a `capability` (currently the `analyze` bucket has three).

> **Note on frontmatter rollout:** The skill files in this repo do not yet carry `capability:` frontmatter — that update is tracked separately in `_bmad-output/implementation-artifacts/deferred-work.md` as Goal B. Until Goal B ships, the orchestrator may route by skill name during the transition; once Goal B ships, capability-based routing is the only path.

## Intent Routing (AD-10)

**Tier 1 hosts (Claude Code):** slash commands are primary entry points (e.g. `/job-search:input-resume`, `/job-search:tailor-resume 3`).

**Tier 2 and Tier 3 hosts:** free-text intent routing per the table below. Every slash command must also be reachable via at least one documented free-text phrase.

| User phrase (examples) | Capability | Skill |
|---|---|---|
| "here's my resume", "parse this resume", "analyze my CV" | `parse` | `skills/resume-parser` |
| "find me jobs", "hunt for openings", "what should I apply for" | `hunt` | `skills/job-hunter` |
| "search Naukri / Internshala / LinkedIn for X" | `search` | `skills/job-searcher` |
| "score these jobs", "rate the matches", "rank by fit" | `score` | `skills/job-scorer` |
| "dedupe these results", "filter the listings" | `analyze` / `dedupe-filter` | `skills/job-search-analyst` |
| "score me for the Berlin market", "DACH compatibility" | `analyze` / `regional-market` | `skills/market-analyzer` |
| "rate my resume quality", "review my CV writing" | `analyze` / `resume-quality` | `skills/resume-rater` |
| "tailor my resume for #3", "rewrite my resume for Razorpay" | `tailor` | `skills/resume-tailor` |
| "write a cover letter for #3" | `write` | `skills/cover-letter-writer` |
| "prep me for the Postman interview", "interview questions for Atlan" | `prep` | `skills/interview-prep` |
| "will this resume pass the ATS for #3", "ATS check" | `check` | `skills/ats-analyzer` |
| "save these to my tracker", "I applied to #5", "show pipeline" | `track` | `skills/application-tracker` |
| "draft an email to apply for #3", "apply to Razorpay", "help me apply" | `apply` | `commands/apply.md` (host-surface, not a `skills/` entry — writes to `application_drafts/<company>-<role>.txt`) |

## Pipeline Cache (AD-7, AD-8)

Results are cached per-persona between sessions to avoid re-parsing resumes and re-searching. **Always check the cache before starting work** (cache-first orchestration per AD-1).

Cache files are stored in `.cache/<persona>/` as JSON. **Every cache file uses the AD-7 envelope shape:**

```json
{
  "cached_at": "2026-06-28T10:30:00Z",
  "schema_version": 1,
  "ttl_days": 30,
  "data": { ... }
}
```

**Envelope fields:**

- `cached_at` — ISO 8601 UTC timestamp of the write.
- `schema_version` — integer; starts at `1`; breaking shape changes bump it. **Readers MUST check `schema_version` before parsing `data`.** On mismatch, invalidate this slice and rebuild from upstream.
- `ttl_days` — integer; lives in the envelope per AD-8. Reader skill computes `today - cached_at` against `ttl_days` to determine freshness. **Single source of truth — no separate TTL table.** (The `Default ttl_days` column in the owner table below is informational: it lists the default value an owner skill SHOULD write when first creating its slice. Readers always read `ttl_days` from the envelope, never from this table.)
- `data` — the slice payload.

**Cache slices and their owners (AD-6):**

| File | Owner skill | Default `ttl_days` |
|---|---|---|
| `.cache/<persona>/profile.json` | `resume-parser` | 30 |
| `.cache/<persona>/search_strategy.json` | `job-hunter` | 7 |
| `.cache/<persona>/search_results.json` | `job-searcher` | 2 |
| `.cache/<persona>/scored_jobs.json` | `job-scorer` | 2 |
| `job_tracker.json` (project root, not in `.cache/`) | `application-tracker` | n/a (no TTL — user-managed pipeline state) |

**One-owner-per-slice rule (AD-6):** each cache slice has exactly one writer skill. The orchestrator never writes to data slices; it only manages `active_persona.txt` and persona directory lifecycle.

**Cache file at top level:**

- `.cache/active_persona.txt` — the currently active persona slug. Orchestrator-owned (AD-16). Skills MUST NOT write to this file.

> **Migration note for legacy cache files:** Existing cache files in this repo (created before the AD-7 envelope landed) use the older shape `{cached_at, data}` without `schema_version` or `ttl_days`. Reader skills MUST treat any cache file missing `schema_version` as legacy → invalidate the slice → trigger re-parse from upstream. Migration scripts are deferred (per the architecture spine's Deferred section).

### Multi-Persona Support (AD-14, AD-15, AD-16)

Each candidate gets their own cache directory under `.cache/<persona-slug>/`. **Personas are hard-isolated** — a skill operating on persona A cannot read from `.cache/<persona-B>/` or `job_tracker.json` entries scoped to persona B (AD-15).

**Persona slug derivation (AD-14):** the slug rule handles ASCII names directly and non-ASCII names via Unicode normalization. The full algorithm:

1. **Normalize.** Apply Unicode NFKD decomposition to separate base characters from combining marks (e.g. `"é"` → `"e" + combining-acute`).
2. **Transliterate.** Drop all combining marks and any other non-Latin-script characters. Keep only ASCII letters, digits, and the original separators (space, hyphen, apostrophe, etc.).
3. **Lowercase.** Convert remaining text to lowercase.
4. **Collapse runs.** Replace any non-`[a-z0-9]` run (a maximal contiguous span of non-alphanumeric ASCII characters) with a single `-`.
5. **Trim.** Strip leading and trailing `-`.
6. **Validate.** If the result is non-empty, use it as the slug. If the result is empty (all characters dropped during step 2), fall back to `candidate-{hash8}` where `hash8` is the first 8 hex characters of a deterministic hash (e.g. SHA-1) of the original name string.
7. **Empty-name guard.** If the input name is itself empty or whitespace-only, the orchestrator MUST halt and ask the user for guidance — never silently create an unidentifiable persona directory.

Examples — including the non-ASCII edge cases that the previous wording could not handle:

| Input | Slug | Notes |
|---|---|---|
| `"Gaurav Ratnawat"` | `gaurav-ratnawat` | ASCII baseline |
| `"Priya R. Sharma"` | `priya-r-sharma` | period collapses as part of `" . "` run |
| `"Anish O'Malley"` | `anish-o-malley` | apostrophe is one run; `o` between apostrophe and space is preserved |
| `"María García"` | `maria-garcia` | NFKD strips combining acute |
| `"Jean-Paul Sartre"` | `jean-paul-sartre` | existing hyphen counts as a run, collapses to single `-` |
| `"John   Doe"` | `john-doe` | multiple spaces are one run |
| `"李明"` | `candidate-{hash8}` | no Latin-script characters survive transliteration; deterministic fallback |
| `"@@@"` | `candidate-{hash8}` | no alphanumerics survive; same fallback |
| `"Anish 李"` | `anish-{hash8}` | partial Latin keeps the prefix; suffix-hash carries the rest |
| `""` (empty) | ERROR | orchestrator halts, asks user |

The `{hash8}` fallback is deterministic — same input always produces the same slug — so a candidate with a non-Latin-script name still gets a stable persona across sessions.

**Active persona ownership (AD-16):** the orchestrator owns `active_persona.txt`. On first resume share with no active persona, the orchestrator derives the slug, creates `.cache/<slug>/`, writes `active_persona.txt`, and proceeds (FR-0.3 auto-bootstrap). Skills MUST NOT write `active_persona.txt`.

**Persona-mismatch check before write (AD-17):** when a resume arrives and the derived slug differs from `active_persona.txt`, the orchestrator MUST surface a persona-mismatch prompt and pause for user confirmation **before** invoking the parse skill. Prevents silent overwrite of persona-A's `profile.json` with persona-B's resume content.

- To switch personas explicitly: tell the agent `switch to persona <slug>` (free-text) or `/job-search:persona <slug>` (Claude Code slash command).
- To list personas: list the directories under `.cache/`.

## Workflow

Each step has a detailed instruction file. Read it before executing that step.

1. **Parse resume** — Read `skills/resume-parser/SKILL.md` and follow its instructions.
2. **Generate search strategy** — Read `skills/job-hunter/SKILL.md`.
3. **Execute job searches** — Read `skills/job-searcher/SKILL.md`.
4. **Deduplicate and filter** — Read `skills/job-search-analyst/SKILL.md`.
5. **Score and rank** — Read `skills/job-scorer/SKILL.md`.
6. **Deliver prioritized list** with application links.
7. **Follow-up actions** as needed:
   - `skills/application-tracker/SKILL.md` — save/view/update tracked jobs
   - `skills/resume-tailor/SKILL.md` — customize resume for a target job
   - `skills/cover-letter-writer/SKILL.md` — write a personalized cover letter
   - `skills/interview-prep/SKILL.md` — prepare for an interview
   - `skills/ats-analyzer/SKILL.md` — check if resume will pass ATS filtering for a target job
   - `skills/market-analyzer/SKILL.md` — score resume compatibility for a regional market (Berlin, DACH, EU, etc.)
   - `skills/resume-rater/SKILL.md` — score resume quality across Impact, Brevity, Style, and Sections

## Tracker

The tracker is a JSON file at `job_tracker.json`. Read `skills/application-tracker/SKILL.md` for the full schema and instructions. The agent reads and writes this file directly — no scripts needed. (Per AD-6: `application-tracker` is the sole writer.)

## Output Rules (AD-19 surface-enforcement contract)

These rules form a **coherent contract** — weakening any one weakens the rest. Each rule names how it is enforced (structurally in code, or via skill prompt + AD-13 evals).

| # | Rule | Enforcement |
|---|---|---|
| FR-7.1 | Find at least 20 relevant jobs unless the candidate narrows scope further. | Prompt + AD-13 eval (`job-hunter` + `job-searcher`). |
| FR-7.2 | Every included job needs a valid application link. | Prompt + AD-13 eval (`job-searcher`); link-liveness check is open work. |
| FR-7.3 | Be honest about fit scores; do not inflate. (Per G-2 and NFR-8.) | Prompt + AD-13 eval (`job-scorer` honesty contract). |
| FR-7.4 | Prefer fresher-friendly reasoning when the candidate is early-career. | Prompt + AD-13 eval (`job-scorer` fresher-aware behavior). |
| FR-7.5 | Default to location-aware search strategy based on the candidate's resume (city, country, willingness to relocate). | Prompt (`job-hunter` + `job-searcher`). |
| FR-7.6 | Present final job lists in a scannable table. | Prompt (`job-scorer` output template — see UX EXPERIENCE.md §Component Patterns). |
| FR-7.7 | For applications, provide the user with direct links. Draft emails as local text files only. | **Structural (AD-19):** `apply` capability writes only to `application_drafts/<company>-<role>.txt`. Submission paths not implemented in v1. |
| FR-7.8 | NEVER submit applications on behalf of the user. (Per G-3.) | **Structural (AD-19):** no submission code path exists. Requires candidate confirmation for any non-local action. |
| FR-7.9 | NEVER auto-apply to LinkedIn or Indeed. (Per G-4.) | **Structural (AD-19):** no LinkedIn / Indeed integration in v1. |

**No resume fabrication (G-5):** `resume-tailor` and `cover-letter-writer` prompts forbid inventing skills, jobs, or dates not in the source resume. Enforcement is prompt + AD-13 eval ("fabrication detection" cases).

**No scraping at scale (G-6):** the `job-searcher` skill uses only the host's native web search. No HTTP clients, no scraper libraries (per AD-5).

**MIT open source (G-7):** the repository `LICENSE` file must remain MIT for v1. `.claude-plugin/plugin.json` `license` field must read `"MIT"`. CI must fail any release where either changes.

## Project Structure

```
skills/                          12 skill instruction documents (read as pipeline steps)
  resume-parser/SKILL.md         capability: parse
  job-hunter/SKILL.md            capability: hunt
  job-searcher/SKILL.md          capability: search
  job-scorer/SKILL.md            capability: score
  job-search-analyst/SKILL.md    capability: analyze / dedupe-filter
  application-tracker/SKILL.md   capability: track
  resume-tailor/SKILL.md         capability: tailor
  cover-letter-writer/SKILL.md   capability: write
  interview-prep/SKILL.md        capability: prep
  ats-analyzer/SKILL.md          capability: check
  market-analyzer/SKILL.md       capability: analyze / regional-market
  resume-rater/SKILL.md          capability: analyze / resume-quality
.claude/commands/                Slash commands (Claude Code standalone)
commands/                        Slash commands (Claude Code plugin)
.claude-plugin/plugin.json       Claude Code plugin manifest
.claude-plugin/marketplace.json  Marketplace listing
plugin.md                        Claude Projects orchestrator (shim → AGENTS.md per AD-1)
skill/SKILL.md                   Installable Claude Code skill (shim → AGENTS.md per AD-1)
tools/view.sh                    Optional gum-based TUI (AD-5 polish layer — never required)
evals/                           AD-13 calibration sets (does not yet exist; deferred to first eval sprint)
.cache/                          Pipeline cache (gitignored; AD-6/7/8/15/16 contract)
job_tracker.json                 Application tracker (gitignored; AD-6 application-tracker owns)
application_drafts/              Apply helper outputs (gitignored)
_bmad-output/                    Planning artifacts (PRD, UX spines, architecture spine, this file's source-of-truth ADs). Read-only to skills per AD-23.
```

## Reference

- **Architecture spine (source of truth for all AD-N citations):** `_bmad-output/planning-artifacts/architecture/architecture-job-search-mcp-2026-06-28/ARCHITECTURE-SPINE.md`
- **PRD (FR / NFR / G / R / O references):** `_bmad-output/planning-artifacts/prds/prd-job-search-mcp-2026-06-28/prd.md`
- **UX (DESIGN.md visual identity, EXPERIENCE.md IA + state patterns + voice rules):** `_bmad-output/planning-artifacts/ux-designs/ux-job-search-mcp-2026-06-28/`
