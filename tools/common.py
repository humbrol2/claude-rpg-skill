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


def find_memory_dir(start: Optional[Path] = None) -> Path:
    """Locate the campaign memory directory.

    Order of resolution:
    1. RPG_CAMPAIGN.md in CWD pointing to a memory_dir.
    2. ./memory if it has MEMORY.md.
    3. ~/.claude/projects/*/memory/ (search; if multiple, latest mtime wins).
    4. Fall back to creating ./memory in CWD.
    """
    start = start or Path.cwd()

    campaign_marker = start / "RPG_CAMPAIGN.md"
    if campaign_marker.exists():
        for line in campaign_marker.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*memory_dir\s*:\s*(.+)\s*$", line)
            if m:
                path = Path(m.group(1).strip()).expanduser()
                if path.exists():
                    return path

    cwd_memory = start / "memory"
    if (cwd_memory / "MEMORY.md").exists():
        return cwd_memory

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
