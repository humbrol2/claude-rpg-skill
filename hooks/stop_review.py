#!/usr/bin/env python3
"""Stop hook: review the last assistant response for named entities not in canon.

Fires after the assistant finishes a response. Reads the transcript, scans the
last assistant message for capitalized-name patterns, cross-references with the
campaign registry, and emits a system reminder if any names are unrecognized.

This is reactive — the response is already sent — but it surfaces the issue
*before the next turn* so corrections happen quickly rather than compounding.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def find_memory_dir(cwd: Path) -> Path | None:
    """Same logic as session_start.py."""
    for ancestor in [cwd] + list(cwd.parents):
        if (ancestor / "RPG_CAMPAIGN.md").exists():
            for line in (ancestor / "RPG_CAMPAIGN.md").read_text(encoding="utf-8").splitlines():
                if ":" in line and "memory_dir" in line:
                    path_str = line.split(":", 1)[1].strip()
                    candidate = Path(path_str).expanduser()
                    if candidate.exists():
                        return candidate
        if (ancestor / "memory" / "MEMORY.md").exists():
            return ancestor / "memory"
        if ancestor == ancestor.parent:
            break

    home = Path.home() / ".claude" / "projects"
    if home.exists():
        cwd_marker = str(cwd).replace(":", "-").replace("\\", "-").replace("/", "-")
        for project_dir in home.iterdir():
            if not project_dir.is_dir():
                continue
            if cwd_marker.lower() in project_dir.name.lower():
                mem = project_dir / "memory"
                if (mem / "MEMORY.md").exists():
                    return mem
    return None


def load_registry(memory_dir: Path) -> dict | None:
    path = memory_dir / "registry.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def strip_heritage_suffix(name: str) -> str:
    """Drakari suffix-strip: e.g. Aren-Vor → Aren."""
    lower = name.lower()
    for suffix in ["-vor-korr-threll", "-vor-korr", "-vor", "-korr-threll", "-korr",
                   "-threll", "-saen", "-vellith", "-daresh", "-khorr"]:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return name


def is_canon_name(name: str, registry: dict) -> bool:
    """Check whether a candidate name resolves in the registry."""
    if not registry:
        return False
    key = name.lower()
    if key in registry["entities"]:
        return True
    if key in registry["by_alias"]:
        return True
    bare = strip_heritage_suffix(name).lower()
    if bare != key:
        if bare in registry["entities"]:
            return True
        if bare in registry["by_alias"]:
            return True
    # Substring fallback — match if name is contained in any entity name
    for k in registry["entities"]:
        if bare in k or k in bare:
            return True
    return False


# Common English words that look like names but aren't. Used to suppress false positives.
COMMON_NON_NAMES = {
    # Pronouns + articles
    "I", "The", "A", "An", "He", "She", "They", "We", "You", "It", "His", "Her", "Their", "My", "Your",
    # Conjunctions / sentence-starters
    "Yes", "No", "OK", "Of", "And", "Or", "But", "If", "When", "Then", "So", "Also", "Only", "Even", "Yet", "Still",
    "Across", "Through", "After", "Before", "During", "While", "Despite", "Although", "Though",
    "Above", "Below", "Beyond", "Between", "Behind", "Beside", "Within", "Without",
    "Both", "Either", "Neither", "Each", "Every", "Some", "Most", "Many", "Few", "All",
    "First", "Second", "Third", "Last", "Next", "Last",
    "Now", "Soon", "Later", "Often", "Always", "Sometimes", "Never", "Once", "Twice",
    "There", "Here", "Where", "How", "Why", "What", "Who", "Which",
    "Just", "Quite", "Very", "Rather", "Really", "Truly", "Indeed",
    "Take", "Make", "Have", "Has", "Had", "Do", "Does", "Did", "Be", "Is", "Are", "Was", "Were",
    "Tell", "Say", "Said", "Go", "Goes", "Went", "Come", "Came", "Look", "Looked",
    "Up", "Down", "Out", "In", "On", "Off", "Over", "Under",
    "Time", "Day", "Week", "Month", "Year",
    # Setting / species (always-known background)
    "Lilim", "Drakari", "Aetheran", "Verse",
    # Setting locations + venues (common references)
    "Hadlea", "Lockwell", "Tellurian", "Vethrin", "Confluence", "Throne", "Closure",
    "Slow", "Lamp", "Glass", "Reach", "Sourcefall", "Threlling", "Kethra",
    # Mechanical / structural
    "Mark", "Domain", "Sig", "Phase", "Cycle", "ASC", "Day", "Hour", "Minute",
    # Titles
    "Mr", "Mrs", "Ms", "Sir", "Dr", "Captain", "Father", "Mother", "Brother", "Sister",
}


def extract_candidate_names(text: str) -> list[str]:
    """Extract capitalized words that look like proper names.

    Patterns matched:
    - Capitalized single words at sentence-start or mid-sentence (most common)
    - Hyphenated names (Saen-Daresh, Korr-Threll-Vor, etc.)
    - Two-word names (Sennit Vethrin-Saen)
    """
    candidates = set()

    # Match capitalized words including hyphens and trailing-suffix patterns
    # Limit to mid-sentence positions to reduce false positives from sentence starts
    pattern = re.compile(r"\b([A-Z][a-z]+(?:[-' ][A-Z][a-zA-Z]+)*)\b")
    for match in pattern.finditer(text):
        name = match.group(1)
        # Skip very short
        if len(name) < 3:
            continue
        # Skip common non-names
        first_word = name.split(" ")[0].split("-")[0]
        if first_word in COMMON_NON_NAMES:
            continue
        candidates.add(name)

    return sorted(candidates)


def read_last_assistant_message(transcript_path: Path) -> str:
    """Read the last assistant message text from a Claude Code transcript .jsonl."""
    if not transcript_path.exists():
        return ""
    last_msg = ""
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "assistant":
                msg = entry.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            last_msg = block.get("text", "")
                elif isinstance(content, str):
                    last_msg = content
    return last_msg


def main() -> int:
    # Read hook input from stdin (Claude Code passes JSON envelope)
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    transcript_path_str = hook_input.get("transcript_path", "")
    cwd_str = hook_input.get("cwd", str(Path.cwd()))
    cwd = Path(cwd_str)

    memory_dir = find_memory_dir(cwd)
    if memory_dir is None:
        # Not in an RPG context — emit nothing
        print(json.dumps({}))
        return 0

    registry = load_registry(memory_dir)
    if registry is None:
        print(json.dumps({}))
        return 0

    if not transcript_path_str:
        print(json.dumps({}))
        return 0

    transcript = Path(transcript_path_str)
    last_msg = read_last_assistant_message(transcript)
    if not last_msg:
        print(json.dumps({}))
        return 0

    candidates = extract_candidate_names(last_msg)
    unrecognized = [n for n in candidates if not is_canon_name(n, registry)]

    if not unrecognized:
        # All names resolved cleanly
        print(json.dumps({}))
        return 0

    # Surface unrecognized names as a system reminder for next turn
    msg_lines = [
        "**RPG canon-check (Stop hook):** The previous response referenced the following names that are NOT in the campaign registry:",
        "",
    ]
    for name in unrecognized[:20]:  # cap at 20 to avoid bloat
        msg_lines.append(f"  - {name}")
    if len(unrecognized) > 20:
        msg_lines.append(f"  ... and {len(unrecognized) - 20} more.")
    msg_lines.append("")
    msg_lines.append(
        "**Action required next turn:** For each unrecognized name, either "
        "(a) confirm with the user that this is a new entity and save to memory via "
        "`save_memory.py`, or (b) correct/retract if it was invented. Do NOT silently re-use."
    )

    envelope = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": "\n".join(msg_lines),
        }
    }
    print(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
