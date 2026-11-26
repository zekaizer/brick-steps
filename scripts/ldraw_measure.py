"""Measure LDraw parts and models before placing or reviewing them. Part geometry is lego_creator.geometry.

    uv run python scripts/ldraw_measure.py bbox PART...       bounding box of each part
    uv run python scripts/ldraw_measure.py holes PART         pin/axle hole positions and axes
    uv run python scripts/ldraw_measure.py slice PART AXIS LO HI   bounding box of the geometry between LO and HI
    uv run python scripts/ldraw_measure.py overlap SLUG       placed parts whose boxes intersect
    uv run python scripts/ldraw_measure.py pins SLUG          pins and axles that share a hole
    uv run python scripts/ldraw_measure.py axles SLUG         axles that stop at a face; gears that can come off or have play
    uv run python scripts/ldraw_measure.py balance SLUG       rough centre of gravity against the floor contacts
    uv run python scripts/ldraw_measure.py steps SLUG [MAX]   parts per instruction step, steps above MAX (10)
    uv run python scripts/ldraw_measure.py line SLUG X Y Z AXIS   parts with holes on that line, pins already on it
    uv run python scripts/ldraw_measure.py where SLUG LABEL...    model position and box of parts a report named
    uv run python scripts/ldraw_measure.py assembly SLUG      parts with nothing to hold them yet, pins that
                                                              cannot be pushed in, parts that cannot slide on

Parts are looked up in ldraw/ and custom/. `overlap` compares axis-aligned boxes, so it reports
candidates to look at, not proven collisions. Use `slice` on the larger part to see whether its
geometry really reaches the other one. Pins, axles and bushes are skipped because they sit inside
other parts on purpose, and so are pairs that mesh (tread on sprocket). `pins` reports two pins or
axles on the same line whose lengths overlap, which means both are drawn in one hole.

SLUG may also be a path to an .mpd file. `axles`, `assembly` and `balance` read real geometry, but
they know nothing of friction, flex or fingers: they point at places to look at, as `overlap` does.
`assembly` follows the instruction steps: a part may rest only on parts of earlier or the same
step, and a pin or axle is pushed in along its own axis, so one of its ends needs a clear line out
past every part placed before it. `balance` weighs parts from a rough table and is an estimate.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from lego_creator.geometry import (
    AXLES,
    BANDS,
    BUSHES,
    CONNECTORS,
    GEARS,
    IDENTITY,
    STOP_AT_PLUS_X,
    Matrix,
    Shapes,
    Solid,
    apply,
    box,
    compose,
    first_blocker,
    refs,
)

ROOT = Path(__file__).resolve().parents[1]
ROOTS = (ROOT / "ldraw", ROOT / "custom")
SHAPES = Shapes(ROOTS)
find, points, triangles, hole_list = SHAPES.find, SHAPES.points, SHAPES.triangles, SHAPES.holes
# Rough weights in grams; any other part is weighed by its box, beams by their holes.
GRAMS = {"45601c01": 155, "54675": 55, "54675c01": 58, "54696p01": 38, "54696p01c01": 41, "37308c01": 15,
         "37316c01": 20, "37312c01": 15, "39794": 7, "39790": 10, "39369": 20, "64179": 4, "15458": 6, "11954": 6,
         "24119": 4, "41751": 8, "41749": 4, "41750": 4, "3738": 2.5, "39789": 3, "44375b": 4, "32498": 3,
         "46372": 2, "18938": 12, "18939": 8, "57518": 1.2, "57519": 4}
BEAM_HOLES = {"32523": 3, "32316": 5, "32524": 7, "40490": 9, "32525": 11, "41239": 13, "32278": 15}
# Pairs that mesh by design and always intersect as boxes.
MESHING = {frozenset(("57518", "57519")), frozenset(("57518",))}  # tread on sprocket, tread link on its neighbour


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
    for (at, axis), names in hole_list(part + ".dat"):
        print(f"axis {axis}  at {at}  {', '.join(names)}")


def model_text(target: str) -> str:
    """The .mpd text of a model slug, or of a file path ending in .mpd."""
    path = Path(target)
    if path.suffix == ".mpd" and path.is_file():
        return path.read_text(encoding="utf-8")
    return (ROOT / "models" / target / "model.mpd").read_text(encoding="utf-8")


def placed_parts(slug: str):
    """(path, part, matrix, position) of every part in the model, submodels flattened."""
    text = model_text(slug)
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


@dataclass(eq=False)
class Placed(Solid):
    levels: tuple[tuple[str, int], ...]  # (sub-assembly instance, step in it) from the main model down
    ground: bool


def _blocks(text: str) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    name = None
    for line in text.splitlines():
        t = line.split(None, 2)
        if t[:2] == ["0", "FILE"]:
            name = t[2].strip().lower()
            blocks[name] = []
        elif name:
            blocks[name].append(line)
    return blocks


def placements(text: str) -> list[Placed]:
    """Every part with its instruction step at each sub-assembly level, sub-assemblies flattened."""
    blocks = _blocks(text)
    grounds = {n for n, lines in blocks.items() if any(line.split()[:3] == ["0", "!LC", "GROUND"] for line in lines)}
    out: list[Placed] = []

    def walk(sub: str, m: Matrix, t: tuple[float, float, float], path: str, levels: tuple, ground: bool) -> None:
        step, k = 1, 0
        for line in blocks[sub]:
            tok = line.split(None, 14)
            if tok[:2] == ["0", "STEP"]:
                step += 1
            elif len(tok) == 15 and tok[0] == "1":
                v = [float(x) for x in tok[2:14]]
                n = (tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12]))
                child = tok[14].strip().lower()
                world, at, here = compose(m, n), apply(m, t, tuple(v[:3])), levels + ((path, step),)
                if child in blocks:
                    walk(child, world, at, f"{path}{child}#{k}/", here, ground or child in grounds)
                else:
                    part = child.removesuffix(".dat")
                    out.append(Placed(f"{path}{part}#{k}", part, child, world, at, SHAPES, here, ground))
                k += 1

    main = next(iter(blocks))
    walk(main, IDENTITY, (0, 0, 0), "", (), main in grounds)
    return out


def _before(q: Placed, p: Placed, same_step: bool) -> bool:
    """q is placed before p while p's sub-assembly is built (or in the same step when same_step)."""
    n = len(p.levels) - 1
    if len(q.levels) <= n or q.levels[:n] != p.levels[:n] or q.levels[n][0] != p.levels[n][0]:
        return False
    return q.levels[n][1] < p.levels[n][1] or (same_step and q.levels[n][1] == p.levels[n][1])


def _touch(a: tuple[list[float], list[float]], b: tuple[list[float], list[float]], gap: float = 1.0) -> bool:
    return all(a[0][i] - gap <= b[1][i] and b[0][i] - gap <= a[1][i] for i in range(3))


def _blocker(parts: list[Placed], i: int, pj: float, pk: float, start: float, d: int, skip=()) -> str | None:
    hit = first_blocker(parts, i, pj, pk, start, d, skip=skip)
    return hit.label if hit else None


def _pinned(g: Placed, i: int, axle: Placed, ps: list[Placed]) -> bool:
    """A pin or axle beside `axle` runs through the gear and on into another part, so the gear cannot slide."""
    j, k = [x for x in range(3) if x != i]
    lo, hi = g.box
    for q in ps:
        if q is axle or q.part not in CONNECTORS or q.part in BUSHES or q.axis(0) != i:
            continue
        if not (lo[j] < q.pos[j] < hi[j] and lo[k] < q.pos[k] < hi[k]):
            continue
        if (q.pos[j] - axle.pos[j]) ** 2 + (q.pos[k] - axle.pos[k]) ** 2 < 16:
            continue
        e0, e1 = q.ends(i)
        if e1 <= lo[i] or e0 >= hi[i]:
            continue
        for a, b in ((e0, lo[i]), (hi[i], e1)):
            if b - a < 4:
                continue
            point = [0.0] * 3
            point[i], point[j], point[k] = (a + b) / 2, q.pos[j], q.pos[k]
            if any(r is not g and r is not q and all(r.box[0][x] <= point[x] <= r.box[1][x] for x in range(3)) for r in ps):
                return True
    return False


def axle_report(text: str) -> list[tuple[str, ...]]:
    """("touches-only", axle, part) when an axle end only meets a part's face; ("gear-free", gear, side, axle)
    when nothing on the axle stops the gear on that side, so it can come off; ("gear-play", gear, side, axle,
    detail) when the nearest stop on that side is more than 1.5 LDU away. Rubber bands are no stop, and a gear
    pinned to a neighbour through its own pin holes is held."""
    ps = placements(text)
    out: list[tuple[str, ...]] = []
    for a in ps:
        i = a.axis(0)
        if a.part not in AXLES or i is None:
            continue
        j, k = [x for x in range(3) if x != i]
        pj, pk = a.pos[j], a.pos[k]
        s0, s1 = a.ends(i)
        near = []
        for q in ps:
            if q is a or (q.part in CONNECTORS and q.part not in BUSHES):
                continue
            lo, hi = q.box
            if lo[j] - 12 <= pj <= hi[j] + 12 and lo[k] - 12 <= pk <= hi[k] + 12 and hi[i] >= s0 - 2 and lo[i] <= s1 + 2:
                near.append(q)
        axis = "XYZ"[i]
        for q in near:
            if q.part in GEARS | BUSHES:
                continue
            for c0, c1 in q.material(i, pj, pk, 8):
                if -1 <= min(c1, s1) - max(c0, s0) <= 1:
                    out.append(("touches-only", a.label, f"{q.label} {axis} {c0:.0f}..{c1:.0f}, axle {s0:.0f}..{s1:.0f}"))
        stop = None
        if a.part in STOP_AT_PLUS_X:
            stop = s1 if a.rot[i][0] > 0 else s0
        for g in near:
            if g.part not in GEARS or _pinned(g, i, a, ps):
                continue
            others = [(o0, o1, o.label) for o in near if o is not g and o.part not in BANDS
                      for o0, o1 in o.material(i, pj, pk, 12)]
            for c0, c1 in g.material(i, pj, pk, 8):
                if min(c1, s1) - max(c0, s0) <= 1:
                    continue
                for face, sign in ((c0, -1), (c1, 1)):
                    if stop is not None and abs(stop - face) <= 4:
                        continue
                    gaps = [(max(o0 - face, 0) if sign > 0 else max(face - o1, 0), label) for o0, o1, label in others
                            if (o1 >= face + 0.5 if sign > 0 else o0 <= face - 0.5)]
                    side = f"{'+' if sign > 0 else '-'}{axis}"
                    if not gaps:
                        out.append(("gear-free", g.label, side, a.label))
                    elif (gap := min(gaps))[0] > 1.5:
                        out.append(("gear-play", g.label, side, a.label, f"{gap[0]:.0f} LDU to {gap[1]}"))
    return out


def _mass(p: Placed) -> float:
    if p.part in GRAMS:
        return GRAMS[p.part]
    if p.part in BEAM_HOLES:
        return 0.23 * BEAM_HOLES[p.part]
    lo, hi = box(points(p.name)) if points(p.name) else ([0.0] * 3, [0.0] * 3)
    return min(20.0, 1.5e-5 * (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2]))


def _hull(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def balance_report(text: str) -> dict:
    """Rough mass and centre of gravity (x, z) against the hull of the lowest points of `0 !LC GROUND` parts."""
    ps = placements(text)
    total = sum(_mass(p) for p in ps)
    cg = (sum(_mass(p) * p.pos[0] for p in ps) / total, sum(_mass(p) * p.pos[2] for p in ps) / total)
    ground = [p for p in ps if p.ground]
    floor = max((p.box[1][1] for p in ground), default=0.0)
    hull = _hull([(v[0], v[2]) for p in ground for v in p.points if v[1] >= floor - 2])
    margin = float("-inf")
    if len(hull) >= 3:
        margin = float("inf")
        for (x0, z0), (x1, z1) in zip(hull, hull[1:] + hull[:1]):
            length = ((x1 - x0) ** 2 + (z1 - z0) ** 2) ** 0.5
            margin = min(margin, ((x1 - x0) * (cg[1] - z0) - (z1 - z0) * (cg[0] - x0)) / length)
    return {"mass": total, "cg": cg, "floor": floor, "support": hull, "margin": margin, "inside": margin > 0}


def step_sizes(text: str) -> list[tuple[str, int, int]]:
    out = []
    for name, lines in _blocks(text).items():
        step, count = 1, 0
        for line in lines:
            tok = line.split()
            if tok[:2] == ["0", "STEP"]:
                if count:
                    out.append((name, step, count))
                step, count = step + 1, 0
            elif tok[:1] == ["1"]:
                count += 1
        if count:
            out.append((name, step, count))
    return out


def assembly_report(text: str) -> list[tuple[str, ...]]:
    """("floating", part, detail), ("pin-blocked", pin, detail) and ("no-slide", part, detail) by instruction step."""
    ps = placements(text)
    out: list[tuple[str, ...]] = []
    first: dict[str, int] = {}
    for p in ps:
        inst, step = p.levels[-1]
        first[inst] = min(first.get(inst, step), step)
    units: dict[str, list[Placed]] = {}
    for p in ps:
        for n in range(len(p.levels) - 1):
            units.setdefault(p.levels[n + 1][0], []).append(p)
    for p in ps:
        inst, step = p.levels[-1]
        if step == first[inst]:
            continue
        if not any(q is not p and _before(q, p, True) and _touch(q.box, p.box) for q in ps):
            out.append(("floating", p.label, f"step {step}: touches nothing placed by then"))
    for unit, members in units.items():
        ref = members[0]
        n = next(x for x in range(len(ref.levels)) if ref.levels[x + 1][0] == unit)
        parent, step = ref.levels[n]
        if step == first.get(parent, step):
            continue
        names = {m.label for m in members}
        others = [q for q in ps if q.label not in names and len(q.levels) > n and q.levels[:n] == ref.levels[:n]
                  and q.levels[n][0] == parent and q.levels[n][1] <= step]
        if not any(_touch(q.box, m.box) for q in others for m in members):
            out.append(("floating", unit.rstrip("/"), f"step {step}: the sub-assembly touches nothing placed by then"))
    for p in ps:
        i = p.axis(0)
        if p.part not in CONNECTORS or p.part in BUSHES or i is None:
            continue
        j, k = [x for x in range(3) if x != i]
        s0, s1 = p.ends(i)
        earlier = [q for q in ps if q is not p and _before(q, p, False)]
        hits = [_blocker(earlier, i, p.pos[j], p.pos[k], s1, 1), _blocker(earlier, i, p.pos[j], p.pos[k], s0, -1)]
        if all(hits):
            out.append(("pin-blocked", p.label, f"step {p.levels[-1][1]}: +{'XYZ'[i]} {hits[0]}, -{'XYZ'[i]} {hits[1]}"))
    for p in ps:
        if p.part in CONNECTORS:
            continue
        holes = {}
        for (pos, axis), _ in hole_list(p.name):
            w = apply(p.rot, p.pos, pos)
            i = "XYZ".index(axis)
            vec = [abs(p.rot[r][i]) for r in range(3)]
            wi = vec.index(max(vec))
            if vec[wi] > 0.999:
                holes.setdefault(wi, set()).add((round(w[0], 1), round(w[1], 1), round(w[2], 1)))
        for i, centres in holes.items():
            j, k = [x for x in range(3) if x != i]
            # Only pins already in place force the part to slide on; pins of the same step go in after it.
            pins = [q for q in ps if q.part in CONNECTORS and q.part not in BUSHES and q.axis(0) == i
                    and _before(q, p, False)
                    and any(abs(q.pos[j] - c[j]) < 1 and abs(q.pos[k] - c[k]) < 1 for c in centres)]
            if not pins:
                continue
            on_line = {q.label for q in ps if q.part in CONNECTORS and q.axis(0) == i
                       and any(abs(q.pos[j] - c[j]) < 1 and abs(q.pos[k] - c[k]) < 1 for c in centres)}
            earlier = [q for q in ps if q is not p and _before(q, p, False)]
            blocked = []
            for d in (1, -1):
                face = p.box[1][i] if d > 0 else p.box[0][i]
                hit = next((b for c in centres if (b := _blocker(earlier, i, c[j], c[k], face, d, on_line))), None)
                blocked.append(hit)
            if all(blocked):
                out.append(("no-slide", p.label, f"step {p.levels[-1][1]}: onto pins along {'XYZ'[i]}, "
                                                 f"+{'XYZ'[i]} {blocked[0]}, -{'XYZ'[i]} {blocked[1]}"))
    return out


def where_report(text: str, labels: list[str]) -> list[tuple[str, tuple, tuple, tuple]]:
    """(label, position, box low corner, box high corner) in model coordinates for each label a report printed."""
    by_label = {p.label: p for p in placements(text)}
    out = []
    for label in labels:
        if label not in by_label:
            raise SystemExit(f"no part labelled {label}")
        p = by_label[label]
        out.append((label, tuple(p.pos), *p.box))
    return out


def line_report(text: str, point: tuple[float, float, float], axis: str) -> dict:
    """Parts with holes on the line through `point` along `axis`, and the pins or axles already on it."""
    ps = placements(text)
    i = "XYZ".index(axis.upper())
    j, k = [x for x in range(3) if x != i]
    holes, connectors = [], []
    for p in ps:
        if p.part in CONNECTORS and p.part not in BUSHES:
            if p.axis(0) == i and abs(p.pos[j] - point[j]) < 1 and abs(p.pos[k] - point[k]) < 1:
                connectors.append((p.label, *p.ends(i)))
            continue
        along = []
        for (pos, letter), _ in hole_list(p.name):
            if abs(p.rot[i]["XYZ".index(letter)]) < 0.999:
                continue
            w = apply(p.rot, p.pos, pos)
            if abs(w[j] - point[j]) < 1 and abs(w[k] - point[k]) < 1:
                along.append(w[i])
        if along:
            holes.append((p.label, min(along), max(along)))
    return {"holes": sorted(holes, key=lambda h: h[1]), "connectors": sorted(connectors, key=lambda c: c[1])}


def cmd_axles(target: str) -> None:
    report = axle_report(model_text(target))
    for w in report:
        print("  ".join(w))
    print(f"{len(report)} axle finding(s)")


def cmd_balance(target: str) -> None:
    b = balance_report(model_text(target))
    print(f"mass about {b['mass']:.0f} g, centre of gravity x {b['cg'][0]:.0f} z {b['cg'][1]:.0f}, floor y {b['floor']:.0f}")
    print("floor contacts (x, z): " + " ".join(f"({x:.0f}, {z:.0f})" for x, z in b["support"]))
    state = "inside" if b["inside"] else "OUTSIDE"
    print(f"centre of gravity is {state} the contacts, {b['margin']:.0f} LDU from the nearest edge")


def cmd_steps(target: str, most: str = "10") -> None:
    sizes = step_sizes(model_text(target))
    big = [s for s in sizes if s[2] > int(most)]
    for name, step, count in big:
        print(f"{name} step {step}: {count} parts")
    print(f"{len(sizes)} steps, {len(big)} above {most} parts")


def cmd_line(target: str, x: str, y: str, z: str, axis: str) -> None:
    report = line_report(model_text(target), (float(x), float(y), float(z)), axis)
    for label, lo, hi in report["holes"]:
        print(f"hole  {label}  {axis.upper()} {lo:.0f}" + (f"..{hi:.0f}" if hi != lo else ""))
    for label, lo, hi in report["connectors"]:
        print(f"pin   {label}  {axis.upper()} {lo:.0f}..{hi:.0f}")
    print(f"{len(report['holes'])} part(s) with holes on the line, {len(report['connectors'])} pin(s) or axle(s) on it")


def cmd_where(target: str, *labels: str) -> None:
    for label, at, lo, hi in where_report(model_text(target), list(labels)):
        span = " ".join(f"{a}{l:.0f}..{h:.0f}" for a, l, h in zip("XYZ", lo, hi))
        print(f"{label}  at {at[0]:.0f} {at[1]:.0f} {at[2]:.0f}  box {span}")


def cmd_assembly(target: str) -> None:
    report = assembly_report(model_text(target))
    for w in report:
        print("  ".join(w))
    print(f"{len(report)} assembly finding(s)")


if __name__ == "__main__":
    commands = {"bbox": lambda a: cmd_bbox(a), "holes": lambda a: cmd_holes(*a), "slice": lambda a: cmd_slice(*a),
                "overlap": lambda a: cmd_overlap(*a), "pins": lambda a: cmd_pins(*a), "axles": lambda a: cmd_axles(*a),
                "balance": lambda a: cmd_balance(*a), "steps": lambda a: cmd_steps(*a),
                "assembly": lambda a: cmd_assembly(*a), "line": lambda a: cmd_line(*a),
                "where": lambda a: cmd_where(*a)}
    if len(sys.argv) < 3 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    commands[sys.argv[1]](sys.argv[2:])
