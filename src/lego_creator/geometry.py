"""What library parts are shaped like and how they connect: part files read from LDraw roots, placed parts, rays.

Pins and axles are modelled along their local X.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Container, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

Vec = tuple[float, float, float]
Matrix = tuple[Vec, Vec, Vec]  # rows; column c is where local axis c points
Tri = tuple[Vec, ...]
Box = tuple[list[float], list[float]]
IDENTITY: Matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

# Primitives whose local Y axis is the axis of a hole or a pin.
HOLES = ("peghole", "axlehol", "axl3hole", "connhole", "beamhole", "npeghol")
# Parts that are meant to sit inside other parts.
CONNECTORS = frozenset({"61332", "6558", "3673", "3749", "43093", "11214", "18651", "32054", "4274", "3713", "32123b",
                        "32062", "4519", "3705", "32073", "3706", "44294", "3707", "60485", "3708", "87083"})
# Connectors that sit on an axle rather than in a hole.
BUSHES = frozenset({"3713", "32123b"})
AXLES = frozenset({"4519", "3705", "32073", "3706", "44294", "3707", "60485", "3708", "23948", "50450", "87083",
                   "15462", "55013", "32062"})
# Axles with a stop at their local +X end.
STOP_AT_PLUS_X = frozenset({"87083", "15462", "55013"})
# Parts that bend away instead of stopping a gear.
BANDS = frozenset({"85543"})
# Parts that turn on an axle and need something on both sides to stay in place.
GEARS = frozenset({"32270", "32498", "46372", "18575", "6589", "32198a", "35185", "4185a", "56903", "39367p01",
                   "49295p01", "57519", "61254"})


def apply(m: Matrix, t: Vec, v: Vec) -> Vec:
    return tuple(m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] + t[i] for i in range(3))  # type: ignore[return-value]


def compose(m: Matrix, n: Matrix) -> Matrix:
    return tuple(tuple(sum(m[i][k] * n[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def refs(text: str) -> Iterator[tuple[Vec, Matrix, str]]:
    """(position, matrix, file name) of every type 1 line."""
    for line in text.splitlines():
        t = line.split(None, 14)
        if len(t) == 15 and t[0] == "1":
            v = [float(x) for x in t[2:14]]
            yield tuple(v[:3]), (tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12])), t[14].strip()  # type: ignore[misc]


def box(pts: Sequence[Vec]) -> Box:
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


class Shapes:
    """Library parts in their own frames, read from `roots` (parts/, p/, then the root; earlier roots win).

    Every file is read once per instance.
    """

    def __init__(self, roots: Sequence[Path]) -> None:
        self.roots = tuple(roots)
        self.points = functools.lru_cache(maxsize=None)(self._points)
        self.triangles = functools.lru_cache(maxsize=None)(self._triangles)
        self.holes = functools.lru_cache(maxsize=None)(self._holes)

    def find(self, name: str) -> Path | None:
        name = name.strip().replace("\\", "/").lower()
        for root in self.roots:
            for folder in ("parts", "p", ""):
                path = root / folder / name
                if path.is_file():
                    return path
        return None

    def _text(self, name: str) -> str | None:
        path = self.find(name)
        return None if path is None else path.read_text(encoding="utf-8", errors="replace")

    def _points(self, name: str) -> tuple[Vec, ...]:
        text = self._text(name)
        if text is None:
            return ()
        out = []
        for pos, m, child in refs(text):
            out += [apply(m, pos, p) for p in self.points(child)]
        for line in text.splitlines():
            t = line.split()
            if t and t[0] in ("3", "4"):
                v = [float(x) for x in t[2:]]
                out += [tuple(v[i:i + 3]) for i in range(0, len(v) - 2, 3)]
        return tuple(out)

    def _triangles(self, name: str) -> tuple[Tri, ...]:
        text = self._text(name)
        if text is None:
            return ()
        out = []
        for pos, m, child in refs(text):
            out += [tuple(apply(m, pos, v) for v in tri) for tri in self.triangles(child)]
        for line in text.splitlines():
            t = line.split()
            if t and t[0] == "3" and len(t) >= 11:
                v = [float(x) for x in t[2:11]]
                out.append((tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9])))
            elif t and t[0] == "4" and len(t) >= 14:
                v = [float(x) for x in t[2:14]]
                a, b, c, d = tuple(v[0:3]), tuple(v[3:6]), tuple(v[6:9]), tuple(v[9:12])
                out += [(a, b, c), (a, c, d)]
        return tuple(out)

    def _holes(self, name: str) -> tuple[tuple[tuple[Vec, str], tuple[str, ...]], ...]:
        """((position, axis letter), primitive names) of every hole in a part, in its own frame."""
        found: dict[tuple, set[str]] = {}

        def walk(name: str, m: Matrix, t: Vec) -> None:
            text = self._text(name)
            if text is None:
                return
            for pos, n, child in refs(text):
                world, at = compose(m, n), apply(m, t, pos)
                base = child.replace("\\", "/").lower().rsplit("/", 1)[-1]
                if base.startswith(HOLES):
                    axis = [abs(world[i][1]) for i in range(3)]
                    found.setdefault((tuple(round(c, 1) for c in at), "XYZ"[axis.index(max(axis))]), set()).add(base)
                else:
                    walk(child, world, at)

        walk(name, IDENTITY, (0, 0, 0))
        return tuple((k, tuple(sorted(v))) for k, v in sorted(found.items(), key=lambda kv: (kv[0][1], kv[0][0])))


@dataclass(eq=False)
class Solid:
    """One library part placed in some frame."""

    label: str
    part: str  # part id
    name: str  # file name as referenced
    rot: Matrix
    pos: Vec
    shapes: Shapes = field(repr=False)

    @functools.cached_property
    def points(self) -> list[Vec]:
        return [apply(self.rot, self.pos, p) for p in self.shapes.points(self.name)]

    @functools.cached_property
    def box(self) -> Box:
        return box(self.points) if self.points else ([0.0] * 3, [0.0] * 3)

    @functools.cached_property
    def triangles(self) -> list[Tri]:
        return [tuple(apply(self.rot, self.pos, v) for v in tri) for tri in self.shapes.triangles(self.name)]

    def axis(self, column: int) -> int | None:
        """Frame axis that the part's local axis `column` points along, if it is axis-aligned."""
        v = [abs(self.rot[i][column]) for i in range(3)]
        i = v.index(max(v))
        return i if v[i] > 0.999 else None

    def ends(self, i: int) -> tuple[float, float]:
        """Extent along frame axis i of a pin or axle."""
        lo, hi = box(self.shapes.points(self.name))
        return tuple(sorted(self.pos[i] + self.rot[i][0] * x for x in (lo[0], hi[0])))  # type: ignore[return-value]

    def material(self, i: int, pj: float, pk: float, radius: float) -> list[tuple[float, float]]:
        """Spans along axis i covered by faces that come within `radius` of the line through (pj, pk)."""
        j, k = [x for x in range(3) if x != i]
        r2 = radius * radius
        spans = sorted((min(v[i] for v in tri), max(v[i] for v in tri)) for tri in self.triangles
                       if any((v[j] - pj) ** 2 + (v[k] - pk) ** 2 <= r2 for v in tri))
        out: list[list[float]] = []
        for lo, hi in spans:
            if out and lo <= out[-1][1] + 1:
                out[-1][1] = max(out[-1][1], hi)
            else:
                out.append([lo, hi])
        return [(lo, hi) for lo, hi in out]


def _ray_hit(tris: Iterable[Tri], i: int, j: int, k: int, pj: float, pk: float, start: float, d: int,
             reach: float) -> bool:
    """Does the line along axis i through (pj, pk) cross a triangle more than 0.5 and at most `reach` from `start`
    in direction d?"""
    for a, b, c in tris:
        if pj < min(a[j], b[j], c[j]) or pj > max(a[j], b[j], c[j]):
            continue
        if pk < min(a[k], b[k], c[k]) or pk > max(a[k], b[k], c[k]):
            continue
        det = (b[j] - a[j]) * (c[k] - a[k]) - (c[j] - a[j]) * (b[k] - a[k])
        if abs(det) < 1e-9:
            continue
        l1 = ((pj - a[j]) * (c[k] - a[k]) - (c[j] - a[j]) * (pk - a[k])) / det
        l2 = ((b[j] - a[j]) * (pk - a[k]) - (pj - a[j]) * (b[k] - a[k])) / det
        if l1 < -1e-6 or l2 < -1e-6 or l1 + l2 > 1 + 1e-6:
            continue
        if 0.5 < (a[i] + l1 * (b[i] - a[i]) + l2 * (c[i] - a[i]) - start) * d <= reach:
            return True
    return False


def first_blocker(solids: Iterable[Solid], i: int, pj: float, pk: float, start: float, d: int, *,
                  reach: float = math.inf, skip: Container[str] = ()) -> Solid | None:
    """First solid, in the given order, whose faces the ray along axis i through (pj, pk) crosses, from `start`
    in direction d; solids labelled in `skip` are ignored."""
    j, k = [x for x in range(3) if x != i]
    for q in solids:
        if q.label in skip:
            continue
        lo, hi = q.box
        if not (lo[j] <= pj <= hi[j] and lo[k] <= pk <= hi[k]) or (hi[i] if d > 0 else -lo[i]) <= start * d:
            continue
        if (lo[i] if d > 0 else -hi[i]) > start * d + reach:
            continue
        if _ray_hit(q.triangles, i, j, k, pj, pk, start, d, reach):
            return q
    return None
