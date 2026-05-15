#!/usr/bin/env python3
"""Add a new memory entry. Creates the file and updates MEMORY.md index.

Usage: python save_memory.py --type project --name "Saen-Korr-Threll" --description "..." --body "..."
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import find_memory_dir


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text[:60]


def write_entry(memory_dir: Path, entry_type: str, name: str, description: str, body: str,
                extra_frontmatter: dict | None = None) -> Path:
    slug = slugify(name)
    filename = f"{entry_type}_{slug}.md"
    path = memory_dir / filename

    fm_lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        f"type: {entry_type}",
    ]
    if extra_frontmatter:
        for k, v in extra_frontmatter.items():
            if isinstance(v, list):
                fm_lines.append(f"{k}: [{', '.join(repr(x) for x in v)}]")
            else:
                fm_lines.append(f"{k}: {v}")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append(body)

    path.write_text("\n".join(fm_lines), encoding="utf-8")
    return path


def update_index(memory_dir: Path, filename: str, name: str, description: str) -> None:
    index_path = memory_dir / "MEMORY.md"
    line = f"- [{name}]({filename}) — {description}"

    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8")
        if f"]({filename})" in existing:
            # Already indexed; skip
            return
        if not existing.endswith("\n"):
            existing += "\n"
        existing += line + "\n"
        index_path.write_text(existing, encoding="utf-8")
    else:
        index_path.write_text(line + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["project", "feedback", "user", "reference"])
    ap.add_argument("--name", required=True)
    ap.add_argument("--description", required=True, help="One-line description for the index")
    ap.add_argument("--body", required=True, help="Main body content")
    ap.add_argument("--memory-dir", type=Path, default=None)
    args = ap.parse_args()

    memory_dir = args.memory_dir or find_memory_dir()
    path = write_entry(memory_dir, args.type, args.name, args.description, args.body)
    update_index(memory_dir, path.name, args.name, args.description)
    print(f"Saved memory: {path}")
    print(f"Indexed in MEMORY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
