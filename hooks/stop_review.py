#!/usr/bin/env python3
"""Stop hook: review the last assistant response for named entities not in canon.

Fires after the assistant finishes a response. Reads the transcript, scans the
last assistant message for capitalized-name patterns, cross-references with the
campaign registry, and emits a system reminder if any names are unrecognized.

This is reactive — the response is already sent — but it surfaces the issue
*before the next turn* so corrections happen quickly rather than compounding.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))
from common import find_campaign_dir  # noqa: E402


def find_memory_dir(cwd: Path) -> Path | None:
    """The campaign for this session's CWD, else this project's auto-memory."""
    campaign = find_campaign_dir(cwd)
    if campaign is not None:
        return campaign

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


def normalize(name: str) -> str:
    return re.sub(r"[-_\s]+", " ", name.strip().lower())


def load_ignore(memory_dir: Path) -> set[str]:
    """Per-campaign suppression list for vocabulary that is capitalized but is not
    an entity — rules terms (skill names, DC bands), the currency, headers.

    Lives with the campaign rather than in COMMON_NON_NAMES because it is
    campaign-specific: one campaign's rules term is another's NPC. Two sources,
    merged:
    - `ignore_names: Stealth, Perception, ...` lines in the campaign's
      RPG_CAMPAIGN.md (comma-separated; the line may repeat).
    - canon_ignore.txt, one entry per line, '#' starts a comment.
    Matching is case- and separator-insensitive.
    """
    names: set[str] = set()
    marker = memory_dir / "RPG_CAMPAIGN.md"
    if marker.exists():
        for line in marker.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*(?:-\s+)?ignore[ _-]?names\s*:\s*(.*)$",
                         re.sub(r"[*`]", "", line), re.IGNORECASE)
            if m:
                names.update(normalize(n) for n in m.group(1).split(",") if n.strip())
    path = memory_dir / "canon_ignore.txt"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                names.add(normalize(line))
    return names


# Near-miss spelling of a registered name ("Tallows", "Merrins") is the same
# entity, not an invention; below this ratio names are genuinely different
# ("Hallow" vs "Tallow" scores 0.83).
FUZZY_MATCH_RATIO = 0.85


def _contains_words(outer: tuple[str, ...], inner: tuple[str, ...]) -> bool:
    n = len(inner)
    return any(outer[i:i + n] == inner for i in range(len(outer) - n + 1))


def is_canon_name(name: str, registry: dict) -> bool:
    """Check whether a candidate name resolves against registry names or aliases.

    Beyond exact hits, a candidate resolves when its words appear as a
    contiguous run inside a registered name ("Sallow Street" in "Sallow Street
    house") or a registered name's words appear inside it (honorifics and
    heritage suffixes: "Lady Merrin", "Name-vor"), or when it is a near-miss
    spelling of one.
    """
    if not registry:
        return False
    key = normalize(name)
    known = set(registry["entities"]) | set(registry["by_alias"])
    if key in known:
        return True
    words = tuple(key.split())
    for k in known:
        k_words = tuple(k.split())
        if _contains_words(k_words, words) or _contains_words(words, k_words):
            return True
        if difflib.SequenceMatcher(None, key, k).ratio() >= FUZZY_MATCH_RATIO:
            return True
    return False


RPG_COMMAND = "<command-name>/rpg</command-name>"


# Common English words that look like names but aren't. Used to suppress false positives.
# Campaign-specific vocabulary must NOT be added here — it belongs in the registry
# (as entities or aliases), which is per-campaign.
COMMON_NON_NAMES = {
    # Pronouns + articles
    "I", "The", "A", "An", "He", "She", "They", "We", "You", "It", "His", "Her", "Their", "My", "Your",
    # Conjunctions / sentence-starters
    "Yes", "No", "OK", "Of", "And", "Or", "But", "If", "When", "Then", "So", "Also", "Only", "Even", "Yet", "Still",
    "Across", "Through", "After", "Before", "During", "While", "Despite", "Although", "Though",
    "Above", "Below", "Beyond", "Between", "Behind", "Beside", "Within", "Without",
    "Both", "Either", "Neither", "Each", "Every", "Some", "Most", "Many", "Few", "All",
    "First", "Second", "Third", "Last", "Next",
    "Now", "Soon", "Later", "Often", "Always", "Sometimes", "Never", "Once", "Twice",
    "There", "Here", "Where", "How", "Why", "What", "Who", "Which",
    "Just", "Quite", "Very", "Rather", "Really", "Truly", "Indeed",
    "Take", "Make", "Have", "Has", "Had", "Do", "Does", "Did", "Be", "Is", "Are", "Was", "Were",
    "Tell", "Say", "Said", "Go", "Goes", "Went", "Come", "Came", "Look", "Looked",
    "Up", "Down", "Out", "In", "On", "Off", "Over", "Under",
    "Time", "Day", "Week", "Month", "Year", "Hour", "Minute",
    # Titles
    "Mr", "Mrs", "Ms", "Sir", "Dr", "Captain", "Father", "Mother", "Brother", "Sister",
}


def _strip_non_narration(text: str) -> str:
    """Remove text regions that can't contain narrated entities: code blocks,
    inline code, markdown link targets, file paths, and URLs."""
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"\]\([^)]*\)", "] ", text)  # markdown link targets
    # Paths and URLs only — NOT every token containing a slash. A blanket slash
    # rule also eats ordinary prose ("cr/day", "and/or", "24/7") together with
    # the sentence-ending punctuation in front of it, which makes the NEXT
    # sentence's opening capital look mid-sentence and flags it as a name.
    text = re.sub(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+", " ", text)  # URLs
    text = re.sub(r"\S*\\\S*", " ", text)                          # Windows paths
    text = re.sub(r"(?<![\w.])\.{0,2}/\S+", " ", text)             # /abs ./rel ../rel
    text = re.sub(r"\S+/\S+/\S+", " ", text)                       # multi-segment paths
    return text


def extract_candidate_names(text: str) -> list[str]:
    """Extract capitalized words that look like proper names.

    A candidate only counts if it appears capitalized at least once
    MID-SENTENCE — sentence-initial, heading, bullet, and quote-opening
    capitals are ordinary English, and counting them buries real findings
    in noise whenever the response contains prose.
    """
    text = _strip_non_narration(text)
    candidates = set()

    pattern = re.compile(r"\b([A-Z][a-z]+(?:[-' ][A-Z][a-zA-Z]+)*)\b")
    for match in pattern.finditer(text):
        name = match.group(1)
        if len(name) < 3:
            continue
        first_word = name.split(" ")[0].split("-")[0]
        if first_word in COMMON_NON_NAMES:
            continue
        # Mid-sentence check: what precedes the match must be ordinary
        # running prose on the SAME line — a sentence boundary, heading,
        # bullet, quote-opening, table-cell boundary, or line start all mean
        # ordinary English capitalization, not a proper name.
        #
        # '|' is in the set because a markdown table cell begins a fresh
        # capitalization context exactly like a bullet does. Without it every
        # cell-initial word ("| Route |", "| Work the terminals") reads as an
        # entity, and a response containing one option table buries any real
        # finding under a dozen ordinary verbs.
        line_prefix = text[: match.start()].rsplit("\n", 1)[-1].strip()
        if not line_prefix or line_prefix[-1] in '.!?:;#*->|—–"“‘([':
            continue
        candidates.add(name)

    return sorted(candidates)


def session_booted_rpg(transcript_path: Path) -> bool:
    """True when this session invoked the rpg skill, by tool call or typed /rpg.

    A campaign pointer near the CWD only says a campaign EXISTS there; it says
    nothing about what this chat is for. Without this gate every unrelated chat
    opened under that directory gets its product and library names flagged as
    unregistered entities on every turn.
    """
    if not transcript_path.exists():
        return False
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            if "rpg" not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            role = entry.get("type")
            content = entry.get("message", {}).get("content", [])
            if isinstance(content, str):
                content = [{"type": "text", "text": content}]
            for block in content:
                if not isinstance(block, dict):
                    continue
                if role == "assistant" and block.get("type") == "tool_use":
                    if block.get("name") == "Skill" and block.get("input", {}).get("skill") == "rpg":
                        return True
                if role == "user" and block.get("type") == "text":
                    # At the start only: a compaction summary that merely quotes
                    # the tag mid-text re-armed the hook in a non-RPG chat.
                    if block.get("text", "").lstrip().startswith(RPG_COMMAND):
                        return True
    return False


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

    # No campaign canon on file (only feedback/user/reference entries) means
    # there is no narration to guard — every flag would be meta-conversation
    # noise. Stay silent until a campaign actually has entities.
    has_canon = any(
        ent.get("file", "").startswith(("project_", "entity_"))
        for ent in registry.get("entities", {}).values()
    )
    if not has_canon:
        print(json.dumps({}))
        return 0

    if not transcript_path_str:
        print(json.dumps({}))
        return 0

    transcript = Path(transcript_path_str)
    if not session_booted_rpg(transcript):
        print(json.dumps({}))
        return 0

    last_msg = read_last_assistant_message(transcript)
    if not last_msg:
        print(json.dumps({}))
        return 0

    ignore = load_ignore(memory_dir)
    candidates = extract_candidate_names(last_msg)
    unrecognized = [
        n for n in candidates
        if normalize(n) not in ignore
        and not is_canon_name(n, registry)
    ]

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
