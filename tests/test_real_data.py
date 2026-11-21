"""Checks against the real LDraw library and committed inventory data. Skipped until `lc fetch-ldraw` has run."""

import csv
from pathlib import Path

import pytest

from lego_creator.bom import load_id_map
from lego_creator.ldraw import Library
from lego_creator.ports import DEVICES

ROOT = Path(__file__).resolve().parents[1]
LIB = Library(ROOT / "ldraw", ROOT / "custom")
ID_MAP = load_id_map(ROOT / "inventory" / "id-map.csv")

pytestmark = pytest.mark.skipif(LIB.find("3001") is None, reason="LDraw library not fetched")

# Kit items that are not modelled in LDraw (packaging, cable, stickers) or whose print is not yet identified.
KNOWN_UNMAPPED = {"39881", "54187", "54190", "57277", "902097", "98138pr0062", "98138pr0076"}


@pytest.mark.parametrize("pid", sorted(ID_MAP))
def test_id_map_sources_are_real_non_alias_parts(pid):
    assert LIB.find(pid) is not None
    assert LIB.moved_to(pid) is None


@pytest.mark.parametrize("pid", sorted(DEVICES))
def test_devices_are_real_non_alias_parts(pid):
    assert LIB.find(pid) is not None
    assert LIB.moved_to(pid) is None


@pytest.mark.parametrize("kit", sorted(p.stem for p in (ROOT / "inventory").glob("*.csv") if p.stem != "id-map"))
def test_every_kit_part_is_reachable_from_ldraw(kit):
    mapped_targets = {k for targets in ID_MAP.values() for k, _, _ in targets}
    with (ROOT / "inventory" / f"{kit}.csv").open(newline="", encoding="utf-8") as f:
        unreachable = {
            r["part_num"]
            for r in csv.DictReader(f)
            if r["part_num"] not in mapped_targets
            and (LIB.find(r["part_num"]) is None or LIB.moved_to(r["part_num"]) is not None)
        }
    assert unreachable <= KNOWN_UNMAPPED


@pytest.mark.parametrize("path", sorted((ROOT / "templates").glob("*.mpd")), ids=lambda p: p.name)
def test_templates_resolve_without_errors(path):
    from lego_creator.ldraw import parse
    from lego_creator.validate import validate

    issues = validate(parse(path.read_text(encoding="utf-8"), default_name=path.name), LIB, None, ID_MAP)
    assert [i for i in issues if i.level == "error"] == []
