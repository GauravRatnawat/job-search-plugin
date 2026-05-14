Rate resume quality for: $ARGUMENTS

Use the `job-search:resume-rater` skill.

## Parse Arguments

Order of operations:

1. Extract `--resume <path>` if present → store path, set **Full Mode**; remove from args
2. Extract `--role "<value>"` if present (may be quoted) → store role override; remove from args
3. Remaining args → ignored (command takes no positional arguments)

## Detect Mode

**Full Mode** (`--resume <path>` provided):
- Read the file at that path directly as raw resume text
- Line numbers are available — use exact line references in output (e.g., `Line 14`)
- If the file cannot be read or does not exist, tell the user:
  "File not found: <path>. Please check the path and try again." — then stop.

**Cache Mode** (no `--resume`):
- Read `.cache/active_persona.txt` → get persona slug
- Read `.cache/<persona>/profile.json` → use as resume data
- Line numbers are NOT available — use position references in output
  (e.g., `Google — Backend Engineer, bullet 2`)
- If neither file exists: tell user "No cached profile found. Run /input-resume first,
  or provide your resume with `--resume <path>`."

## Detect Target Role

1. If `--role "<value>"` was provided → use that value
2. Else read `data.profile_assessment.recommended_roles[0]` from `profile.json` cache
   — if this field is missing, null, or the array is empty: fall through to step 3
3. Else if no cache → use `"General"` (no role-specific adjustments applied)

## Run Analysis

Invoke the `job-search:resume-rater` skill with:
- The resume text (Full Mode) or profile.json data (Cache Mode)
- The mode (Full or Cache)
- The resolved target role

## Examples

```
/rate-resume
/rate-resume --role "Senior Software Engineer"
/rate-resume --resume ~/Desktop/my-cv.pdf
/rate-resume --resume ~/Desktop/my-cv.pdf --role "Product Manager"
```

If the user provides positional arguments (e.g. `/rate-resume my-cv.pdf` without
`--resume`), inform them: "Positional arguments are not supported. Use:
`/rate-resume --resume <path>`" — then stop.
