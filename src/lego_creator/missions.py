"""Missions: SPIKE App word blocks a child places after building a model (ADR 0003).

`models/<slug>/missions.yaml` is a list of missions:

    - title: 앞뒤로 달리기
      goal: 앞으로 갔다가 돌아와요.
      blocks:
      - [when_program_starts]
      - [set_movement_motors, A, B]
      - [repeat, 2, [[move_for, forward, 2, rotations], [move_for, backward, 2, rotations]]]
      try: 2를 3으로 바꾸면 어떻게 될까요?

A block is its id followed by its arguments; a C-shaped block (repeat) takes its inner blocks
as a last, nested list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import escape

from .report import Issue

PORTS = frozenset("ABCDEF")
# What each argument kind accepts and how it is shown inside the block.
CHOICES = {
    "direction": {"forward": "↑", "backward": "↓", "clockwise": "↻", "counterclockwise": "↺"},
    "spin": {"clockwise": "↻", "counterclockwise": "↺"},
    "unit": {"rotations": "회전", "degrees": "도", "seconds": "초", "cm": "cm"},
}


@dataclass(frozen=True)
class Block:
    category: str  # events, movement, motors, control: the app's palette, drawn in its color
    template: str  # Korean wording; {0}, {1} ... are the argument slots
    kinds: tuple[str, ...] = ()  # port, number, direction, spin, unit
    joined: bool = False  # all arguments share slot {0}, joined with "+" (motor pairs)
    c_shape: bool = False  # holds inner blocks
    checked: bool = False  # wording compared with the SPIKE App on an iPad


# The Korean wording must match the SPIKE App word for word. `checked` blocks were compared with
# a photo of the app (2026-11-22); the rest are guesses, and `lc validate` warns when a mission
# uses one. The app calls the movement palette 동작.
BLOCKS: dict[str, Block] = {
    "when_program_starts": Block("events", "프로그램이 시작될 때", checked=True),
    "set_movement_motors": Block("movement", "동작 모터를 {0}(으)로 정하기", ("port", "port"), joined=True, checked=True),
    "set_movement_speed": Block("movement", "동작 속도를 {0}%로 정하기", ("number",), checked=True),
    # The photo shows "↑ 방향으로 10 회전 만큼 움…"; the last word is cut off.
    "move_for": Block("movement", "{0} 방향으로 {1} {2} 만큼 움직이기", ("direction", "number", "unit")),
    "start_moving": Block("movement", "{0} 방향으로 동작 시작하기", ("direction",), checked=True),
    "stop_moving": Block("movement", "이동 멈추기", checked=True),
    # The photo shows "A 모터 ↻ 방향으로 1 …"; the rest is cut off.
    "run_motor_for": Block("motors", "{0} 모터 {1} 방향으로 {2} {3} 만큼 움직이기", ("port", "spin", "number", "unit")),
    "wait": Block("control", "{0}초 기다리기", ("number",)),
    "repeat": Block("control", "{0}번 반복하기", ("number",), c_shape=True),
}


@dataclass(frozen=True)
class BlockUse:
    block: str
    args: tuple = ()
    body: tuple = ()


@dataclass(frozen=True)
class Mission:
    title: str
    goal: str
    blocks: tuple[BlockUse, ...] = field(default_factory=tuple)
    try_: str = ""


def _block(item: object) -> BlockUse | None:
    if not isinstance(item, list) or not item or not isinstance(item[0], str):
        return None
    args = list(item[1:])
    body: tuple = ()
    if args and isinstance(args[-1], list):
        inner = [_block(b) for b in args.pop()]
        if any(b is None for b in inner):
            return None
        body = tuple(inner)
    return BlockUse(item[0], tuple(args), body)


def parse_missions(data: object) -> tuple[list[Mission], list[Issue]]:
    if not isinstance(data, list):
        return [], [Issue("error", "mission-malformed", "missions.yaml must be a list of missions")]
    missions, issues = [], []
    for k, item in enumerate(data, 1):
        blocks = [_block(b) for b in item.get("blocks") or []] if isinstance(item, dict) else []
        if not isinstance(item, dict) or not item.get("title") or not blocks or None in blocks:
            issues.append(Issue("error", "mission-malformed",
                                f"mission {k} needs a title and a list of blocks, each a list starting with a block id"))
            continue
        missions.append(Mission(str(item["title"]), str(item.get("goal", "")), tuple(blocks), str(item.get("try", ""))))
    return missions, issues


def _walk(blocks: tuple[BlockUse, ...]):
    for b in blocks:
        yield b
        yield from _walk(b.body)


def _arg_ok(kind: str, value: object) -> bool:
    if kind == "port":
        return isinstance(value, str) and value in PORTS
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, str) and value in CHOICES[kind]


def mission_ports(mission: Mission) -> set[str]:
    return {a for b in _walk(mission.blocks) if b.block in BLOCKS
            for kind, a in zip(BLOCKS[b.block].kinds, b.args) if kind == "port" and isinstance(a, str)}


def check_missions(missions: list[Mission], declared: set[str]) -> list[Issue]:
    issues = []
    for m in missions:
        for b in _walk(m.blocks):
            spec = BLOCKS.get(b.block)
            if spec is None:
                issues.append(Issue("error", "block-unknown", f"{m.title}: no block called {b.block}"))
                continue
            if (len(b.args) != len(spec.kinds) or not all(map(_arg_ok, spec.kinds, b.args))
                    or (b.body and not spec.c_shape)):
                wanted = ", ".join(spec.kinds) or "no arguments"
                issues.append(Issue("error", "block-args", f"{m.title}: {b.block} takes {wanted}, got {list(b.args)}"))
        unchecked = sorted({b.block for b in _walk(m.blocks) if b.block in BLOCKS and not BLOCKS[b.block].checked})
        if unchecked:
            issues.append(Issue("warning", "block-wording-unchecked",
                                f"{m.title}: wording of {', '.join(unchecked)} not yet compared with the SPIKE App"))
        extra = sorted(mission_ports(m) - declared)
        if extra:
            issues.append(Issue("error", "mission-port-undeclared",
                                f"{m.title}: uses port {', '.join(extra)} without a `0 !LC PORT` line in the model"))
    return issues


def _shown(kind: str, value: object) -> str:
    if kind in CHOICES:
        return CHOICES[kind].get(str(value), str(value))
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _wording(b: BlockUse) -> str:
    spec = BLOCKS[b.block]
    slots = [_shown(k, a) for k, a in zip(spec.kinds, b.args)]
    menus = [k != "number" for k in spec.kinds]
    if spec.joined:
        slots, menus = ["+".join(slots)], [any(menus)]

    def slot(m: re.Match) -> str:
        k = int(m.group(1))
        if menus[k]:  # the app draws a choice as a dropdown in a darker shade of the block
            return f'<span class="slot menu">{escape(slots[k])} ▾</span>'
        return f'<span class="slot">{escape(slots[k])}</span>'

    return re.sub(r"\{(\d+)\}", slot, escape(spec.template, quote=False))


def blocks_html(blocks: tuple[BlockUse, ...]) -> str:
    """The blocks as nested lists, one item per block, colored by category in CSS."""
    return f'<ol class="blocks">{_items(blocks)}</ol>'


def _items(blocks: tuple[BlockUse, ...]) -> str:
    items = []
    for b in blocks:
        spec = BLOCKS[b.block]
        cls = f"block {spec.category}" + (" c" if spec.c_shape else "")
        inner = f'<ol class="repeat-body">{_items(b.body)}</ol>' if spec.c_shape else ""
        items.append(f'<li class="{cls}" data-block="{b.block}"><span class="block-text t-button">{_wording(b)}</span>{inner}</li>')
    return "".join(items)
