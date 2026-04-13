#!/usr/bin/env python3
"""Pipeline cache — persist state between runs, keyed by persona.

Each persona gets their own subdirectory under .cache/ so you can manage
multiple candidates without overwriting data.

Stages (in pipeline order):
    profile         — parsed resume profile (from resume_parser.md)
    search_strategy — generated search queries (from job_hunter.md)
    search_results  — raw job listings from web search (from job_searcher.md)
    scored_jobs     — scored & ranked job list (from job_scorer.md)

Usage:
    python scripts/cache.py status                             # Status for active persona
    python scripts/cache.py status -p gaurav                   # Status for specific persona
    python scripts/cache.py save profile '<json>'              # Save to active persona
    python scripts/cache.py save profile '<json>' -p gaurav    # Save to named persona
    python scripts/cache.py load profile                       # Load from active persona
    python scripts/cache.py clear [stage]                      # Clear one/all stages
    python scripts/cache.py personas                           # List all personas
    python scripts/cache.py use <name>                         # Switch active persona
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

CACHE_DIR = Path(os.environ.get("CACHE_DIR", ".cache"))
ACTIVE_FILE = CACHE_DIR / ".active_persona"

VALID_STAGES = [
    "profile",
    "search_strategy",
    "search_results",
    "scored_jobs",
]

# How long before we consider cached data stale (in hours)
STAGE_TTL = {
    "profile": 720,  # 30 days — resume rarely changes
    "search_strategy": 168,  # 7 days — strategy based on profile
    "search_results": 48,  # 2 days — job listings go stale fast
    "scored_jobs": 48,  # 2 days — tied to search results freshness
}


def _slugify(name: str) -> str:
    """Turn a display name into a filesystem-safe slug."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:40]
    return slug or "default"


def _get_active_persona() -> str:
    """Read the active persona from disk, or return 'default'."""
    if ACTIVE_FILE.exists():
        name = ACTIVE_FILE.read_text().strip()
        if name:
            return name
    return "default"


def _set_active_persona(name: str):
    """Write the active persona to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    ACTIVE_FILE.write_text(name)


def _persona_dir(persona: str) -> Path:
    return CACHE_DIR / persona


def _stage_path(persona: str, stage: str) -> Path:
    return _persona_dir(persona) / f"{stage}.json"


def _meta_path(persona: str, stage: str) -> Path:
    return _persona_dir(persona) / f"{stage}.meta.json"


def _write_meta(persona: str, stage: str, extra: Optional[dict] = None):
    """Write metadata (timestamp, source info) for a cached stage."""
    meta = {
        "persona": persona,
        "stage": stage,
        "cached_at": datetime.now().isoformat(),
        "ttl_hours": STAGE_TTL.get(stage, 48),
    }
    if extra:
        meta.update(extra)
    _meta_path(persona, stage).write_text(json.dumps(meta, indent=2))


def _read_meta(persona: str, stage: str) -> Optional[dict]:
    p = _meta_path(persona, stage)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _is_stale(persona: str, stage: str) -> bool:
    """Check if cached data is older than its TTL."""
    meta = _read_meta(persona, stage)
    if not meta:
        return True
    try:
        cached_at = datetime.fromisoformat(meta["cached_at"])
        ttl = meta.get("ttl_hours", STAGE_TTL.get(stage, 48))
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
        return age_hours > ttl
    except (KeyError, ValueError):
        return True


def _age_str(cached_at: str) -> str:
    """Human-readable age string."""
    try:
        age_dt = datetime.now() - datetime.fromisoformat(cached_at)
        hours = age_dt.total_seconds() / 3600
        if hours < 1:
            return f"{int(hours * 60)}m ago"
        elif hours < 24:
            return f"{hours:.1f}h ago"
        else:
            return f"{hours / 24:.1f}d ago"
    except (ValueError, TypeError):
        return "unknown"


# ── Commands ────────────────────────────────────────────────────


def cmd_save(persona: str, stage: str, data: str, source_file: Optional[str] = None):
    """Save data for a pipeline stage under a persona."""
    if stage not in VALID_STAGES:
        print(json.dumps({"error": f"Invalid stage '{stage}'. Valid: {VALID_STAGES}"}))
        sys.exit(1)

    if source_file:
        try:
            data = Path(source_file).read_text()
        except (OSError, FileNotFoundError) as e:
            print(json.dumps({"error": f"Cannot read file: {e}"}))
            sys.exit(1)

    # Validate JSON
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)

    # Auto-derive persona slug from profile name if saving profile to "default"
    if stage == "profile" and persona == "default":
        name = parsed.get("name", "")
        if name:
            persona = _slugify(name)

    # Ensure persona directory exists
    pdir = _persona_dir(persona)
    pdir.mkdir(parents=True, exist_ok=True)

    # Write the data
    path = _stage_path(persona, stage)
    path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))

    # Write metadata
    extra = {}
    if source_file:
        extra["source_file"] = source_file
    if stage == "profile":
        extra["name"] = parsed.get("name", "")
        extra["location"] = parsed.get("location", "")
    elif stage == "scored_jobs":
        extra["job_count"] = len(parsed) if isinstance(parsed, list) else 0
    elif stage == "search_results":
        if isinstance(parsed, list):
            extra["result_count"] = len(parsed)
        elif isinstance(parsed, dict) and "results" in parsed:
            extra["result_count"] = len(parsed["results"])
        else:
            extra["result_count"] = 0

    _write_meta(persona, stage, extra)

    # Set as active persona
    _set_active_persona(persona)

    size = path.stat().st_size
    print(
        json.dumps(
            {
                "message": f"Cached '{stage}' for persona '{persona}' ({size:,} bytes)",
                "persona": persona,
                "stage": stage,
                "file": str(path),
                "size_bytes": size,
            }
        )
    )


def cmd_load(persona: str, stage: str):
    """Load cached data for a pipeline stage."""
    if stage not in VALID_STAGES:
        print(json.dumps({"error": f"Invalid stage '{stage}'. Valid: {VALID_STAGES}"}))
        sys.exit(1)

    path = _stage_path(persona, stage)
    if not path.exists():
        print(
            json.dumps(
                {
                    "error": f"No cached data for '{stage}' (persona: '{persona}')",
                    "persona": persona,
                    "cached": False,
                }
            )
        )
        sys.exit(1)

    stale = _is_stale(persona, stage)
    meta = _read_meta(persona, stage) or {}
    data = json.loads(path.read_text())

    print(
        json.dumps(
            {
                "persona": persona,
                "stage": stage,
                "cached": True,
                "stale": stale,
                "cached_at": meta.get("cached_at", "unknown"),
                "data": data,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    )


def cmd_status(persona: str):
    """Show which stages are cached and their freshness for a persona."""
    stages = []
    for stage in VALID_STAGES:
        path = _stage_path(persona, stage)
        meta = _read_meta(persona, stage)
        if path.exists() and meta:
            cached_at = meta.get("cached_at", "unknown")
            stale = _is_stale(persona, stage)
            size = path.stat().st_size

            info = {
                "stage": stage,
                "cached": True,
                "stale": stale,
                "age": _age_str(cached_at),
                "cached_at": cached_at,
                "size_bytes": size,
                "ttl_hours": STAGE_TTL.get(stage, 48),
            }
            # Add stage-specific summary
            if stage == "profile":
                info["name"] = meta.get("name", "")
                info["location"] = meta.get("location", "")
            elif stage == "scored_jobs":
                info["job_count"] = meta.get("job_count", 0)
            elif stage == "search_results":
                info["result_count"] = meta.get("result_count", 0)
            stages.append(info)
        else:
            stages.append({"stage": stage, "cached": False})

    cached_stages = [s for s in stages if s.get("cached")]
    fresh_stages = [s for s in cached_stages if not s.get("stale")]

    print(
        json.dumps(
            {
                "persona": persona,
                "total_stages": len(VALID_STAGES),
                "cached": len(cached_stages),
                "fresh": len(fresh_stages),
                "stale": len(cached_stages) - len(fresh_stages),
                "missing": len(VALID_STAGES) - len(cached_stages),
                "stages": stages,
            },
            indent=2,
        )
    )


def cmd_clear(persona: str, stage: Optional[str] = None):
    """Clear one stage or all cached data for a persona."""
    if stage and stage not in VALID_STAGES:
        print(json.dumps({"error": f"Invalid stage '{stage}'. Valid: {VALID_STAGES}"}))
        sys.exit(1)

    cleared = []
    targets = [stage] if stage else VALID_STAGES

    for s in targets:
        for path in [_stage_path(persona, s), _meta_path(persona, s)]:
            if path.exists():
                path.unlink()
                cleared.append(str(path))

    # Remove persona dir if empty
    pdir = _persona_dir(persona)
    if pdir.exists() and not any(pdir.iterdir()):
        pdir.rmdir()
        cleared.append(str(pdir))

    print(
        json.dumps(
            {
                "message": f"Cleared {len(cleared)} files for persona '{persona}'",
                "persona": persona,
                "cleared": cleared,
            }
        )
    )


def cmd_personas():
    """List all personas with summary info."""
    if not CACHE_DIR.exists():
        print(json.dumps({"personas": [], "active": "default"}))
        return

    active = _get_active_persona()
    personas = []

    for d in sorted(CACHE_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        name = d.name
        # Read profile meta for display name
        meta = _read_meta(name, "profile")
        display_name = meta.get("name", name) if meta else name
        location = meta.get("location", "") if meta else ""

        # Count cached stages
        cached = sum(1 for s in VALID_STAGES if _stage_path(name, s).exists())
        fresh = sum(
            1
            for s in VALID_STAGES
            if _stage_path(name, s).exists() and not _is_stale(name, s)
        )

        personas.append(
            {
                "slug": name,
                "display_name": display_name,
                "location": location,
                "active": name == active,
                "cached_stages": cached,
                "fresh_stages": fresh,
            }
        )

    print(
        json.dumps(
            {
                "active": active,
                "personas": personas,
                "total": len(personas),
            },
            indent=2,
        )
    )


def cmd_use(persona: str):
    """Switch the active persona."""
    pdir = _persona_dir(persona)
    if not pdir.exists():
        # Check if it's a display name that matches a slug
        found = False
        if CACHE_DIR.exists():
            for d in CACHE_DIR.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    meta = _read_meta(d.name, "profile")
                    if meta and _slugify(meta.get("name", "")) == _slugify(persona):
                        persona = d.name
                        found = True
                        break
        if not found:
            print(
                json.dumps(
                    {
                        "error": f"Persona '{persona}' not found. Run 'personas' to see available ones.",
                        "hint": "Save a profile first to create a persona.",
                    }
                )
            )
            sys.exit(1)

    _set_active_persona(persona)
    meta = _read_meta(persona, "profile")
    display_name = meta.get("name", persona) if meta else persona

    print(
        json.dumps(
            {
                "message": f"Active persona set to '{persona}'",
                "persona": persona,
                "display_name": display_name,
            }
        )
    )


# ── CLI ─────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline cache manager (persona-aware)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Add -p/--persona to every subparser so it can appear anywhere
    persona_kwargs = {
        "default": None,
        "help": "Persona name (default: active persona)",
    }

    p_save = sub.add_parser("save", help="Save stage data")
    p_save.add_argument("-p", "--persona", **persona_kwargs)
    p_save.add_argument("stage", choices=VALID_STAGES, help="Pipeline stage")
    p_save.add_argument("data", nargs="?", default="", help="JSON string")
    p_save.add_argument("-f", "--file", help="Read data from file instead")

    p_load = sub.add_parser("load", help="Load cached stage data")
    p_load.add_argument("-p", "--persona", **persona_kwargs)
    p_load.add_argument("stage", choices=VALID_STAGES, help="Pipeline stage")

    p_status = sub.add_parser("status", help="Show cache status for active persona")
    p_status.add_argument("-p", "--persona", **persona_kwargs)

    p_clear = sub.add_parser("clear", help="Clear cached data")
    p_clear.add_argument("-p", "--persona", **persona_kwargs)
    p_clear.add_argument(
        "stage",
        nargs="?",
        choices=VALID_STAGES,
        help="Stage to clear (omit for all)",
    )

    sub.add_parser("personas", help="List all personas")

    p_use = sub.add_parser("use", help="Switch active persona")
    p_use.add_argument("name", help="Persona name or slug")

    p_list = sub.add_parser("list", help="List cached files for active persona")
    p_list.add_argument("-p", "--persona", **persona_kwargs)

    args = parser.parse_args()

    # Resolve persona: explicit -p flag > active > default
    persona = getattr(args, "persona", None) or _get_active_persona()

    if args.command == "save":
        if args.file:
            cmd_save(persona, args.stage, "", source_file=args.file)
        elif args.data:
            cmd_save(persona, args.stage, args.data)
        else:
            cmd_save(persona, args.stage, sys.stdin.read())
    elif args.command == "load":
        cmd_load(persona, args.stage)
    elif args.command == "status":
        cmd_status(persona)
    elif args.command == "clear":
        cmd_clear(persona, getattr(args, "stage", None))
    elif args.command == "personas":
        cmd_personas()
    elif args.command == "use":
        cmd_use(args.name)
    elif args.command == "list":
        cmd_list(persona)


def cmd_list(persona: str):
    """List all cached files for a persona."""
    pdir = _persona_dir(persona)
    if not pdir.exists():
        print(
            json.dumps(
                {
                    "persona": persona,
                    "files": [],
                    "message": f"No cache for persona '{persona}'",
                }
            )
        )
        return

    files = []
    for f in sorted(pdir.iterdir()):
        if f.is_file():
            files.append(
                {
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
            )

    print(
        json.dumps(
            {
                "persona": persona,
                "files": files,
                "total": len(files),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
