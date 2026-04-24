---
description: Check resume compatibility for a target role in a specific regional market (Berlin, Germany, DACH, Europe, Remote-EU, Netherlands, etc.). Scores language fit, visa/work auth, CV format, local certs, stack preferences, salary benchmarks, cultural framing, and job boards. Uses cached profile by default; override with --resume <path>.
allowed-tools: Read, Write, Glob, WebSearch
---

Run market compatibility check for: $ARGUMENTS

Use the `job-search:market-analyzer` skill.

## Parse Arguments

Order of operations:

1. Extract `--resume <path>` if present → store path, set **Full Mode**; remove from args
2. Extract `--market <value>` if present → store market input; remove from args
3. Remaining args → role title (the job you are targeting)

**If role is missing:** ask "What role are you targeting? Example: `/market-check \"Senior Backend Engineer\" --market berlin`"

**If `--market` is missing:** ask "Which market? Supported: `berlin`, `germany`, `dach`, `austria`, `switzerland`, `europe`, `remote-eu`, `netherlands`, `france`, `spain`, `portugal` — and city aliases like `munich`, `vienna`, `amsterdam`, `zurich`."

## Get Resume

**Full Mode** (`--resume <path>` was provided):
- Read the file at that path directly

**Limited Mode** (no `--resume`):
- Read `.cache/active_persona.txt` → get persona slug
- Read `.cache/<persona>/profile.json` → use this as resume data
- If neither file exists: tell user "No cached profile found. Run /input-resume first, or provide your resume with `--resume <path>`."

## Run Analysis

Invoke the `job-search:market-analyzer` skill with:
- The role title
- The raw market input (skill resolves aliases internally)
- The resume text (Full Mode) or profile.json data (Limited Mode)
- The mode (Full or Limited)
