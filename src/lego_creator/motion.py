"""Moving parts declared in LDraw, checked by turning them through their range (box approximation).

- `0 !LC TURN <ax> <ay> <az> <px> <py> <pz> <from> <to> <role>` in a submodel: everything in that submodel
  turns about the axis through the pivot (both in the submodel's own coordinates), from one angle to the other
  in degrees. Turning it must not run into the rest of the model.
- `0 !LC GROUND` in a submodel: its parts touch the floor (wheels, tracks). Every other part must stay at
  least `clearance` above the lowest of them.

Parts are compared as oriented boxes, so results are candidates for a human to look at, not proof.
Pairs already touching before anything turns are joints (an axle in a hole) and are not reported.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .ldraw import Document, PartRef, normalize_name
from .report import Issue

Vec = tuple[float, float, float]
Mat = tuple[Vec, Vec, Vec]  # rows
Box = tuple[Vec, Vec]  # local (min, max)


@dataclass(frozen=True)
class Turn:
    submodel: str
    axis: Vec
    pivot: Vec
    start: float
    end: float
    role: str


@dataclass(frozen=True)
class Placed:
    """A part in world coordinates, with the submodel instances it sits in (outermost first)."""

    ref: PartRef
    submodel: str
    rot: Mat
    pos: Vec
    chain: tuple[int, ...] = field(default=())


def parse_turns(doc: Document) -> tuple[list[Turn], list[Issue]]:
    turns: list[Turn] = []
    issues: list[Issue] = []
    usage = "expected '0 !LC TURN <ax> <ay> <az> <px> <py> <pz> <from> <to> <role>'"
    for sub in doc.models.values():
        for meta in sub.metas:
            if meta[:2] != ["!LC", "TURN"]:
                continue
            try:
                if len(meta) != 11:
                    raise ValueError
                n = [float(t) for t in meta[2:10]]
                if not any(n[:3]):
                    raise ValueError
            except ValueError:
                issues.append(Issue("error", "turn-malformed", f"{sub.name}: {usage}, got '0 {' '.join(meta)}'"))
                continue
            turns.append(Turn(sub.name, (n[0], n[1], n[2]), (n[3], n[4], n[5]), min(n[6], n[7]), max(n[6], n[7]), meta[10]))
    return turns, issues


def _mul(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _apply(m: Mat, v: Vec) -> Vec:
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3))  # type: ignore[return-value]


def _add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _rows(m: tuple[float, ...]) -> Mat:
    return ((m[0], m[1], m[2]), (m[3], m[4], m[5]), (m[6], m[7], m[8]))


def _rotation(axis: Vec, degrees: float) -> Mat:
    """Right-handed rotation about a unit axis (Rodrigues)."""
    n = math.sqrt(sum(c * c for c in axis))
    x, y, z = (c / n for c in axis)
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    t = 1 - c
    return ((t * x * x + c, t * x * y - s * z, t * x * z + s * y),
            (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
            (t * x * z - s * y, t * y * z + s * x, t * z * z + c))


def placements(doc: Document) -> tuple[list[Placed], dict[int, tuple[str, Mat, Vec]]]:
    """Every part of the main model in world coordinates, and each submodel instance's name and transform."""
    parts: list[Placed] = []
    instances: dict[int, tuple[str, Mat, Vec]] = {}
    identity: Mat = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    def walk(name: str, rot: Mat, pos: Vec, chain: tuple[int, ...], depth: int) -> None:
        if depth > 32:
            return
        for ref in doc.models[name].refs:
            r = _mul(rot, _rows(ref.matrix))
            p = _add(_apply(rot, ref.pos), pos)
            if ref.name in doc.models:
                key = len(instances)
                instances[key] = (ref.name, r, p)
                walk(ref.name, r, p, chain + (key,), depth + 1)
            else:
                parts.append(Placed(ref, name, r, p, chain))

    walk(doc.main.name, identity, (0.0, 0.0, 0.0), (), 0)
    return parts, instances


class _Obb:
    """Oriented box: center, unit axes (columns of the part's rotation) and half sizes."""

    def __init__(self, local: Box, rot: Mat, pos: Vec, shrink: float) -> None:
        lo, hi = local
        center = tuple((lo[i] + hi[i]) / 2 for i in range(3))
        self.center = _add(_apply(rot, center), pos)  # type: ignore[arg-type]
        self.axes = tuple((rot[0][i], rot[1][i], rot[2][i]) for i in range(3))
        self.half = tuple(max(0.0, (hi[i] - lo[i]) / 2 - shrink) for i in range(3))

    def radius(self, d: Vec) -> float:
        return sum(self.half[i] * abs(sum(self.axes[i][k] * d[k] for k in range(3))) for i in range(3))

    def overlaps(self, other: _Obb) -> bool:
        t = _sub(other.center, self.center)
        candidates = list(self.axes) + list(other.axes)
        for a in self.axes:
            for b in other.axes:
                candidates.append((a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]))
        for d in candidates:
            if sum(c * c for c in d) < 1e-9:
                continue
            if abs(sum(t[k] * d[k] for k in range(3))) > self.radius(d) + other.radius(d):
                return False
        return True


def _angles(turn: Turn, step: float) -> Iterator[float]:
    """Sampled angles nearest to the start position first, both ways."""
    k = 1
    while True:
        out = [a for a in (k * step, -k * step) if turn.start <= a <= turn.end]
        if not out and k * step > max(abs(turn.start), abs(turn.end)):
            return
        yield from out
        k += 1


def _label(p: Placed) -> str:
    return f"{p.ref.name} ({p.submodel} line {p.ref.line})"


def check_turns(doc: Document, turns: list[Turn], box: Callable[[str], Box | None], *,
                step: float = 15.0, tolerance: float = 2.0) -> list[Issue]:
    if not turns:
        return []
    parts, instances = placements(doc)
    boxes = {id(p): b for p in parts if (b := box(p.ref.name)) is not None}
    parts = [p for p in parts if id(p) in boxes]
    issues: list[Issue] = []
    for turn in turns:
        for key, (name, rot, pos) in instances.items():
            if name != turn.submodel:
                continue
            axis = _apply(rot, turn.axis)
            pivot = _add(_apply(rot, turn.pivot), pos)
            moving = [p for p in parts if key in p.chain]
            still = [(p, _Obb(boxes[id(p)], p.rot, p.pos, tolerance)) for p in parts if key not in p.chain]

            def hits(angle: float) -> set[tuple[int, int]]:
                r = _rotation(axis, angle)
                out = set()
                for i, m in enumerate(moving):
                    obb = _Obb(boxes[id(m)], _mul(r, m.rot), _add(_apply(r, _sub(m.pos, pivot)), pivot), tolerance)
                    out |= {(i, j) for j, (_, s) in enumerate(still) if obb.overlaps(s)}
                return out

            joints = hits(0.0)
            first: dict[tuple[int, int], float] = {}
            for angle in _angles(turn, step):
                for pair in hits(angle) - joints:
                    first.setdefault(pair, angle)
            for (i, j), angle in sorted(first.items(), key=lambda kv: (abs(kv[1]), kv[0])):
                issues.append(Issue("warning", "turn-interference",
                                    f"{turn.role}: {_label(moving[i])} runs into {_label(still[j][0])} at {angle:g}°"))
    return issues


def check_ground(doc: Document, box: Callable[[str], Box | None], *, clearance: float = 8.0) -> list[Issue]:
    grounded = {sub.name for sub in doc.models.values() if ["!LC", "GROUND"] in sub.metas}
    if not grounded:
        return []
    parts, instances = placements(doc)
    on_ground = {k for k, (name, _, _) in instances.items() if name in grounded}

    def bottom(p: Placed) -> float | None:
        b = box(p.ref.name)
        if b is None:
            return None
        obb = _Obb(b, p.rot, p.pos, 0.0)
        return obb.center[1] + obb.radius((0.0, 1.0, 0.0))  # +Y is down

    floor = max((y for p in parts if on_ground & set(p.chain) and (y := bottom(p)) is not None), default=None)
    if floor is None:
        return []
    issues = []
    for p in parts:
        if on_ground & set(p.chain) or (y := bottom(p)) is None:
            continue
        if y > floor - clearance:
            gap = floor - y
            where = "below the floor" if gap < 0 else f"{gap:g} LDU above the floor"
            issues.append(Issue("warning", "ground-clearance", f"{_label(p)} reaches {where} (wheels and tracks touch at y {floor:g})"))
    return issues


class PartBoxes:
    """Local bounding boxes of LDraw parts, read from the library roots (parts/, p/, then the root).

    A subfile contributes the corners of its own box, so a turned subfile makes the box slightly larger
    than the exact one; close enough for the box checks above.
    """

    def __init__(self, roots: tuple[Path, ...] | list[Path]) -> None:
        self.roots = tuple(roots)
        self._box = lru_cache(maxsize=None)(self._load)

    def _find(self, name: str) -> Path | None:
        for root in self.roots:
            for folder in ("parts", "p", ""):
                path = root / folder / name
                if path.is_file():
                    return path
        return None

    def _load(self, name: str) -> Box | None:
        path = self._find(name)
        if path is None:
            return None
        pts: list[Vec] = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            t = line.split(None, 14)
            if len(t) == 15 and t[0] == "1":
                child = self._box(normalize_name(t[14]))
                if child is None:
                    continue
                v = [float(x) for x in t[2:14]]
                m, pos = _rows(tuple(v[3:12])), (v[0], v[1], v[2])
                lo, hi = child
                pts += [_add(_apply(m, (x, y, z)), pos) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
            elif t and t[0] in ("3", "4"):
                v = [float(x) for x in line.split()[2:]]
                pts += [(v[i], v[i + 1], v[i + 2]) for i in range(0, len(v) - 2, 3)]
        if not pts:
            return None
        return (tuple(min(q[i] for q in pts) for i in range(3)),  # type: ignore[return-value]
                tuple(max(q[i] for q in pts) for i in range(3)))

    def __call__(self, name: str) -> Box | None:
        return self._box(normalize_name(name))
