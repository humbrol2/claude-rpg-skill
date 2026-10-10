"""Shared helpers for the rpg skill tools."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Force UTF-8 stdout/stderr so unicode characters (arrows, em-dashes) don't break
# on Windows consoles defaulting to cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


# Pointer lines are hand-written, so the key comes in several spellings:
# "memory_dir: X", "Memory directory: X (this folder)", "**Memory dir:** X".
_POINTER_RE = re.compile(r"^\s*(?:-\s+)?memory[ _-]?dir(?:ectory)?\s*:\s*(.+?)\s*$", re.IGNORECASE)


def _pointer_target(marker: Path) -> Optional[Path]:
    """The existing directory an RPG_CAMPAIGN.md points at, or None.

    The value may trail prose ("D:\\AI\\helluva (this folder). Index: ..."), so
    the longest leading run of words that names an existing directory wins.
    Relative paths resolve against the marker's own directory.
    """
    for line in marker.read_text(encoding="utf-8").splitlines():
        m = _POINTER_RE.match(re.sub(r"[*`]", "", line))
        if not m:
            continue
        words = m.group(1).split()
        for n in range(len(words), 0, -1):
            raw = " ".join(words[:n]).rstrip(".,;:)")
            if not raw:
                continue
            path = Path(raw).expanduser()
            if not path.is_absolute():
                path = marker.parent / path
            if path.is_dir():
                return path
    return None


def find_campaign_dir(start: Path) -> Optional[Path]:
    """The campaign memory directory for `start`, walking up to the drive root.

    The nearest ancestor that names a campaign wins, so a campaign folder
    nested under a directory holding a different campaign's pointer resolves
    to itself, not to its parent's campaign. At each level:
    1. RPG_CAMPAIGN.md pointing at a memory directory.
    2. RPG_CAMPAIGN.md with no usable pointer, beside a MEMORY.md — the
       campaign lives right here.
    3. memory/MEMORY.md.
    """
    for ancestor in [start] + list(start.parents):
        marker = ancestor / "RPG_CAMPAIGN.md"
        if marker.exists():
            target = _pointer_target(marker)
            if target is not None:
                return target
            if (ancestor / "MEMORY.md").exists():
                return ancestor
        if (ancestor / "memory" / "MEMORY.md").exists():
            return ancestor / "memory"
    return None


def find_memory_dir(start: Optional[Path] = None) -> Path:
    """Locate the campaign memory directory.

    Order of resolution:
    1. find_campaign_dir — nearest campaign pointer or memory/ walking up from CWD.
    2. ~/.claude/projects/*/memory/ (search; if multiple, latest mtime wins).
    3. Fall back to creating ./memory in CWD.
    """
    start = start or Path.cwd()

    campaign = find_campaign_dir(start)
    if campaign is not None:
        return campaign

    cwd_memory = start / "memory"

    home = Path.home() / ".claude" / "projects"
    if home.exists():
        candidates = []
        for project_dir in home.iterdir():
            if not project_dir.is_dir():
                continue
            mem = project_dir / "memory"
            if (mem / "MEMORY.md").exists():
                candidates.append((mem.stat().st_mtime, mem))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    # Last resort: create cwd/memory
    cwd_memory.mkdir(parents=True, exist_ok=True)
    return cwd_memory


def load_ledger(memory_dir: Path) -> dict:
    """Load the ledger from memory_dir/economy/ledger.json. Empty if missing."""
    path = memory_dir / "economy" / "ledger.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ledger(memory_dir: Path, ledger: dict) -> None:
    """Save the ledger atomically."""
    econ_dir = memory_dir / "economy"
    econ_dir.mkdir(parents=True, exist_ok=True)
    path = econ_dir / "ledger.json"
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a memory file's YAML frontmatter, returning (frontmatter_dict, body).

    Minimal YAML parsing — handles the simple key:value lines our memory files use.
    Lists rendered as 'key: [a, b, c]' inline. Multi-line values not supported.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")

    fm: dict = {}
    for line in fm_block.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip()
        # Handle inline lists
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
            fm[key] = items
        else:
            fm[key] = val.strip('"').strip("'")

    # Harness-written memory files nest type under a metadata: block
    # (metadata:\n  type: feedback). Surface it as a top-level key.
    if "type" not in fm or fm.get("type") == "":
        m = re.search(r"^[ \t]+type[ \t]*:[ \t]*(\S+)[ \t]*$", fm_block, re.MULTILINE)
        if m:
            fm["type"] = m.group(1).strip('"').strip("'")

    # Aliases get relocated under metadata: by the same linter. Left unhandled
    # this silently empties by_alias, so every "the mate" / "the foreman"
    # reference fails to resolve and gets reported as uncatalogued canon.
    #
    # The horizontal-whitespace classes below are load-bearing. With `\s*` the
    # match runs across the newline whenever the linter leaves a trailing space
    # after `aliases:` — `\s*` eats " \n    " and `(.*)$` then captures the
    # FIRST list item as if it were an inline value. The block scan resumes
    # after it, so alias #1 is silently dropped from every block-list file.
    # That is invisible in the registry and shows up only as the first alias of
    # each file being reported as uncatalogued canon, forever.
    if not fm.get("aliases"):
        m = re.search(r"^[ \t]+aliases[ \t]*:[ \t]*(.*)$", fm_block, re.MULTILINE)
        if m:
            inline = m.group(1).strip()
            if inline.startswith("[") and inline.endswith("]"):
                fm["aliases"] = [a.strip().strip('"').strip("'")
                                 for a in inline[1:-1].split(",") if a.strip()]
            else:
                items = []
                if inline and not inline.startswith("-"):
                    items.append(inline.strip('"').strip("'"))
                for line in fm_block[m.end():].splitlines():
                    stripped = line.strip()
                    if stripped.startswith("- "):
                        items.append(stripped[2:].strip().strip('"').strip("'"))
                    elif stripped:
                        break
                if items:
                    fm["aliases"] = items
    return fm, body


def list_memory_files(memory_dir: Path) -> list[Path]:
    """List all *.md files in memory_dir except MEMORY.md."""
    return sorted(p for p in memory_dir.glob("*.md") if p.name != "MEMORY.md")


def fmt_money(amount: float, currency: str = "M_cr") -> str:
    """Format a money value. Defaults to M_cr (millions of credits)."""
    if currency == "M_cr":
        if abs(amount) >= 1:
            return f"${amount:.2f}M"
        else:
            return f"${amount * 1000:.0f}K"
    return f"{amount} {currency}"
