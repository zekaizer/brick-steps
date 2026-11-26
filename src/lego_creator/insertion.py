"""How each reference of a submodel arrives in the 3D step view: the side of its place it starts on, how far it
travels and in which wave of its step it moves.

Worked out per submodel in the submodel's own axes, with only that submodel's earlier references in place; a
sub-assembly reference moves as one unit. A pin or axle goes in along its own axis from the side it sticks out
on, and whatever goes onto pins or axles slides along them from their free tips (joint). Tread links and bands
go on from above whatever they join (flexible). Anything else takes the first clear side, from above first (free), and drops from
above when every side is blocked (fallback). `0 !LC INSERT FROM <side>` right above a reference overrides the
guess. Paths are checked with rays against earlier parts, so a direction is a guess to review, not proof.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Literal

from .geometry import (
    FLEXIBLE,
    PIN_LIKE,
    Matrix,
    Shapes,
    Solid,
    Vec,
    apply,
    compose,
    first_blocker,
)
from .ldraw import Document, PartRef, Submodel, part_id
from .report import Issue

MARGIN = 20.0  # LDU a part starts beyond the last thing it has to clear
MIN_TRAVEL = 40.0
PIN_RADIUS = 8.0  # faces with a vertex this close to a pin's line hold the pin; hole walls are at 6
FACE_SAMPLES = ((0.0, 0.0), (0.7, 0.7), (0.7, -0.7), (-0.7, 0.7), (-0.7, -0.7))  # of a box face's half sizes
ARROW_GAP = 6.0  # LDU from a part's outer face to the tip of its arrow
TRAIN_GAP = 20.0  # parts coming in on one line no further apart than this share one arrow
SAME_LINE = 2.0

Rule = Literal["override", "joint", "flexible", "free", "fallback"]
Box = tuple[Vec, Vec]


@dataclass(frozen=True)
class Side:
    """A side of a reference's place, in its submodel's axes. The part starts there and moves in."""

    axis: int
    sign: int

    @property
    def vector(self) -> tuple[int, int, int]:
        v = [0, 0, 0]
        v[self.axis] = self.sign
        return (v[0], v[1], v[2])

    @property
    def name(self) -> str:
        return ("+" if self.sign > 0 else "-") + "XYZ"[self.axis]

    @staticmethod
    def parse(token: str) -> Side | None:
        """'+X' .. '-Z'; None for anything else."""
        if len(token) != 2 or token[0] not in "+-" or token[1] not in "XYZ":
            return None
        return Side("XYZ".index(token[1]), 1 if token[0] == "+" else -1)


FROM_ABOVE = Side(1, -1)  # LDraw -Y is up
FROM_BELOW = Side(1, 1)
# Free parts try these after FROM_ABOVE, sorted by how far they point away from what is built; ties keep this order.
HORIZONTAL = (Side(2, -1), Side(0, -1), Side(0, 1), Side(2, 1))


@dataclass(frozen=True)
class Insertion:
    """How one reference arrives, in its submodel's axes."""

    side: Side
    travel: float  # LDU from where the part starts to its place
    wave: int  # 0 moves first; a part moves one wave after the latest new part of its step it goes into or onto
    order: int  # position in its step's sequence, 0-based
    rule: Rule
    partners: tuple[int, ...]  # reference indices of the parts it goes into or onto
    blocked_by: int | None  # reference index of an earlier part in its path; None when the path is clear
    box: Box  # where it ends up
    note: str = ""  # a tie-break, or what is in the way of the side it did not take


def insertions(doc: Document, shapes: Shapes) -> dict[str, tuple[Insertion, ...]]:
    """One Insertion per reference of every submodel, index i for sub.refs[i]. A malformed `0 !LC INSERT` is
    ignored here; check_insertions() reports it."""
    out: dict[str, tuple[Insertion, ...]] = {}
    for sub in doc.models.values():
        overrides = {i: o.side for i, o in _overrides(sub)[0].items()}
        build = _Build(doc, sub, shapes)
        planned: dict[int, Insertion] = {}
        for step in sorted({ref.step for ref in sub.refs}):
            planned |= build.plan_step(step, overrides)
        out[sub.name] = tuple(planned[i] for i in range(len(sub.refs)))
    return out


def moves(arrivals: Sequence[Insertion]) -> list[dict]:
    """What the 3D view needs for the new references of one step, in the same order.

    `from` is the side as a unit vector, `travel` and `wave` are ints. Parts that do not come from above get an
    arrow: one per train of parts on one line from one side, as `at` (the tip, in the submodel's axes) on the
    entry of the part furthest out.
    """
    tips = _arrow_tips(arrivals)
    out = []
    for k, a in enumerate(arrivals):
        entry: dict = {"from": list(a.side.vector), "travel": round(a.travel), "wave": a.wave}
        if k in tips:
            entry["at"] = [round(c) for c in tips[k]]
        out.append(entry)
    return out


def _arrow_tips(arrivals: Sequence[Insertion]) -> dict[int, Vec]:
    lines: list[tuple[Side, Vec, list[int]]] = []
    for k, a in enumerate(arrivals):
        if a.side == FROM_ABOVE:
            continue
        j, l = _others(a.side.axis)
        c = _centre(a.box)
        line = next((m for side, at, m in lines if side == a.side and abs(at[j] - c[j]) <= SAME_LINE
                     and abs(at[l] - c[l]) <= SAME_LINE), None)
        if line is None:
            lines.append((a.side, c, [k]))
        else:
            line.append(k)
    tips: dict[int, Vec] = {}
    for side, _, members in lines:
        i = side.axis
        members.sort(key=lambda m: arrivals[m].box[0][i])
        trains = [[members[0]]]
        for m in members[1:]:
            if arrivals[m].box[0][i] - max(arrivals[n].box[1][i] for n in trains[-1]) <= TRAIN_GAP:
                trains[-1].append(m)
            else:
                trains.append([m])
        for train in trains:
            if side.sign > 0:
                k = max(train, key=lambda m: arrivals[m].box[1][i])
                face = arrivals[k].box[1][i] + ARROW_GAP
            else:
                k = min(train, key=lambda m: arrivals[m].box[0][i])
                face = arrivals[k].box[0][i] - ARROW_GAP
            tip = list(_centre(arrivals[k].box))
            tip[i] = face
            tips[k] = (tip[0], tip[1], tip[2])
    return tips


@dataclass(frozen=True)
class _Override:
    side: Side
    line: int  # of the 0 !LC INSERT line


def _overrides(sub: Submodel) -> tuple[dict[int, _Override], list[Issue]]:
    """Reference index -> override for every well-formed `0 !LC INSERT FROM <side>`, and the problems.

    The line belongs to the next reference of its step; comments and other metas may stand between.
    """
    found: dict[int, _Override] = {}
    issues: list[Issue] = []
    usage = "expected '0 !LC INSERT FROM <+X|-X|+Y|-Y|+Z|-Z>'"
    for meta in sub.metas:
        tokens = meta.tokens
        if tokens[:2] != ("!LC", "INSERT"):
            continue
        side = Side.parse(tokens[3]) if len(tokens) == 4 and tokens[2] == "FROM" else None
        if side is None:
            issues.append(Issue("error", "insert-malformed",
                                f"{sub.name} line {meta.line}: {usage}, got '0 {' '.join(tokens)}'"))
        elif meta.next_ref >= len(sub.refs) or sub.refs[meta.next_ref].step != meta.step:
            issues.append(Issue("error", "insert-dangling",
                                f"{sub.name} line {meta.line}: no reference follows in the same step"))
        elif meta.next_ref in found:
            issues.append(Issue("error", "insert-twice", f"{sub.name} line {meta.line}: a second 0 !LC INSERT "
                                                         f"for the reference on line {sub.refs[meta.next_ref].line}"))
        else:
            found[meta.next_ref] = _Override(side, meta.line)
    return found, issues


def _others(i: int) -> tuple[int, int]:
    j, k = [x for x in range(3) if x != i]
    return j, k


def _centre(box: Box) -> Vec:
    lo, hi = box
    return ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)


def _rows(m: tuple[float, ...]) -> Matrix:
    return ((m[0], m[1], m[2]), (m[3], m[4], m[5]), (m[6], m[7], m[8]))


def _hull(boxes: Sequence[tuple[Sequence[float], Sequence[float]]]) -> Box:
    return ((min(b[0][0] for b in boxes), min(b[0][1] for b in boxes), min(b[0][2] for b in boxes)),
            (max(b[1][0] for b in boxes), max(b[1][1] for b in boxes), max(b[1][2] for b in boxes)))


def _clip(spans: Sequence[tuple[float, float]], lo: float, hi: float) -> list[tuple[float, float]]:
    return [(max(a, lo), min(b, hi)) for a, b in spans if min(b, hi) - max(a, lo) > 1]


def _near(box: tuple[Sequence[float], Sequence[float]], i: int, pj: float, pk: float, s0: float, s1: float) -> bool:
    """The box reaches the line along axis i through (pj, pk) within PIN_RADIUS, between s0 and s1."""
    lo, hi = box
    j, k = _others(i)
    return (lo[j] - PIN_RADIUS <= pj <= hi[j] + PIN_RADIUS and lo[k] - PIN_RADIUS <= pk <= hi[k] + PIN_RADIUS
            and hi[i] >= s0 and lo[i] <= s1)


@dataclass(eq=False)
class _Unit:
    """One reference as a rigid body: a part, or a whole sub-assembly in this submodel's axes."""

    index: int
    ref: PartRef
    solids: tuple[Solid, ...]

    @cached_property
    def box(self) -> Box:
        boxes = [s.box for s in self.solids if s.shaped]
        return _hull(boxes) if boxes else (self.ref.pos, self.ref.pos)

    def extent(self, i: int) -> float:
        return self.box[1][i] - self.box[0][i]

    @property
    def is_pin(self) -> bool:
        return len(self.solids) == 1 and self.solids[0].part in PIN_LIKE

    @property
    def is_flexible(self) -> bool:
        return len(self.solids) == 1 and self.solids[0].part in FLEXIBLE


@dataclass(frozen=True)
class _Joint:
    """A pin or axle running through material, between the unit being placed (own) and a placed unit."""

    solid: int  # position of the own solid in its unit
    own: Solid
    other: Solid
    partner: int  # reference index of the placed unit
    axis: int
    line: tuple[float, float]  # the pin's line: its other two coordinates, ascending axis order
    own_span: tuple[float, float]
    partner_span: tuple[float, float]
    own_pin: bool  # the own solid is the pin; otherwise it slides onto the partner's pin


@dataclass(frozen=True)
class _Guess:
    unit: int
    side: Side
    rule: Rule
    travel: float
    partners: tuple[int, ...]
    blocked_by: int | None
    note: str = ""


def _flatten(doc: Document, ref: PartRef, index: int, shapes: Shapes) -> tuple[Solid, ...]:
    if ref.name not in doc.models:
        pid = part_id(ref.name)
        return (Solid(f"{pid}#{index}", pid, ref.name, _rows(ref.matrix), ref.pos, shapes),)
    out: list[Solid] = []

    def walk(name: str, rot: Matrix, pos: Vec, prefix: str) -> None:
        for k, r in enumerate(doc.models[name].refs):
            m, p = compose(rot, _rows(r.matrix)), apply(rot, pos, r.pos)
            if r.name in doc.models:
                walk(r.name, m, p, f"{prefix}{r.name}#{k}/")
            else:
                pid = part_id(r.name)
                out.append(Solid(f"{prefix}{pid}#{k}", pid, r.name, m, p, shapes))

    walk(ref.name, _rows(ref.matrix), ref.pos, f"{ref.name}#{index}/")
    return tuple(out)


def _pair_joints(a: _Unit, b: _Unit) -> list[_Joint]:
    """Joints of unit a with unit b, either one holding the pin. They do not depend on what else is placed."""
    out: list[_Joint] = []
    for n, s in enumerate(a.solids):
        if not s.shaped:
            continue
        if s.part in PIN_LIKE:
            i = s.axis(0)
            if i is None:
                continue
            j, k = _others(i)
            s0, s1 = s.ends(i)
            for q in b.solids:
                if q.part in PIN_LIKE or not _near(q.box, i, s.pos[j], s.pos[k], s0, s1):
                    continue
                if covered := _clip(q.material(i, s.pos[j], s.pos[k], PIN_RADIUS), s0, s1):
                    out.append(_Joint(n, s, q, b.index, i, (s.pos[j], s.pos[k]), (s0, s1),
                                      (min(c[0] for c in covered), max(c[1] for c in covered)), True))
        else:
            for q in b.solids:
                if q.part not in PIN_LIKE or not q.shaped or (i := q.axis(0)) is None:
                    continue
                j, k = _others(i)
                q0, q1 = q.ends(i)
                if not _near(s.box, i, q.pos[j], q.pos[k], q0, q1):
                    continue
                if _clip(s.material(i, q.pos[j], q.pos[k], PIN_RADIUS), q0, q1):
                    out.append(_Joint(n, s, q, b.index, i, (q.pos[j], q.pos[k]), (s.box[0][i], s.box[1][i]),
                                      (q0, q1), False))
    return out


class _Build:
    """One submodel's references as units. Earlier means an earlier step of this submodel, or earlier in the
    sequence planned for the same step; parts of other submodels never count."""

    def __init__(self, doc: Document, sub: Submodel, shapes: Shapes) -> None:
        self.units = [_Unit(i, ref, _flatten(doc, ref, i, shapes)) for i, ref in enumerate(sub.refs)]
        self._owner = {id(s): u.index for u in self.units for s in u.solids}
        self._pairs: dict[tuple[int, int], list[_Joint]] = {}

    def label(self, index: int) -> str:
        ref = self.units[index].ref
        return f"{part_id(ref.name)} (line {ref.line})"

    def plan_step(self, step: int, overrides: Mapping[int, Side]) -> dict[int, Insertion]:
        """The step's references with sides, waves and travel. Depends on earlier steps as a set of parts only,
        so a step can be planned alone."""
        placed = [u for u in self.units if u.ref.step < step]
        fresh = [u for u in self.units if u.ref.step == step]
        order = self._repair(self._sequence(fresh, placed, overrides), placed, overrides)
        wave: dict[int, int] = {}
        for g in order:
            wave[g.unit] = max((wave[p] + 1 for p in g.partners if p in wave), default=0)
        # One wave coming from one side travels as far as its furthest part, so a train slides on together.
        longest: dict[tuple[int, Side], float] = {}
        for g in order:
            key = (wave[g.unit], g.side)
            longest[key] = max(longest.get(key, 0.0), g.travel)
        return {g.unit: Insertion(g.side, longest[(wave[g.unit], g.side)], wave[g.unit], n, g.rule, g.partners,
                                  g.blocked_by, self.units[g.unit].box, g.note)
                for n, g in enumerate(order)}

    def _sequence(self, fresh: Sequence[_Unit], placed: Sequence[_Unit],
                  overrides: Mapping[int, Side]) -> list[_Guess]:
        """Each round puts in the unit that ranks first against what is in place by then."""
        placed = list(placed)
        remaining = list(fresh)
        order: list[_Guess] = []
        while remaining:
            guesses = {u.index: self._guess(u, placed, overrides.get(u.index)) for u in remaining}
            pick = min(remaining, key=lambda u: _rank(u, guesses[u.index]))
            order.append(guesses[pick.index])
            placed.append(pick)
            remaining.remove(pick)
        return order

    def _replay(self, sequence: Sequence[int], placed: Sequence[_Unit],
                overrides: Mapping[int, Side]) -> list[_Guess]:
        placed = list(placed)
        out = []
        for index in sequence:
            out.append(self._guess(self.units[index], placed, overrides.get(index)))
            placed.append(self.units[index])
        return out

    def _repair(self, order: list[_Guess], placed: Sequence[_Unit], overrides: Mapping[int, Side]) -> list[_Guess]:
        """Moves a blocked unit to just before the first new part it joins, while that leaves fewer units blocked:
        a bush shut in between two parts goes on before the axle that runs through it."""
        for _ in range(len(order)):
            stuck = [g for g in order if g.blocked_by is not None]
            sequence = [g.unit for g in order]
            for g in stuck:
                before = [sequence.index(p) for p in g.partners if p in sequence]
                if not before:
                    continue
                trial = [u for u in sequence if u != g.unit]
                trial.insert(min(before), g.unit)
                replayed = self._replay(trial, placed, overrides)
                if sum(r.blocked_by is not None for r in replayed) < len(stuck):
                    order = replayed
                    break
            else:
                return order
        return order

    def _joints(self, unit: _Unit, placed: Sequence[_Unit]) -> list[_Joint]:
        out: list[_Joint] = []
        for p in placed:
            key = (unit.index, p.index)
            if key not in self._pairs:
                self._pairs[key] = _pair_joints(unit, p)
            out += self._pairs[key]
        out.sort(key=lambda jt: jt.solid)
        return out

    def _guess(self, unit: _Unit, placed: Sequence[_Unit], override: Side | None) -> _Guess:
        solids = [s for p in placed for s in p.solids]
        joints = self._joints(unit, placed)
        pins = [s for s in solids if s.part in PIN_LIKE]
        skip = set()
        for jt in joints:
            if not jt.own_pin:
                j, k = _others(jt.axis)
                skip |= {p.label for p in pins if p.axis(0) == jt.axis and abs(p.pos[j] - jt.line[0]) < 1
                         and abs(p.pos[k] - jt.line[1]) < 1}
        built = _centre(_hull([p.box for p in placed]) if placed else unit.box)

        if override is not None:
            on_axis = [jt for jt in joints if jt.axis == override.axis]
            across = [jt for jt in joints if jt.axis != override.axis]
            partners = tuple(sorted({jt.partner for jt in on_axis}))
            travel = _joint_travel(on_axis) if on_axis else max(MIN_TRAVEL, unit.extent(override.axis) + MARGIN)
            if across:
                return _Guess(unit.index, override, "override", travel, partners, across[0].partner,
                              f"held along {'XYZ'[across[0].axis]} by {self.label(across[0].partner)}")
            hit = _in_the_way(unit, solids, override, travel, joints, skip)
            return _Guess(unit.index, override, "override", travel, partners, self._owner_of(hit))

        # Before joints: a band stretched over pins is not pushed along them, and nothing stops it.
        if unit.is_flexible:
            return _Guess(unit.index, FROM_ABOVE, "flexible", max(MIN_TRAVEL, unit.extent(1) + MARGIN), (), None)

        if joints:
            counted: set[tuple[int, int]] = set()
            axes: Counter[int] = Counter()
            for jt in joints:
                key = (jt.solid, -1 if jt.own_pin else id(jt.other))
                if key not in counted:
                    counted.add(key)
                    axes[jt.axis] += 1
            i = axes.most_common(1)[0][0]
            on_axis = [jt for jt in joints if jt.axis == i]
            own = (min(jt.own_span[0] for jt in on_axis), max(jt.own_span[1] for jt in on_axis))
            held = (min(jt.partner_span[0] for jt in on_axis), max(jt.partner_span[1] for jt in on_axis))
            # A pin is pushed from the side it sticks out on; a part going onto pins sits at their free tips.
            beyond = (own[0] + own[1]) / 2 - (held[0] + held[1]) / 2
            note = ""
            if abs(beyond) <= 1:
                beyond = _centre(unit.box)[i] - built[i]
                note = "tie: away from what is built" if abs(beyond) > 1 else f"tie: from -{'XYZ'[i]}"
            first = Side(i, 1 if beyond > 1 else -1)
            partners = tuple(sorted({jt.partner for jt in on_axis}))
            travel = _joint_travel(on_axis)
            hit = _in_the_way(unit, solids, first, travel, joints, skip)
            if hit is None:
                return _Guess(unit.index, first, "joint", travel, partners, None, note)
            second = Side(i, -first.sign)
            if _in_the_way(unit, solids, second, travel, joints, skip) is None:
                return _Guess(unit.index, second, "joint", travel, partners, None,
                              f"{first.name} runs into {self.label(self._owner[id(hit)])}")
            return _Guess(unit.index, first, "joint", travel, partners, self._owner_of(hit), note)

        centre = _centre(unit.box)
        outward = sorted(HORIZONTAL, key=lambda s: -(centre[s.axis] - built[s.axis]) * s.sign)
        above: Solid | None = None
        for side in (FROM_ABOVE, *outward, FROM_BELOW):
            travel = max(MIN_TRAVEL, unit.extent(side.axis) + MARGIN)
            hit = _in_the_way(unit, solids, side, travel, (), set())
            if hit is None:
                note = "" if above is None else f"from above runs into {self.label(self._owner[id(above)])}"
                return _Guess(unit.index, side, "free", travel, (), None, note)
            above = above or hit
        return _Guess(unit.index, FROM_ABOVE, "fallback", max(MIN_TRAVEL, unit.extent(1) + MARGIN), (),
                      self._owner_of(above), "every side is blocked")

    def _owner_of(self, solid: Solid | None) -> int | None:
        return None if solid is None else self._owner[id(solid)]


def _joint_travel(joints: Sequence[_Joint]) -> float:
    lo = min(min(jt.own_span[0], jt.partner_span[0]) for jt in joints)
    hi = max(max(jt.own_span[1], jt.partner_span[1]) for jt in joints)
    return max(MIN_TRAVEL, hi - lo + MARGIN)


def _rank(unit: _Unit, g: _Guess) -> tuple[int, float, int]:
    """Pins into what holds them first, then what goes onto them, then clear drops from the bottom up."""
    clear = g.blocked_by is None
    if clear and g.partners:
        rank = 0 if unit.is_pin else 1
    elif clear and g.side == FROM_ABOVE and g.rule != "joint":
        rank = 2
    elif not unit.is_pin and g.rule != "joint":
        rank = 3
    elif not unit.is_pin:
        rank = 4
    else:
        rank = 5
    return (rank, -unit.box[1][1] if rank == 2 else 0.0, unit.index)


def _in_the_way(unit: _Unit, solids: Sequence[Solid], side: Side, travel: float, joints: Sequence[_Joint],
                skip: set[str]) -> Solid | None:
    """First placed solid in the way when the unit leaves its place towards `side` for `travel` LDU.

    Rays run along the side's axis only: from the ends of its own pins, along the pins it slides on (those pins
    skipped), and from five points of the box face of each of its other parts.
    """
    i, d = side.axis, side.sign
    for jt in joints:
        if jt.axis != i:
            continue
        if jt.own_pin:
            start = jt.own_span[1] if d > 0 else jt.own_span[0]
            hit = first_blocker(solids, i, *jt.line, start, d, reach=travel)
        else:
            start = jt.own.box[1][i] if d > 0 else jt.own.box[0][i]
            hit = first_blocker(solids, i, *jt.line, start, d, reach=travel, skip=skip)
        if hit is not None:
            return hit
    j, k = _others(i)
    for s in unit.solids:
        if s.part in PIN_LIKE or not s.shaped:
            continue
        lo, hi = s.box
        start = hi[i] if d > 0 else lo[i]
        cj, ck = (lo[j] + hi[j]) / 2, (lo[k] + hi[k]) / 2
        hj, hk = (hi[j] - lo[j]) / 2, (hi[k] - lo[k]) / 2
        for a, b in FACE_SAMPLES:
            hit = first_blocker(solids, i, cj + a * hj, ck + b * hk, start, d, reach=travel, skip=skip)
            if hit is not None:
                return hit
    return None
