"""Bill of materials: LDraw-to-kit part mapping and kit inventory diff."""

from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from .ldraw import INHERIT_COLOR, part_id

Bom = Counter[tuple[str, int]]
# ldraw part id -> [(kit part, qty per ldraw part, color override or None)]
IdMap = dict[str, list[tuple[str, int, int | None]]]


@dataclass(frozen=True)
class Shortage:
    part: str
    color: int | None
    need: int
    have: int


def load_inventory(path: Path) -> Bom:
    """Read a kit inventory CSV with part_num,color_id,quantity columns. Blank-quantity rows are skipped."""
    inv: Bom = Counter()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["quantity"].strip():
                inv[(row["part_num"], int(row["color_id"]))] += int(row["quantity"])
    return inv


def load_unknown_parts(path: Path) -> set[str]:
    """Parts listed with a blank quantity: owned, count not known."""
    with path.open(newline="", encoding="utf-8") as f:
        return {row["part_num"] for row in csv.DictReader(f) if not row["quantity"].strip()}


def load_id_map(path: Path) -> IdMap:
    """Read ldraw_id,kit_part,qty,color rows; repeated ldraw_id rows expand to several kit parts."""
    m: IdMap = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            color = row.get("color", "").strip()
            m.setdefault(part_id(row["ldraw_id"]), []).append(
                (row["kit_part"].strip(), int(row["qty"]), int(color) if color else None)
            )
    return m


def to_kit_space(bom: Bom, id_map: IdMap) -> Bom:
    out: Bom = Counter()
    for (pid, color), n in bom.items():
        for kit_part, qty, override in id_map.get(pid, [(pid, 1, None)]):
            out[(kit_part, color if override is None else override)] += n * qty
    return out


def check(
    required: Bom, available: Bom, unknown: Collection[str] = frozenset()
) -> tuple[list[Shortage], list[Shortage]]:
    """Return (part-level shortages, color-level shortages for parts whose total suffices).

    Parts in `unknown` have no known count and are never reported.
    """
    need_by_part: Counter[str] = Counter()
    have_by_part: Counter[str] = Counter()
    for (p, _), n in required.items():
        need_by_part[p] += n
    for (p, _), n in available.items():
        have_by_part[p] += n

    errors = [
        Shortage(p, None, need, have_by_part[p])
        for p, need in sorted(need_by_part.items())
        if p not in unknown and need > have_by_part[p]
    ]
    short_parts = {s.part for s in errors}
    warnings = [
        Shortage(p, c, need, available[(p, c)])
        for (p, c), need in sorted(required.items())
        if p not in short_parts and p not in unknown and c != INHERIT_COLOR and need > available[(p, c)]
    ]
    return errors, warnings


def left(required: Bom, available: Bom) -> list[tuple[str, int, int, int, int]]:
    """(kit part, colour, have, used, left) for every part the kits hold or the model uses, in kit space."""
    keys = sorted(set(required) | {k for k, n in available.items() if n > 0})
    return [(p, c, available[(p, c)], required[(p, c)], available[(p, c)] - required[(p, c)]) for p, c in keys]
