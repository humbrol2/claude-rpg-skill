#!/usr/bin/env python3
"""Build memory_dir/registry.json from all memory files. Fast-lookup index of canon.

Usage: python registry_build.py [--memory-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir, list_memory_files, parse_frontmatter


def normalize_name(name: str) -> str:
    # Separator forms vary: memory linters slugify frontmatter `name:` fields to
    # kebab-case ("berth-authority") while narration uses spaces ("Berth Authority").
    # Fold hyphens, underscores, and runs of whitespace to a single space so a name
    # resolves in either form.
    return re.sub(r"[-_\s]+", " ", name.strip().lower())


def extract_roster_entities(path: Path, body: str) -> list[dict]:
    """Scan a roster file's body for per-entity bold sections like '**Name** — ...'.

    Returns list of {name, blurb, line_start} for each detected entity heading.
    """
    import re
    found = []
    pattern = re.compile(r"^\*\*([A-Z][A-Za-z0-9_'\- ]+?)\*\*\s*[—\-]\s*(.+?)$", re.MULTILINE)
    for match in pattern.finditer(body):
        name = match.group(1).strip()
        # Strip trailing italicized role descriptors and asterisks
        blurb_raw = match.group(2).strip().rstrip(".*")
        blurb = blurb_raw.strip("*").strip()
        found.append({"name": name, "blurb": blurb, "file": path.name})
    return found


def build_registry(memory_dir: Path) -> dict:
    entities = {}
    by_alias = {}
    by_type = {}

    for path in list_memory_files(memory_dir):
        try:
            text = path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(text)
        except Exception as exc:
            # A single unreadable / malformed file must not sink the whole index.
            print(f"  warning: skipped {path.name} ({exc})", file=sys.stderr)
            continue
        if not fm:
            continue

        # Primary entry for the file itself
        entity = {
            "file": path.name,
            "name": fm.get("name", path.stem),
            "type": fm.get("type", "unknown"),
            "description": fm.get("description", ""),
            "frontmatter": fm,
        }

        key = normalize_name(entity["name"])
        entities[key] = entity

        aliases = fm.get("aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                by_alias[normalize_name(alias)] = key

        type_key = entity["type"]
        by_type.setdefault(type_key, []).append(entity["name"])

        # Roster expansion — extract per-entity sections from the body
        # Triggered if frontmatter description contains "roster" or filename has "roster"
        is_roster = (
            "roster" in fm.get("description", "").lower()
            or "roster" in path.name.lower()
            or "entities" in fm  # explicit declaration
        )
        if is_roster:
            roster_entries = extract_roster_entities(path, body)
            for sub in roster_entries:
                sub_key = normalize_name(sub["name"])
                # Don't overwrite existing primary entries
                if sub_key in entities:
                    continue
                sub_entity = {
                    "file": path.name,
                    "name": sub["name"],
                    "type": fm.get("type", "unknown") + "_roster_member",
                    "description": sub["blurb"][:200],
                    "frontmatter": {
                        "name": sub["name"],
                        "description": sub["blurb"][:200],
                        "type": fm.get("type", "unknown") + "_roster_member",
                        "parent_file": path.name,
                        "parent_roster": fm.get("name", path.stem),
                    },
                }
                entities[sub_key] = sub_entity
                by_type.setdefault(sub_entity["type"], []).append(sub["name"])

    return {
        "entities": entities,
        "by_alias": by_alias,
        "by_type": by_type,
        "count": len(entities),
    }


def referenced_canon_files(memory_dir: Path) -> set[str]:
    """Collect every project_*.md / entity_*.md filename referenced in MEMORY.md.

    Catches markdown link targets ``](project_x.md)`` and bare filename mentions.
    Returns an empty set if MEMORY.md is absent.
    """
    import re
    index = memory_dir / "MEMORY.md"
    if not index.exists():
        return set()
    text = index.read_text(encoding="utf-8")
    # Any project_/entity_ .md filename token, whether inside a [link](...) or bare.
    pattern = re.compile(r"((?:project|entity)_[A-Za-z0-9_\-]+\.md)")
    return {m.group(1) for m in pattern.finditer(text)}


def orphan_report(memory_dir: Path) -> dict:
    """Diff MEMORY.md against the canon files on disk.

    - dangling:  referenced in MEMORY.md but the file does not exist (e.g. canon
                 that only ever lived in transcript). The critical failure.
    - unindexed: a project_/entity_ file exists on disk but MEMORY.md never links it
                 (canon that won't be surfaced on load).
    """
    referenced = referenced_canon_files(memory_dir)
    on_disk = {
        p.name
        for p in list_memory_files(memory_dir)
        if p.name.startswith(("project_", "entity_"))
    }
    dangling = sorted(referenced - on_disk)
    unindexed = sorted(on_disk - referenced)
    return {
        "has_index": (memory_dir / "MEMORY.md").exists(),
        "referenced": len(referenced),
        "on_disk": len(on_disk),
        "dangling": dangling,
        "unindexed": unindexed,
    }


def print_orphan_report(memory_dir: Path) -> None:
    """Print the MEMORY.md-vs-disk orphan diff in a human-readable form."""
    rep = orphan_report(memory_dir)
    print()
    if not rep["has_index"]:
        print("ORPHAN CHECK: no MEMORY.md found — cannot diff.")
        return
    print(
        f"ORPHAN CHECK: {rep['referenced']} canon files referenced in MEMORY.md, "
        f"{rep['on_disk']} on disk."
    )
    if rep["dangling"]:
        print(f"  DANGLING ({len(rep['dangling'])}) — linked in MEMORY.md, file MISSING:")
        for name in rep["dangling"]:
            print(f"    - {name}")
    if rep["unindexed"]:
        print(f"  UNINDEXED ({len(rep['unindexed'])}) — file on disk, not linked in MEMORY.md:")
        for name in rep["unindexed"]:
            print(f"    - {name}")
    if not rep["dangling"] and not rep["unindexed"]:
        print("  CLEAN — index and disk agree.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory-dir", type=Path, default=None)
    ap.add_argument(
        "--check",
        action="store_true",
        help="After building, diff MEMORY.md against disk and report orphans.",
    )
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    registry = build_registry(memory_dir)

    out = memory_dir / "registry.json"
    tmp = out.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    tmp.replace(out)

    print(f"Built registry: {registry['count']} entities at {out}")
    print(f"  Types: {dict((t, len(v)) for t, v in registry['by_type'].items())}")

    if args.check:
        # The orphan check is advisory. A failure here must not undo the registry
        # that was just written successfully, so swallow any error and report it.
        try:
            print_orphan_report(memory_dir)
        except Exception as exc:
            print(f"\nORPHAN CHECK: skipped ({exc}) — registry was still built.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
