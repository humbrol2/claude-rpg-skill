#!/usr/bin/env python3
"""Roll dice honestly. The narrator never generates a result in its head.

Usage: python roll.py <expr> [<expr> ...] [--adv | --dis] [--seed N]
  expr: standard dice notation — d20, 2d6+3, 1d100, 3d6-1, d20+5

Each expression prints its individual dice and the total. --adv / --dis
roll the first expression twice and keep the higher / lower (D&D 5e style).
Natural 1 / natural max on a single die are flagged for the narrator.
"""
from __future__ import annotations

import argparse
import random
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

_DICE_RE = re.compile(r"^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)


def parse(expr: str) -> tuple[int, int, int]:
    """'2d6+3' -> (count, sides, modifier). Count defaults to 1."""
    m = _DICE_RE.match(expr)
    if not m:
        raise ValueError(f"bad dice expression: {expr!r} (expected like d20, 2d6+3)")
    count = int(m.group(1) or 1)
    sides = int(m.group(2))
    mod = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    if count < 1 or count > 100 or sides < 2 or sides > 1000:
        raise ValueError(f"out of range: {expr!r}")
    return count, sides, mod


def roll_once(expr: str, rng: random.Random) -> tuple[list[int], int, str]:
    count, sides, mod = parse(expr)
    dice = [rng.randint(1, sides) for _ in range(count)]
    total = sum(dice) + mod
    flag = ""
    if count == 1:
        if dice[0] == 1:
            flag = "  NATURAL 1"
        elif dice[0] == sides:
            flag = f"  NATURAL {sides}"
    return dice, total, flag


def fmt(expr: str, dice: list[int], total: int, flag: str) -> str:
    _, _, mod = parse(expr)
    mod_s = f" {'+' if mod >= 0 else '-'} {abs(mod)}" if mod else ""
    return f"{expr.strip()}: [{', '.join(map(str, dice))}]{mod_s} = {total}{flag}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exprs", nargs="+", help="dice expressions, e.g. d20+5 2d6")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--adv", action="store_true", help="roll first expr twice, keep higher")
    g.add_argument("--dis", action="store_true", help="roll first expr twice, keep lower")
    ap.add_argument("--seed", type=int, default=None, help="reproducible rolls (tests only)")
    args = ap.parse_args()

    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    try:
        exprs = list(args.exprs)
        if args.adv or args.dis:
            first = exprs.pop(0)
            a = roll_once(first, rng)
            b = roll_once(first, rng)
            keep, drop = (max(a, b, key=lambda r: r[1]), min(a, b, key=lambda r: r[1]))
            if args.dis:
                keep, drop = drop, keep
            mode = "advantage" if args.adv else "disadvantage"
            print(f"{fmt(first, *keep)}   ({mode}; dropped {drop[1]})")
        for expr in exprs:
            print(fmt(expr, *roll_once(expr, rng)))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
