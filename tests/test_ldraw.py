from pathlib import Path

import pytest

from lego_creator.ldraw import (
    Library,
    Meta,
    flatten,
    normalize_name,
    parse,
    part_id,
    step_groups,
)

FIXTURE_LIB = Path(__file__).parent / "fixtures" / "ldraw"

IDENTITY = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def test_normalize_name_lowercases_and_unifies_separators():
    assert normalize_name("S\\3001S01.DAT") == "s/3001s01.dat"
    assert normalize_name("  Chassis.LDR ") == "chassis.ldr"


def test_part_id_strips_dat_extension_only():
    assert part_id("54675C01.dat") == "54675c01"
    assert part_id("chassis.ldr") == "chassis.ldr"


def test_parse_single_ldr_reads_type1_lines():
    doc = parse("0 Test\n1 4 10 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n2 24 0 0 0 1 1 1\n")
    ref = doc.main.refs[0]
    assert len(doc.main.refs) == 1
    assert ref.color == 4
    assert ref.pos == (10.0, -24.0, 0.0)
    assert ref.matrix == IDENTITY
    assert ref.name == "3001.dat"


def test_parse_mpd_keeps_file_order_and_first_is_main():
    text = (
        "0 FILE robot.ldr\n"
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 base.ldr\n"
        "0 NOFILE\n"
        "0 FILE base.ldr\n"
        "1 15 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
        "0 NOFILE\n"
    )
    doc = parse(text)
    assert list(doc.models) == ["robot.ldr", "base.ldr"]
    assert doc.main.name == "robot.ldr"


def test_parse_counts_steps_and_collects_meta_tokens():
    text = "0 STEP\n0 !LC PORT A 54675c01 drive_left\n0 STEP\n0 // plain comment\n"
    sub = parse(text).main
    assert sub.steps == 2
    assert [m.tokens for m in sub.metas] == [("!LC", "PORT", "A", "54675c01", "drive_left")]


def test_meta_keeps_its_line_step_and_the_reference_after_it():
    text = (
        "0 FILE main.ldr\n"
        "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
        "0 STEP\n"
        "0 !LC INSERT FROM +X\n"
        "0 // the brick goes on from the side\n"
        "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
        "0 !LC GROUND\n"
    )
    sub = parse(text).main
    assert sub.metas == [Meta(("!LC", "INSERT", "FROM", "+X"), 4, 1, 1), Meta(("!LC", "GROUND"), 7, 1, 2)]


def test_flatten_multiplies_submodels_and_inherits_color():
    text = (
        "0 FILE robot.ldr\n"
        "1 4 0 0 0 1 0 0 0 1 0 0 0 1 side.ldr\n"
        "1 1 0 0 0 1 0 0 0 1 0 0 0 1 side.ldr\n"
        "1 0 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
        "0 FILE side.ldr\n"
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
        "1 71 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
    )
    bom = flatten(parse(text))
    assert bom == {("3020", 4): 1, ("3020", 1): 1, ("3020", 71): 2, ("3001", 0): 1}


def test_flatten_rejects_submodel_cycle():
    text = (
        "0 FILE a.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 b.ldr\n"
        "0 FILE b.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 a.ldr\n"
    )
    with pytest.raises(ValueError, match="cycle"):
        flatten(parse(text))


def test_library_find_is_case_insensitive():
    lib = Library(FIXTURE_LIB)
    assert lib.find("4519") is not None
    assert lib.find("3001") is not None
    assert lib.find("99999") is None


def test_library_title_and_moved_to():
    lib = Library(FIXTURE_LIB)
    assert lib.title("3001") == "Brick  2 x  4"
    assert lib.moved_to("54696c01") == "54696p01c01"
    assert lib.moved_to("3001") is None


FIXTURE_CUSTOM = Path(__file__).parent / "fixtures" / "custom"


def test_library_searches_extra_roots_after_official():
    lib = Library(FIXTURE_LIB, FIXTURE_CUSTOM)
    assert lib.title("test-board") == "Test Custom Board"
    assert lib.title("3001") == "Brick  2 x  4"


def test_parse_records_malformed_lines_instead_of_raising():
    doc = parse("0 FILE a.ldr\n1 4 0 0 0 1 0 0\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n7 junk\n")
    assert [(m, n) for m, n, _ in doc.errors] == [("a.ldr", 2), ("a.ldr", 4)]
    assert [r.line for r in doc.main.refs] == [3]


def test_parse_accepts_direct_hex_colors():
    ref = parse("1 0x2FF0000 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n").main.refs[0]
    assert ref.color == 0x2FF0000


def test_library_colors_from_ldconfig():
    colors = Library(FIXTURE_LIB, FIXTURE_CUSTOM).colors()
    assert colors is not None and {0, 4, 16, 71} <= colors and 9999 not in colors


STEPPED = (
    "0 FILE robot.ldr\n"
    "0 Robot Title\n"
    "0 Name: robot.ldr\n"
    "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
    "0 STEP\n"
    "0 STEP\n"
    "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
    "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
)


def test_step_groups_follow_step_markers_and_trailing_content():
    groups = step_groups(parse(STEPPED).main)
    assert [[r.name for r in g] for g in groups] == [["3001.dat"], [], ["3020.dat", "3020.dat"]]


def test_step_groups_without_trailing_content_match_marker_count():
    sub = parse("1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n").main
    assert len(step_groups(sub)) == 1


def test_submodel_title_is_first_plain_comment():
    assert parse(STEPPED).main.title == "Robot Title"
