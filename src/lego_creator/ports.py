"""Hub port assignments declared in LDraw as `0 !LC PORT <A-F> <part> <role>`."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .ldraw import Document, part_id
from .report import Issue

PORTS = frozenset("ABCDEF")

# LDraw part id -> device kind. Bare and cabled (c01) variants are both listed.
DEVICES: dict[str, str] = {
    **dict.fromkeys(("54675", "54675c01", "69730", "69730c01"), "large_motor"),
    **dict.fromkeys(("54696p01", "54696p01c01"), "medium_motor"),
    **dict.fromkeys(("37308", "37308c01"), "color_sensor"),
    **dict.fromkeys(("37316", "37316c01"), "distance_sensor"),
    **dict.fromkeys(("37312", "37312c01"), "force_sensor"),
    "lms-esp32v2": "lms_esp32",  # custom part, custom/parts/
}


@dataclass(frozen=True)
class PortAssignment:
    port: str
    part: str
    role: str


def parse_ports(doc: Document) -> tuple[list[PortAssignment], list[Issue]]:
    assignments: list[PortAssignment] = []
    issues: list[Issue] = []
    for sub in doc.models.values():
        for meta in sub.metas:
            if meta[:2] != ["!LC", "PORT"]:
                continue
            if len(meta) != 5:
                issues.append(
                    Issue("error", "port-malformed", f"{sub.name}: expected '0 !LC PORT <A-F> <part> <role>', got '0 {' '.join(meta)}'")
                )
                continue
            assignments.append(PortAssignment(meta[2].upper(), part_id(meta[3]), meta[4]))
    return assignments, issues


def check_ports(assignments: list[PortAssignment], bom: Counter[tuple[str, int]]) -> list[Issue]:
    issues: list[Issue] = []
    present: Counter[str] = Counter()
    for (pid, _), n in bom.items():
        present[pid] += n

    seen: set[str] = set()
    for a in assignments:
        if a.port not in PORTS:
            issues.append(Issue("error", "port-invalid", f"port {a.port} ({a.role}) is not one of A-F"))
        elif a.port in seen:
            issues.append(Issue("error", "port-duplicate", f"port {a.port} assigned more than once"))
        seen.add(a.port)
        if a.part not in DEVICES:
            issues.append(Issue("error", "port-not-device", f"port {a.port}: {a.part} is not a hub device"))

    assigned = Counter(a.part for a in assignments if a.part in DEVICES)
    for pid, n in sorted(assigned.items()):
        if n > present[pid]:
            issues.append(
                Issue("error", "port-device-missing", f"{pid}: {n} port assignment(s) but {present[pid]} in model")
            )
    for pid in sorted(p for p in present if p in DEVICES):
        if present[pid] > assigned[pid]:
            issues.append(
                Issue("warning", "port-unassigned", f"{pid}: {present[pid] - assigned[pid]} device(s) without a port")
            )
    return issues
