"""Measure LDraw parts and models before placing or reviewing them. Standard library only.

    uv run python scripts/ldraw_measure.py bbox PART...       bounding box of each part
    uv run python scripts/ldraw_measure.py holes PART         pin/axle hole positions and axes
    uv run python scripts/ldraw_measure.py slice PART AXIS LO HI   bounding box of the geometry between LO and HI
    uv run python scripts/ldraw_measure.py overlap SLUG       placed parts whose boxes intersect
    uv run python scripts/ldraw_measure.py pins SLUG          pins and axles that share a hole

Parts are looked up in ldraw/ and custom/. `overlap` compares axis-aligned boxes, so it reports
candidates to look at, not proven collisions. Use `slice` on the larger part to see whether its
geometry really reaches the other one. Pins, axles and bushes are skipped because they sit inside
other parts on purpose, and so are pairs that mesh (tread on sprocket). `pins` reports two pins or
axles on the same line whose lengths overlap, which means both are drawn in one hole.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOTS = (ROOT / "ldraw", ROOT / "custom")
# Primitives whose local Y axis is the axis of a hole or a pin.
HOLES = ("peghole", "axlehol", "axl3hole", "connhole", "beamhole", "npeghol")
# Parts that are meant to sit inside other parts.
CONNECTORS = {"61332", "6558", "3673", "3749", "43093", "11214", "18651", "32054", "4274", "3713", "32123b",
              "32062", "4519", "3705", "32073", "3706", "44294", "3707", "60485", "3708", "87083"}
# Connectors that sit on an axle rather than in a hole.
BUSHES = {"3713", "32123b"}
# Pairs that mesh by design and always intersect as boxes.
MESHING = {frozenset(("57518", "57519")), frozenset(("57518",))}  # tread on sprocket, tread link on its neighbour
Matrix = tuple[tuple[float, float, float], ...]
IDENTITY: Matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def find(name: str) -> Path | None:
    name = name.strip().replace("\\", "/").lower()
    for root in ROOTS:
        for folder in ("parts", "p", ""):
            path = root / folder / name
            if path.is_file():
                return path
    return None


def apply(m: Matrix, t: tuple[float, float, float], v: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] + t[i] for i in range(3))


def compose(m: Matrix, n: Matrix) -> Matrix:
    return tuple(tuple(sum(m[i][k] * n[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def refs(text: str):
    """(position, matrix, file name) of every type 1 line."""
    for line in text.splitlines():
        t = line.split(None, 14)
        if len(t) == 15 and t[0] == "1":
            v = [float(x) for x in t[2:14]]
            yield tuple(v[:3]), (tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12])), t[14].strip()


@functools.lru_cache(maxsize=None)
def points(name: str) -> tuple[tuple[float, float, float], ...]:
    path = find(name)
    if path is None:
        return ()
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for pos, m, child in refs(text):
        out += [apply(m, pos, p) for p in points(child)]
    for line in text.splitlines():
        t = line.split()
        if t and t[0] in ("3", "4"):
            v = [float(x) for x in t[2:]]
            out += [tuple(v[i:i + 3]) for i in range(0, len(v) - 2, 3)]
    return tuple(out)


def box(pts) -> tuple[list[float], list[float]]:
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def fmt(lo: list[float], hi: list[float]) -> str:
    return " ".join(f"{a}[{lo[i]:.0f},{hi[i]:.0f}]" for i, a in enumerate("XYZ"))


def cmd_bbox(parts: list[str]) -> None:
    for part in parts:
        pts = points(part + ".dat")
        print(f"{part:14}", fmt(*box(pts)) if pts else "not found")


def cmd_slice(part: str, axis: str, lo: str, hi: str) -> None:
    i = "XYZ".index(axis.upper())
    pts = [p for p in points(part + ".dat") if float(lo) <= p[i] <= float(hi)]
    print(fmt(*box(pts)) if pts else "no geometry in that range")


def cmd_holes(part: str) -> None:
    found: dict[tuple, set[str]] = {}

    def walk(name: str, m: Matrix, t: tuple[float, float, float]) -> None:
        path = find(name)
        if path is None:
            return
        for pos, n, child in refs(path.read_text(encoding="utf-8", errors="replace")):
            world, at = compose(m, n), apply(m, t, pos)
            base = child.replace("\\", "/").lower().rsplit("/", 1)[-1]
            if base.startswith(HOLES):
                axis = [abs(world[i][1]) for i in range(3)]
                found.setdefault((tuple(round(c, 1) for c in at), "XYZ"[axis.index(max(axis))]), set()).add(base)
            else:
                walk(child, world, at)

    walk(part + ".dat", IDENTITY, (0, 0, 0))
    for (at, axis), names in sorted(found.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"axis {axis}  at {at}  {', '.join(sorted(names))}")


def placed_parts(slug: str):
    """(path, part, matrix, position) of every part in the model, submodels flattened."""
    text = (ROOT / "models" / slug / "model.mpd").read_text(encoding="utf-8")
    blocks: dict[str, str] = {}
    name = None
    for line in text.splitlines():
        t = line.split(None, 2)
        if t[:2] == ["0", "FILE"]:
            name = t[2].strip().lower()
            blocks[name] = ""
        elif name:
            blocks[name] += line + "\n"

    def walk(sub: str, m: Matrix, t: tuple[float, float, float], path: str):
        for k, (pos, n, child) in enumerate(refs(blocks[sub])):
            world, at, key = compose(m, n), apply(m, t, pos), child.lower()
            if key in blocks:
                yield from walk(key, world, at, f"{path}{key}#{k}/")
            else:
                yield f"{path}{key.removesuffix('.dat')}#{k}", key, world, at

    yield from walk(next(iter(blocks)), IDENTITY, (0, 0, 0), "")


def cmd_overlap(slug: str, tolerance: float = 2.0) -> None:
    placed = []
    for label, key, world, at in placed_parts(slug):
        part = key.removesuffix(".dat")
        pts = points(key)
        if part in CONNECTORS or not pts:
            continue
        placed.append((label, None, part, box([apply(world, at, p) for p in pts])))
    hits = 0
    for i, (a, pa, ka, (alo, ahi)) in enumerate(placed):
        for b, pb, kb, (blo, bhi) in placed[i + 1:]:
            if frozenset((ka, kb)) in MESHING:
                continue
            depth = [min(ahi[k], bhi[k]) - max(alo[k], blo[k]) for k in range(3)]
            if min(depth) > tolerance:
                hits += 1
                print(f"{a}  x  {b}  overlap " + " ".join(f"{ax}{d:.0f}" for ax, d in zip("XYZ", depth)))
    print(f"{hits} candidate overlap(s) deeper than {tolerance:g} LDU among {len(placed)} parts")


def cmd_pins(slug: str, tolerance: float = 1.0) -> None:
    lines: dict[tuple, list] = {}
    for label, key, world, at in placed_parts(slug):
        part = key.removesuffix(".dat")
        pts = points(key)
        if part not in CONNECTORS or part in BUSHES or not pts:
            continue
        axis = [abs(world[i][0]) for i in range(3)]  # pins and axles are modelled along local X
        i = axis.index(max(axis))
        lo, hi = box(pts)
        ends = sorted(at[i] + world[i][0] * x for x in (lo[0], hi[0]))
        line = (i, *(round(at[k]) for k in range(3) if k != i))
        lines.setdefault(line, []).append((ends, label))
    hits = 0
    for (i, *rest), segs in lines.items():
        for j, ((a0, a1), a) in enumerate(segs):
            for (b0, b1), b in segs[j + 1:]:
                if min(a1, b1) - max(a0, b0) > tolerance:
                    hits += 1
                    print(f"{a}  x  {b}  along {'XYZ'[i]} at {tuple(rest)}: {max(a0, b0):.0f}..{min(a1, b1):.0f}")
    print(f"{hits} pin or axle pair(s) sharing a hole")


if __name__ == "__main__":
    commands = {"bbox": lambda a: cmd_bbox(a), "holes": lambda a: cmd_holes(*a), "slice": lambda a: cmd_slice(*a),
                "overlap": lambda a: cmd_overlap(*a), "pins": lambda a: cmd_pins(*a)}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](sys.argv[2:])
