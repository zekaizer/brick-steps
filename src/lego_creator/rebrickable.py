"""Extract a set inventory from Rebrickable bulk CSV downloads."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable


def extract_set_inventory(
    inventories: Iterable[dict[str, str]],
    inventory_parts: Iterable[dict[str, str]],
    part_names: dict[str, str],
    set_num: str,
) -> list[dict[str, str]]:
    """Return non-spare parts of the latest inventory version of set_num, sorted by part/color."""
    versions = [(int(r["version"]), r["id"]) for r in inventories if r["set_num"] == set_num]
    if not versions:
        return []
    inv_id = max(versions)[1]

    qty: Counter[tuple[str, str]] = Counter()
    for r in inventory_parts:
        if r["inventory_id"] == inv_id and r["is_spare"] != "True":
            qty[(r["part_num"], r["color_id"])] += int(r["quantity"])

    return [
        {"part_num": p, "color_id": c, "quantity": str(n), "name": part_names.get(p, "")}
        for (p, c), n in sorted(qty.items())
    ]
