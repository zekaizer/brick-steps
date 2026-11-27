"""How each new part arrives in the 3D step view. Skipped until `lc fetch-ldraw` has run."""

from pathlib import Path

import pytest

from lego_creator.geometry import Shapes
from lego_creator.insertion import FROM_ABOVE, Side, check_insertions, insertions, moves
from lego_creator.ldraw import parse

ROOT = Path(__file__).resolve().parents[1]
SHAPES = Shapes((ROOT / "ldraw", ROOT / "custom"))

pytestmark = pytest.mark.skipif(SHAPES.find("3001.dat") is None, reason="LDraw library not fetched")

I = "1 0 0 0 1 0 0 0 1"
UP = "0 -1 0 1 0 0 0 0 1"  # local X along Y: pins standing up
HOLES_X = "0 -1 0 1 0 0 0 0 1"  # beam along Z with its holes along X
ALONG_X = "0 0 1 0 1 0 -1 0 0"  # beam along X with vertical holes; bush or gear on an X axle
FROM_PLUS_X, FROM_MINUS_X = Side(0, 1), Side(0, -1)


def model(*steps, extra=""):
    """Lines starting with "0 !" are metas; any other line is a type 1 line without its leading "1"."""
    body = "".join("".join(f"{line}\n" if line.startswith("0 !") else f"1 {line}\n" for line in step) + "0 STEP\n"
                   for step in steps)
    return f"0 FILE main.ldr\n0 test\n{body}0 NOFILE\n{extra}"


def arrive(text):
    return insertions(parse(text), SHAPES)["main.ldr"]


@pytest.mark.parametrize("x, side", [(10, FROM_PLUS_X), (-10, FROM_MINUS_X)])
def test_pin_goes_in_from_the_side_it_sticks_out_on(x, side):
    pin = arrive(model([f"0 0 0 0 {HOLES_X} 32316.dat"], [f"0 {x} 0 0 {I} 61332.dat"]))[1]
    assert (pin.side, pin.rule, pin.partners, pin.blocked_by) == (side, "joint", (0,), None)


def test_beam_slides_onto_placed_pins_from_their_free_tips():
    pins = [f"0 10 0 {z} {I} 61332.dat" for z in (-20, 20)]
    beam = arrive(model([f"0 0 0 0 {HOLES_X} 32316.dat", *pins], [f"0 20 0 0 {HOLES_X} 32316.dat"]))[3]
    assert (beam.side, beam.rule, beam.partners, beam.blocked_by) == (FROM_PLUS_X, "joint", (1, 2), None)


def test_bush_and_gear_slide_onto_an_axle_from_its_free_end_as_one_train():
    # the 3L axle sticks out of the beam on +X; the bush and the gear sit end to end on that part
    step = arrive(model([f"0 0 0 0 {HOLES_X} 32316.dat", f"0 20 0 0 {I} 4519.dat"],
                        [f"0 20 0 0 {ALONG_X} 3713.dat", f"0 40 0 0 {ALONG_X} 32270.dat"]))[2:]
    assert [(a.side, a.rule, a.partners, a.blocked_by) for a in step] == [(FROM_PLUS_X, "joint", (1,), None)] * 2
    assert step[0].wave == step[1].wave and step[0].travel == step[1].travel
    wire = moves(step)
    assert [m["from"] for m in wire] == [[1, 0, 0], [1, 0, 0]]
    assert [sorted(m) for m in wire] == [["from", "travel", "wave"]] * 2


def test_loop_around_a_part_comes_in_from_the_side_when_above_is_blocked():
    # like a track around its sprockets: one beam over the post and one under it, as one sub-assembly,
    # crossing the post between two of its holes
    loop = (f"0 FILE loop.ldr\n1 0 0 -30 0 {I} 32316.dat\n1 0 0 30 0 {I} 32316.dat\n0 NOFILE\n")
    unit = arrive(model([f"0 0 0 0 {ALONG_X} 32316.dat"], [f"16 30 0 0 {I} loop.ldr"], extra=loop))[1]
    assert (unit.side, unit.rule, unit.partners, unit.blocked_by) == (FROM_PLUS_X, "free", (), None)


def test_part_with_nothing_to_go_by_drops_from_above():
    first, second = arrive(model([f"0 0 24 0 {I} 3001.dat"], [f"0 0 0 0 {I} 3001.dat"]))
    assert [(a.side, a.rule, a.blocked_by) for a in (first, second)] == [(FROM_ABOVE, "free", None)] * 2
    assert moves([second]) == [{"from": [0, -1, 0], "travel": round(second.travel), "wave": 0}]


def test_part_shut_in_on_every_side_drops_from_above_and_names_what_is_in_the_way():
    around = [f"0 0 -24 0 {I} 3001.dat", f"0 0 24 0 {I} 3001.dat", f"0 -80 0 0 {I} 3001.dat",
              f"0 80 0 0 {I} 3001.dat", f"0 0 0 -40 {I} 3001.dat", f"0 0 0 40 {I} 3001.dat"]
    shut = arrive(model(around, [f"0 0 0 0 {I} 3001.dat"]))[6]
    assert (shut.side, shut.rule, shut.blocked_by) == (FROM_ABOVE, "fallback", 0)


def test_tread_link_goes_on_from_above_even_under_another_part():
    link = arrive(model([f"0 0 -30 0 {I} 3001.dat"], [f"0 0 0 0 {I} 57518.dat"]))[1]
    assert (link.side, link.rule, link.blocked_by) == (FROM_ABOVE, "flexible", None)


def test_band_stretched_over_pins_goes_on_from_above_though_the_pins_point_into_parts():
    pins = [f"0 10 0 {z} {I} 61332.dat" for z in (-20, 20)]
    beams = [f"0 0 0 0 {HOLES_X} 32316.dat", f"0 40 0 0 {HOLES_X} 32316.dat"]
    band = arrive(model([*beams, *pins], [f"15 20 0 0 {ALONG_X} 85543.dat"]))[4]
    assert (band.side, band.rule, band.blocked_by) == (FROM_ABOVE, "flexible", None)


def test_pins_go_into_the_beams_before_the_hub_goes_down_onto_them():
    # tank-1 steps 6 and 7, with the hub written before its pins
    beams = [f"0 0 -100 {z} {ALONG_X} 40490.dat" for z in (100, 220)]
    pins = [f"0 {x} -110 {z} {UP} 61332.dat" for z in (100, 220) for x in (60, -60)]
    hub, *pins = arrive(model(beams, [f"14 0 -110 160 {I} 45601c01.dat", *pins]))[2:]
    assert [(p.side, p.rule, p.wave) for p in pins] == [(FROM_ABOVE, "joint", 0)] * 4
    assert (hub.side, hub.rule, hub.wave, hub.partners) == (FROM_ABOVE, "joint", 1, (3, 4, 5, 6))
    assert hub.order == 4 and sorted(p.order for p in pins) == [0, 1, 2, 3]


def test_insert_line_sets_how_the_next_reference_arrives():
    second = arrive(model([f"0 0 24 0 {I} 3001.dat"], ["0 !LC INSERT FROM -Z", f"0 0 0 0 {I} 3001.dat"]))[1]
    assert (second.side, second.rule) == (Side(2, -1), "override")


@pytest.mark.parametrize("slug", sorted(p.parent.name for p in (ROOT / "models").glob("*/model.mpd")))
def test_every_reference_of_a_real_model_arrives_once(slug):
    doc = parse((ROOT / "models" / slug / "model.mpd").read_text(encoding="utf-8"))
    result = insertions(doc, SHAPES)
    for name, sub in doc.models.items():
        assert len(result[name]) == len(sub.refs), name
        for step in {ref.step for ref in sub.refs}:
            orders = [result[name][i].order for i, ref in enumerate(sub.refs) if ref.step == step]
            assert sorted(orders) == list(range(len(orders))), (name, step)


def warnings(text):
    return [(i.level, i.code, i.message) for i in check_insertions(parse(text), SHAPES)]


def test_insert_line_whose_path_runs_into_a_part_is_a_warning():
    text = model([f"0 0 24 0 {I} 3001.dat"], ["0 !LC INSERT FROM +Y", f"0 0 0 0 {I} 3001.dat"])
    assert warnings(text) == [("warning", "insert-blocked",
                               "main.ldr line 6 (3001): from +Y runs into 3001 (line 3) within 48 LDU")]


def test_insert_line_that_says_what_the_view_does_anyway_is_a_warning():
    text = model([f"0 0 24 0 {I} 3001.dat"], ["0 !LC INSERT FROM -Y", f"0 0 0 0 {I} 3001.dat"])
    assert warnings(text) == [("warning", "insert-unneeded",
                               "main.ldr line 5: the 3D view already brings 3001 (line 6) in from -Y")]


def test_insert_line_with_a_clear_path_of_its_own_is_quiet():
    text = model([f"0 0 24 0 {I} 3001.dat"], ["0 !LC INSERT FROM -Z", f"0 0 0 0 {I} 3001.dat"])
    assert warnings(text) == []


def test_insert_line_across_a_pin_in_its_hole_is_a_warning():
    text = model([f"0 0 0 0 {HOLES_X} 32316.dat"], ["0 !LC INSERT FROM -Y", f"0 10 0 0 {I} 61332.dat"])
    assert warnings(text) == [("warning", "insert-blocked",
                               "main.ldr line 6 (61332): from -Y held along X by 32316 (line 3)")]


def test_sub_assembly_with_its_own_pin_moves_as_one_unit_along_the_pin():
    plug = f"0 FILE plug.ldr\n1 0 20 0 0 {HOLES_X} 32316.dat\n1 0 10 0 0 {I} 61332.dat\n0 NOFILE\n"
    unit = arrive(model([f"0 0 0 0 {HOLES_X} 32316.dat"], [f"16 0 0 0 {I} plug.ldr"], extra=plug))[1]
    assert (unit.side, unit.rule, unit.partners, unit.blocked_by) == (FROM_PLUS_X, "joint", (0,), None)


def test_part_missing_from_the_library_and_a_tilted_pin_drop_from_above():
    tilted = "0.7071 -0.7071 0 0.7071 0.7071 0 0 0 1"  # 45 degrees about Z: its axis is on no grid line
    step = arrive(model([f"0 0 0 0 {HOLES_X} 32316.dat"], [f"0 0 -60 0 {I} no-such-part.dat",
                                                           f"0 10 0 0 {tilted} 61332.dat"]))[1:]
    assert [(a.side, a.rule, a.blocked_by) for a in step] == [(FROM_ABOVE, "free", None)] * 2
    assert [m["from"] for m in moves(step)] == [[0, -1, 0], [0, -1, 0]]


def test_insert_line_turns_a_whole_sub_assembly():
    loop = f"0 FILE loop.ldr\n1 0 0 -30 0 {I} 32316.dat\n1 0 0 30 0 {I} 32316.dat\n0 NOFILE\n"
    text = model([f"0 0 0 0 {ALONG_X} 32316.dat"], ["0 !LC INSERT FROM -X", f"16 30 0 0 {I} loop.ldr"], extra=loop)
    unit = arrive(text)[1]
    assert (unit.side, unit.rule, unit.blocked_by) == (FROM_MINUS_X, "override", None)
    assert warnings(text) == []
