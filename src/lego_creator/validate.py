"""Run all static checks on a parsed model."""

from __future__ import annotations

from collections.abc import Collection

from .bom import Bom, IdMap, check, to_kit_space
from .ldraw import INHERIT_COLOR, Document, Library, PartRef, flatten
from .ports import check_ports, parse_ports
from .report import Issue

MATRIX_TOL = 1e-3


def _matrix_problem(m: tuple[float, ...]) -> str | None:
    """None for a proper rotation (orthonormal, det +1); otherwise why it is not one."""
    a, b, c, d, e, f, g, h, i = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < MATRIX_TOL:
        return "singular (det 0)"
    rows = ((a, b, c), (d, e, f), (g, h, i))
    for r in range(3):
        for s in range(3):
            dot = sum(rows[r][k] * rows[s][k] for k in range(3))
            if abs(dot - (1.0 if r == s else 0.0)) > MATRIX_TOL:
                return f"not orthonormal (det {det:.3g}); scaled or sheared"
    if det < 0:
        return "mirrored (det -1)"
    return None


def _refs(doc: Document) -> list[tuple[str, PartRef]]:
    return [(sub.name, ref) for sub in doc.models.values() for ref in sub.refs]


def validate(
    doc: Document,
    library: Library,
    available: Bom | None,
    id_map: IdMap,
    unknown: Collection[str] = frozenset(),
) -> list[Issue]:
    """Check line syntax, matrices, colors, part resolution, kit inventory (when available is given) and ports."""
    issues: list[Issue] = [
        Issue("error", "malformed-line", f"{sub} line {n}: {msg}") for sub, n, msg in doc.errors
    ]
    valid_colors = library.colors()
    for sub, ref in _refs(doc):
        if (problem := _matrix_problem(ref.matrix)) is not None:
            issues.append(Issue("error", "bad-matrix", f"{sub} line {ref.line} ({ref.name}): {problem}"))
        if valid_colors is not None and ref.color != INHERIT_COLOR and ref.color not in valid_colors:
            issues.append(Issue("error", "unknown-color", f"{sub} line {ref.line} ({ref.name}): color {ref.color} not in LDConfig"))

    try:
        bom = flatten(doc)
    except ValueError as e:
        return issues + [Issue("error", "submodel-cycle", str(e))]

    for pid in sorted({p for p, _ in bom}):
        if library.find(pid) is None:
            issues.append(Issue("error", "missing-part", f"{pid}: not a submodel and not in the LDraw library"))
        elif (target := library.moved_to(pid)) is not None:
            issues.append(Issue("error", "alias-part", f"{pid}: alias file, use {target}"))

    if available is not None:
        required = to_kit_space(bom, id_map)
        shortages, color_warnings = check(required, available, unknown)
        issues += [
            Issue("warning", "quantity-unknown", f"{p}: owned count unknown, not checked")
            for p in sorted({p for p, _ in required} & set(unknown))
        ]
        issues += [
            Issue("error", "inventory-shortage", f"{s.part}: need {s.need}, kits have {s.have}") for s in shortages
        ]
        issues += [
            Issue("warning", "color-not-in-kit", f"{s.part} color {s.color}: need {s.need}, kits have {s.have}")
            for s in color_warnings
        ]

    assignments, port_issues = parse_ports(doc)
    return issues + port_issues + check_ports(assignments, bom)
