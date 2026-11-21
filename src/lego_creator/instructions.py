"""Turn a parsed model into an instruction plan: sections, steps and the parts each step adds."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .ldraw import Document, Library, Submodel, part_id, step_groups


@dataclass(frozen=True)
class StepItem:
    part: str  # LDraw part id, or a submodel name when is_submodel
    color: int
    qty: int
    is_submodel: bool = False


@dataclass
class Step:
    number: int  # 1-based, LeoCAD step number within the section's submodel
    items: list[StepItem] = field(default_factory=list)


@dataclass
class Section:
    submodel: str
    title: str
    steps: list[Step] = field(default_factory=list)


def _section_order(doc: Document) -> list[Submodel]:
    """Submodels used by the main model, each after the submodels it uses (post-order, first use)."""
    seen: set[str] = set()
    order: list[Submodel] = []

    def visit(sub: Submodel) -> None:
        if sub.name in seen:
            return
        seen.add(sub.name)
        for ref in sub.refs:
            child = doc.models.get(ref.name)
            if child is not None:
                visit(child)
        order.append(sub)

    visit(doc.main)
    return order


def _items(doc: Document, refs: list) -> list[StepItem]:
    counts: dict[tuple[str, int, bool], int] = {}
    for ref in refs:
        is_sub = ref.name in doc.models
        key = (ref.name if is_sub else part_id(ref.name), ref.color, is_sub)
        counts[key] = counts.get(key, 0) + 1
    return [StepItem(part, color, qty, is_sub) for (part, color, is_sub), qty in counts.items()]


def plan(doc: Document) -> list[Section]:
    """Sections in build order (sub-assemblies first, main model last); steps that add nothing are dropped."""
    sections = []
    for sub in _section_order(doc):
        steps = [Step(i + 1, _items(doc, refs)) for i, refs in enumerate(step_groups(sub)) if refs]
        sections.append(Section(sub.name, sub.title or sub.name, steps))
    return sections


def _custom_parts(doc: Document, library: Library, custom_root: Path) -> list[tuple[str, Path]]:
    root = custom_root.resolve()
    found: dict[str, Path] = {}
    for sub in doc.models.values():
        for ref in sub.refs:
            if ref.name in doc.models or ref.name in found:
                continue
            path = library.find(ref.name)
            if path is not None and path.resolve().is_relative_to(root):
                found[ref.name] = path
    return list(found.items())


def build_mpd(text: str, doc: Document, library: Library, custom_root: Path) -> str:
    """The model as one MPD with every custom part it uses embedded as a `0 FILE` block.

    Renderers then need only the official library.
    """
    out = text if text.endswith("\n") else text + "\n"
    if not any(line.split()[:2] == ["0", "FILE"] for line in text.splitlines()):
        out = f"0 FILE {doc.main.name}\n" + out
    parts = _custom_parts(doc, library, custom_root)
    for name, path in parts:
        out += f"0 NOFILE\n0 FILE {name}\n{path.read_text(encoding='utf-8').rstrip()}\n"
    if parts:
        out += "0 NOFILE\n"
    return out
