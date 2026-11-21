"""Cables from hub ports to devices, for the manual's cable step (`0 !LC PORT` lines).

The n-th `0 !LC PORT` line naming a part belongs to the n-th placement of that part in the
same submodel, in file order.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ldraw import Document, PartRef, part_id
from .ports import DEVICES, parse_ports

Point = tuple[float, float, float]

HUB_PARTS = frozenset({"45601c01", "45601"})
# Where a plug enters each port, in the frame of hub 45601c01 (bottom center origin, USB and the
# Bluetooth button at +Z, the Bluetooth button on the +X side). The six port sockets (23807) sit on
# the long sides at x ±70, y -68, z -40/0/40. The letters come from a photo of a real hub
# (2026-11-22): with the Bluetooth button end up, A/C/E run down the left side and B/D/F down the
# right, so A/C/E are on -X and A/B are at the Bluetooth end.
HUB_PORT_POINTS: dict[str, Point] = {
    "A": (-70, -68, 40), "B": (70, -68, 40),
    "C": (-70, -68, 0), "D": (70, -68, 0),
    "E": (-70, -68, -40), "F": (70, -68, -40),
}
# Where the cable leaves a device, in the device's frame. The large motor's coiled cable starts at
# (0, 14, 142) in 54675c01 and the housing ends at z 150. Devices not listed use their origin.
CABLE_EXIT: dict[str, Point] = {"54675": (0, 14, 150), "54675c01": (0, 14, 150)}
LABELS = {"large_motor": "큰 모터", "medium_motor": "중간 모터", "color_sensor": "컬러 센서",
          "distance_sensor": "거리 센서", "force_sensor": "힘 센서", "lms_esp32": "보드"}


@dataclass(frozen=True)
class Cable:
    port: str
    part: str
    color: int
    label: str
    device_point: Point
    hub_point: Point | None
    hub_out: Point | None = None  # direction the port faces, out of the hub


@dataclass(frozen=True)
class CablePlan:
    submodel: str
    after_step: int  # 0-based build step of `submodel` after which the cables go in
    shown: int  # references of `submodel` visible at that step
    cables: list[Cable] = field(default_factory=list)
    keep: list[int] = field(default_factory=list)  # indices into the submodel's references that stay solid


def _turn(ref: PartRef, v: Point) -> Point:
    a, b, c, d, e, f, g, h, i = ref.matrix
    return (a * v[0] + b * v[1] + c * v[2], d * v[0] + e * v[1] + f * v[2], g * v[0] + h * v[1] + i * v[2])


def _place(ref: PartRef, local: Point) -> Point:
    a, b, c, d, e, f, g, h, i = ref.matrix
    x, y, z = local
    px, py, pz = ref.pos
    return (px + a * x + b * y + c * z, py + d * x + e * y + f * z, pz + g * x + h * y + i * z)


def _sided(cables: list[Cable]) -> list[Cable]:
    """Tell same-named devices apart by side: +X is the model's right (see the ldraw-spike skill)."""
    labels = [c.label for c in cables]
    out = []
    for c in cables:
        if labels.count(c.label) > 1 and abs(c.device_point[0]) > 10:
            c = Cable(c.port, c.part, c.color, ("오른쪽 " if c.device_point[0] > 0 else "왼쪽 ") + c.label,
                      c.device_point, c.hub_point, c.hub_out)
        out.append(c)
    return out


def cable_plan(doc: Document) -> CablePlan | None:
    """Cables of the first submodel that declares ports; None when no submodel does."""
    assignments, _ = parse_ports(doc)
    for sub in doc.models.values():
        mine = [a for a in assignments if a.submodel == sub.name]
        if not mine:
            continue
        placed: dict[str, list[PartRef]] = {}
        for ref in sub.refs:
            placed.setdefault(part_id(ref.name), []).append(ref)
        hub = next((r for r in sub.refs if part_id(r.name) in HUB_PARTS), None)
        used, cables, last = {}, [], hub.step if hub else 0
        keep = {sub.refs.index(hub)} if hub else set()
        for a in mine:
            k = used.get(a.part, 0)
            used[a.part] = k + 1
            refs = placed.get(a.part, [])
            if k >= len(refs):
                continue  # lc validate reports port-device-missing
            ref = refs[k]
            last = max(last, ref.step)
            keep.add(next(i for i, r in enumerate(sub.refs) if r is ref))
            cables.append(Cable(
                a.port, a.part, ref.color, LABELS.get(DEVICES.get(a.part, ""), a.part),
                _place(ref, CABLE_EXIT.get(a.part, (0, 0, 0))),
                _place(hub, HUB_PORT_POINTS[a.port]) if hub and a.port in HUB_PORT_POINTS else None,
                _turn(hub, (-1 if a.port in "ACE" else 1, 0, 0)) if hub else None,
            ))
        if cables:
            return CablePlan(sub.name, last, sum(r.step <= last for r in sub.refs), _sided(cables), sorted(keep))
    return None
