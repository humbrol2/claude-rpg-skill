"""Tests for the campaign tools: ledger, tracker, dice, scene context."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent


def run(tool: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / tool), *args],
                          capture_output=True, text=True, cwd=cwd)


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = Path(self._tmp.name)
        (self.mem / "economy").mkdir()
        (self.mem / "economy" / "ledger.json").write_text(json.dumps({
            "as_of_day": 5, "currency": "gp", "liquid": {"gp": 100},
            "monthly_inflows": [{"source": "rent", "amount": 30}, "free-text flow"],
            "history": [], "receivables": [{"from": "Mags", "amount": 140}],
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def ledger(self) -> dict:
        return json.loads((self.mem / "economy" / "ledger.json").read_text(encoding="utf-8"))

    def test_post_moves_liquid_and_appends_history_in_one_write(self) -> None:
        r = run("ledger.py", "--memory-dir", str(self.mem), "post", "--delta", "-40", "--note", "bribe")
        self.assertEqual(r.returncode, 0, r.stderr)
        led = self.ledger()
        self.assertEqual(led["liquid"]["gp"], 60)
        self.assertEqual(led["history"][-1]["note"], "bribe")
        self.assertEqual(led["history"][-1]["day"], 5)

    def test_tick_prorates_monthly_flows_and_advances_day(self) -> None:
        r = run("ledger.py", "--memory-dir", str(self.mem), "tick", "--days", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        led = self.ledger()
        self.assertEqual(led["as_of_day"], 8)
        self.assertEqual(led["liquid"]["gp"], 103)
        self.assertIn("free-text flow", r.stdout)

    def test_tick_refuses_more_than_the_seven_day_ceiling(self) -> None:
        r = run("ledger.py", "--memory-dir", str(self.mem), "tick", "--days", "9")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.ledger()["as_of_day"], 5)

    def test_show_preserves_and_prints_campaign_extension_keys(self) -> None:
        r = run("ledger.py", "--memory-dir", str(self.mem), "show")
        self.assertIn("receivables", r.stdout)
        self.assertIn("free-text flow", r.stdout)
        self.assertIn("receivables", self.ledger())


class TrackTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.mem = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def t(self, *args: str) -> subprocess.CompletedProcess:
        return run("track.py", "--memory-dir", str(self.mem), *args)

    def test_beat_bumps_named_threads_and_warns_on_unknown(self) -> None:
        self.t("thread-add", "--id", "a", "--title", "A thread", "--day", "1")
        r = self.t("beat", "--day", "8", "--type", "social", "--summary", "x", "--thread", "a", "--thread", "zz")
        self.assertIn("unknown thread id(s) ['zz']", r.stdout)
        threads = json.loads((self.mem / "sessions" / "threads.json").read_text(encoding="utf-8"))
        self.assertEqual(threads[0]["last_advanced_day"], 8)
        beats = json.loads((self.mem / "sessions" / "beat_log.json").read_text(encoding="utf-8"))
        self.assertEqual(len(beats), 1)

    def test_status_flags_stale_threads_and_monotony(self) -> None:
        self.t("thread-add", "--id", "old", "--title", "Old", "--day", "0")
        for day in (150, 151, 152):
            self.t("beat", "--day", str(day), "--type", "social", "--summary", "s")
        r = self.t("status")
        self.assertIn("STALE threads: 1", r.stdout)
        self.assertIn("VARIETY FLAG", r.stdout)

    def test_pressure_due_soon_surfaces_in_status(self) -> None:
        self.t("beat", "--day", "10", "--type", "combat", "--summary", "s")
        self.t("pressure-add", "--id", "rent", "--title", "Rent", "--urgency", "LOW", "--due", "20")
        self.assertIn("DUE SOON", self.t("status").stdout)
        self.t("pressure-resolve", "--id", "rent")
        self.assertNotIn("DUE SOON", self.t("status").stdout)


class RollTests(unittest.TestCase):
    def test_seeded_roll_is_reproducible_and_shows_dice(self) -> None:
        a = run("roll.py", "2d6+3", "--seed", "4").stdout
        b = run("roll.py", "2d6+3", "--seed", "4").stdout
        self.assertEqual(a, b)
        self.assertRegex(a, r"2d6\+3: \[\d, \d\] \+ 3 = \d+")

    def test_advantage_reports_dropped_die(self) -> None:
        self.assertIn("advantage; dropped", run("roll.py", "d20", "--adv", "--seed", "1").stdout)

    def test_bad_expression_is_an_error_not_a_roll(self) -> None:
        r = run("roll.py", "twenty")
        self.assertEqual(r.returncode, 2)
        self.assertIn("bad dice expression", r.stderr)


class SceneTests(unittest.TestCase):
    def test_scene_lists_files_that_mention_the_place_with_source_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            (mem / "MEMORY.md").write_text("# idx\n", encoding="utf-8")
            (mem / "project_rusty_nail.md").write_text(
                "---\nname: Rusty Nail\ndescription: a bar\ntype: project\naliases: [bar]\n---\n# Rusty Nail\n", encoding="utf-8")
            (mem / "entity_varla.md").write_text(
                "---\nname: Varla\ndescription: barkeep\ntype: project\nstatus: active\n---\n# Varla\nRuns the Rusty Nail.\n", encoding="utf-8")
            (mem / "entity_other.md").write_text(
                "---\nname: Other\ndescription: unrelated\ntype: project\n---\n# Other\nDrinks at a bar sometimes.\n", encoding="utf-8")
            r = run("canon_check.py", "Rusty Nail", "--scene", "--memory-dir", str(mem))
            self.assertIn("Varla (entity_varla.md)", r.stdout)
            self.assertIn('"Runs the Rusty Nail."', r.stdout)
            self.assertNotIn("Other", r.stdout, "short alias 'bar' must not anchor the scan")


if __name__ == "__main__":
    unittest.main()
