from collections import Counter

from lego_creator.bom import (
    IdMap,
    Shortage,
    check,
    left,
    load_id_map,
    load_inventory,
    load_unknown_parts,
    to_kit_space,
)


def test_load_inventory_sums_duplicate_rows(tmp_path):
    p = tmp_path / "kit.csv"
    p.write_text(
        "part_num,color_id,quantity,name\n"
        "3001,4,2,Brick 2 x 4\n"
        "3001,4,3,Brick 2 x 4\n"
        "54675,322,1,Motor\n"
    )
    assert load_inventory(p) == {("3001", 4): 5, ("54675", 322): 1}


def test_load_id_map_groups_expansions(tmp_path):
    p = tmp_path / "id-map.csv"
    p.write_text(
        "ldraw_id,kit_part,qty,color,note\n"
        "45601c01,45601,1,,hub\n"
        "45601c01,55422,1,14,battery\n"
        "54675C01,54675,1,,\n"
    )
    m = load_id_map(p)
    assert m["45601c01"] == [("45601", 1, None), ("55422", 1, 14)]
    assert m["54675c01"] == [("54675", 1, None)]


def test_to_kit_space_expands_mapped_parts_and_passes_through_others():
    id_map: IdMap = {"45601c01": [("45601", 1, None), ("55422", 1, 14)]}
    bom = Counter({("45601c01", 71): 1, ("3001", 4): 2})
    assert to_kit_space(bom, id_map) == {("45601", 71): 1, ("55422", 14): 1, ("3001", 4): 2}


def test_check_reports_part_level_shortage_as_error():
    errors, warnings = check(Counter({("3001", 4): 3}), Counter({("3001", 4): 1, ("3001", 1): 1}))
    assert errors == [Shortage("3001", None, need=3, have=2)]
    assert warnings == []


def test_check_reports_color_shortage_as_warning_when_part_total_suffices():
    errors, warnings = check(Counter({("3001", 4): 2}), Counter({("3001", 4): 1, ("3001", 1): 5}))
    assert errors == []
    assert warnings == [Shortage("3001", 4, need=2, have=1)]


def test_check_ignores_inherited_color_for_color_warnings():
    errors, warnings = check(Counter({("54675", 16): 1}), Counter({("54675", 322): 1}))
    assert (errors, warnings) == ([], [])


def test_blank_quantity_rows_are_unknown_not_counted(tmp_path):
    p = tmp_path / "kit.csv"
    p.write_text("part_num,color_id,quantity,name\n57519,0,,Sprocket\n3001,4,2,Brick\n")
    assert load_inventory(p) == {("3001", 4): 2}
    assert load_unknown_parts(p) == {"57519"}


def test_check_skips_unknown_quantity_parts():
    errors, warnings = check(Counter({("57519", 0): 4, ("3001", 4): 1}), Counter(), unknown={"57519"})
    assert errors == [Shortage("3001", None, need=1, have=0)]
    assert warnings == []


def test_left_subtracts_the_model_from_the_kits_part_by_colour():
    used = Counter({("3001", 4): 1, ("3002", 1): 1})
    kits = Counter({("3001", 4): 3, ("3020", 0): 2})
    assert left(used, kits) == [("3001", 4, 3, 1, 2), ("3002", 1, 0, 1, -1), ("3020", 0, 2, 0, 2)]
