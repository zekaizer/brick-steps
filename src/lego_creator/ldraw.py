"""LDraw MPD/LDR parsing, submodel flattening and parts-library lookup."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

INHERIT_COLOR = 16
STEP_METAS = {"STEP", "ROTSTEP"}
# Type 0 keywords that are commands, not a model title.
COMMAND_METAS = {"BFC", "ROTATION", "CLEAR", "PAUSE", "SAVE", "PRINT", "WRITE"}


def normalize_name(name: str) -> str:
    return name.strip().replace("\\", "/").lower()


def part_id(name: str) -> str:
    name = normalize_name(name)
    return name.removesuffix(".dat")


@dataclass(frozen=True)
class PartRef:
    color: int
    pos: tuple[float, float, float]
    matrix: tuple[float, ...]
    name: str
    line: int = field(default=0, compare=False)
    # 0-based index of the build step this reference belongs to within its submodel
    step: int = field(default=0, compare=False)


@dataclass(frozen=True)
class Meta:
    """A `0 !...` line where it stands in its submodel."""

    tokens: tuple[str, ...]  # from the "!" keyword on
    line: int  # 1-based line number in the file
    step: int  # 0-based build step, counted like PartRef.step
    next_ref: int  # index in Submodel.refs of the first reference after it; len(refs) when none follows


@dataclass
class Submodel:
    name: str
    refs: list[PartRef] = field(default_factory=list)
    metas: list[Meta] = field(default_factory=list)
    steps: int = 0
    title: str = ""


@dataclass
class Document:
    models: dict[str, Submodel]
    # (submodel name, 1-based line number, message) for lines that could not be parsed
    errors: list[tuple[str, int, str]] = field(default_factory=list)

    @property
    def main(self) -> Submodel:
        return next(iter(self.models.values()))


def _parse_color(token: str) -> int:
    """LDConfig code or a direct color (0x2RRGGBB)."""
    return int(token, 16) if token.lower().startswith("0x") else int(token)


# line type -> number of numeric fields after the color
GEOMETRY_FIELDS = {2: 6, 3: 9, 4: 12, 5: 12}


def _parse_type1(tokens: list[str], lineno: int, step: int = 0) -> PartRef:
    if len(tokens) < 15:
        raise ValueError(f"type 1 line needs color, 12 numbers and a file name, got {len(tokens) - 1} fields")
    nums = [float(t) for t in tokens[2:14]]
    return PartRef(
        color=_parse_color(tokens[1]),
        pos=(nums[0], nums[1], nums[2]),
        matrix=tuple(nums[3:12]),
        name=normalize_name(" ".join(tokens[14:])),
        line=lineno,
        step=step,
    )


def _check_geometry_line(tokens: list[str]) -> None:
    kind = int(tokens[0])
    expected = GEOMETRY_FIELDS[kind] + 2
    if len(tokens) != expected:
        raise ValueError(f"type {kind} line needs {expected - 1} fields, got {len(tokens) - 1}")
    _parse_color(tokens[1])
    for t in tokens[2:]:
        float(t)


def parse(text: str, default_name: str = "main.ldr") -> Document:
    """Parse LDR or MPD text. The first model in the document is the main model."""
    models: dict[str, Submodel] = {}
    current: Submodel | None = None
    is_mpd = any(line.split()[:2] == ["0", "FILE"] for line in text.splitlines() if line.strip())
    if not is_mpd:
        current = models.setdefault(default_name, Submodel(default_name))

    errors: list[tuple[str, int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        tokens = raw.split()
        if not tokens:
            continue
        if tokens[0] == "0" and len(tokens) >= 3 and tokens[1] == "FILE":
            name = normalize_name(raw.split(None, 2)[2])
            current = models.setdefault(name, Submodel(name))
            continue
        if tokens[:2] == ["0", "NOFILE"]:
            current = None
            continue
        if current is None:
            continue
        if tokens[0] == "0":
            pass
        elif tokens[0] not in ("1", "2", "3", "4", "5"):
            errors.append((current.name, lineno, f"unknown line type {tokens[0]!r}"))
            continue
        else:
            try:
                if tokens[0] == "1":
                    current.refs.append(_parse_type1(tokens, lineno, current.steps))
                else:
                    _check_geometry_line(tokens)
            except ValueError as e:
                errors.append((current.name, lineno, str(e)))
            continue
        if len(tokens) >= 2:
            if tokens[1] in STEP_METAS:
                current.steps += 1
            elif tokens[1].startswith("!"):
                current.metas.append(Meta(tuple(tokens[1:]), lineno, current.steps, len(current.refs)))
            elif (
                not current.title
                and tokens[1] not in COMMAND_METAS
                and not tokens[1].startswith("//")
                and not tokens[1].endswith(":")
            ):
                current.title = raw.split(None, 1)[1].strip()

    if not models:
        models[default_name] = Submodel(default_name)
    return Document(models=models, errors=errors)


def step_groups(sub: Submodel) -> list[list[PartRef]]:
    """References grouped by build step, numbered like LeoCAD/LPub3D.

    There is one group per `0 STEP` marker, plus one more if references follow the last marker.
    """
    count = sub.steps + (1 if any(r.step == sub.steps for r in sub.refs) else 0)
    groups: list[list[PartRef]] = [[] for _ in range(count)]
    for ref in sub.refs:
        groups[ref.step].append(ref)
    return groups


def flatten(doc: Document) -> Counter[tuple[str, int]]:
    """Expand submodel references into a (part_id, color) count of library parts.

    Raises ValueError on a submodel reference cycle.
    """
    bom: Counter[tuple[str, int]] = Counter()

    def walk(sub: Submodel, parent_color: int, stack: tuple[str, ...]) -> None:
        if sub.name in stack:
            raise ValueError(f"submodel cycle: {' -> '.join((*stack, sub.name))}")
        for ref in sub.refs:
            color = parent_color if ref.color == INHERIT_COLOR else ref.color
            child = doc.models.get(ref.name)
            if child is not None:
                walk(child, color, (*stack, sub.name))
            else:
                bom[(part_id(ref.name), color)] += 1

    walk(doc.main, INHERIT_COLOR, ())
    return bom


class Library:
    """Read-only view of LDraw parts libraries, each rooted at a directory holding parts/.

    Earlier roots win on name clashes, so custom roots cannot shadow official parts.
    """

    def __init__(self, *roots: Path) -> None:
        self.roots = roots

    @cached_property
    def _index(self) -> dict[str, Path]:
        index: dict[str, Path] = {}
        for root in self.roots:
            parts = root / "parts"
            if parts.is_dir():
                for p in parts.iterdir():
                    if p.suffix.lower() == ".dat":
                        index.setdefault(p.name.lower(), p)
        return index

    def find(self, pid: str) -> Path | None:
        return self._index.get(f"{part_id(pid)}.dat")

    def title(self, pid: str) -> str | None:
        path = self.find(pid)
        if path is None:
            return None
        with path.open(encoding="utf-8", errors="replace") as f:
            first = f.readline().strip()
        return first.removeprefix("0 ")

    def colors(self) -> set[int] | None:
        """Color codes from the first root's LDConfig.ldr, or None if no root has one."""
        for root in self.roots:
            config = root / "LDConfig.ldr"
            if config.is_file():
                text = config.read_text(encoding="utf-8", errors="replace")
                return {int(m) for m in re.findall(r"^0\s+!COLOUR\s+\S+\s+CODE\s+(\d+)", text, re.MULTILINE)}
        return None

    def moved_to(self, pid: str) -> str | None:
        title = self.title(pid)
        if title is None or not title.startswith("~Moved to "):
            return None
        return part_id(title.removeprefix("~Moved to "))
