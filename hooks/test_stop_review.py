"""Tests for the Stop hook's session gate: the canon check must only run in
sessions that actually booted the RPG skill, not in every chat opened under a
directory that happens to contain a campaign pointer."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "stop_review.py"

NARRATION = "The door opened and Zorblax Quillfeather walked in beside Freya."


def assistant_text(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


def skill_call(skill: str) -> dict:
    return {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "Skill", "input": {"skill": skill}}]},
    }


def slash_command(name: str) -> dict:
    return {"type": "user", "message": {"content": f"<command-name>/{name}</command-name>"}}


class StopHookSessionGate(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        memory = self.root / "memory"
        memory.mkdir()
        (memory / "MEMORY.md").write_text("# Canon\n", encoding="utf-8")
        registry = {"entities": {"freya": {"file": "project_freya.md"}}, "by_alias": {}}
        (memory / "registry.json").write_text(json.dumps(registry), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_hook(self, entries: list[dict]) -> dict:
        transcript = self.root / "transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
        hook_input = json.dumps({"transcript_path": str(transcript), "cwd": str(self.root)})
        result = subprocess.run(
            [sys.executable, str(HOOK)], input=hook_input, capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)

    def test_stays_silent_when_session_never_booted_the_rpg_skill(self) -> None:
        output = self.run_hook([assistant_text(NARRATION)])
        self.assertEqual(output, {})

    def test_stays_silent_when_only_another_skill_was_invoked(self) -> None:
        output = self.run_hook([skill_call("superpowers:brainstorming"), assistant_text(NARRATION)])
        self.assertEqual(output, {})

    def test_flags_unknown_names_after_rpg_skill_tool_call(self) -> None:
        output = self.run_hook([skill_call("rpg"), assistant_text(NARRATION)])
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Zorblax Quillfeather", context)
        self.assertNotIn("Freya", context)

    def test_flags_unknown_names_after_typed_rpg_command(self) -> None:
        output = self.run_hook([slash_command("rpg"), assistant_text(NARRATION)])
        self.assertIn("Zorblax Quillfeather", output["hookSpecificOutput"]["additionalContext"])

    def test_assistant_quoting_the_command_text_does_not_boot_rpg(self) -> None:
        quoted = assistant_text("Type <command-name>/rpg</command-name> to begin.")
        output = self.run_hook([quoted, assistant_text(NARRATION)])
        self.assertEqual(output, {})


def write_campaign(directory: Path, marker: str, entities: dict, by_alias: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "RPG_CAMPAIGN.md").write_text(marker, encoding="utf-8")
    (directory / "MEMORY.md").write_text("# Canon\n", encoding="utf-8")
    registry = {"entities": entities, "by_alias": by_alias}
    (directory / "registry.json").write_text(json.dumps(registry), encoding="utf-8")


class StopHookCampaignResolution(unittest.TestCase):
    """A campaign folder nested under a directory whose pointer names a
    different campaign must check against its own registry."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        other = self.root / "other-campaign"
        write_campaign(other, "# Other\n", {"voss": {"file": "entity_voss.md"}}, {})
        (self.root / "RPG_CAMPAIGN.md").write_text(f"memory_dir: {other}\n", encoding="utf-8")
        self.nested = self.root / "nested"
        write_campaign(
            self.nested,
            f"# Nested\nMemory directory: {self.nested} (this folder). Index: MEMORY.md.\n"
            "ignore_names: Stealth, Sleight, Hand, Perception, Deception\n",
            {
                "tallow": {"file": "entity_tallow.md"},
                "sallow street house": {"file": "project_sallow_street_house.md"},
                "humbrol": {"file": "project_pc.md"},
            },
            {"hum": "humbrol"},
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_hook(self, text: str, cwd: Path) -> dict:
        transcript = self.root / "transcript.jsonl"
        entries = [skill_call("rpg"), assistant_text(text)]
        transcript.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
        hook_input = json.dumps({"transcript_path": str(transcript), "cwd": str(cwd)})
        result = subprocess.run(
            [sys.executable, str(HOOK)], input=hook_input, capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)

    def test_nested_campaign_resolves_to_itself_not_parent_pointer(self) -> None:
        output = self.run_hook("The door opened and Tallow walked out onto Sallow Street.", self.nested)
        self.assertEqual(output, {})

    def test_subdirectory_of_nested_campaign_still_resolves_to_it(self) -> None:
        sub = self.nested / "sessions"
        sub.mkdir()
        output = self.run_hook("The door opened and Tallow nodded.", sub)
        self.assertEqual(output, {})

    def test_parent_directory_still_resolves_to_parent_pointer(self) -> None:
        output = self.run_hook("The door opened and Tallow nodded to Voss.", self.root)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Tallow", context)
        self.assertNotIn("Voss", context)

    def test_ignore_names_suppress_rules_terms(self) -> None:
        output = self.run_hook(
            "You roll Stealth, then Sleight of Hand, then Perception and Deception.", self.nested
        )
        self.assertEqual(output, {})

    def test_near_miss_spelling_resolves(self) -> None:
        output = self.run_hook("The door opened and the Tallows came in.", self.nested)
        self.assertEqual(output, {})

    def test_unknown_name_is_still_flagged_in_nested_campaign(self) -> None:
        output = self.run_hook("The door opened and Tallow nodded to Voss.", self.nested)
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Voss", context)
        self.assertNotIn("Tallow", context)


if __name__ == "__main__":
    unittest.main()
