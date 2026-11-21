from lego_creator.ldraw import parse
from lego_creator.motion import Turn, check_ground, check_turns, parse_turns

# Local boxes of the test parts: a 20 LDU cube, a bar 100 long along Z, an axle 60 long along Y.
BOXES = {
    "cube.dat": ((-10, -10, -10), (10, 10, 10)),
    "bar.dat": ((-5, -5, 0), (5, 5, 100)),
    "axle.dat": ((-2, -30, -2), (2, 30, 2)),
}


def box(name):
    return BOXES.get(name)


def codes(issues):
    return sorted(i.code for i in issues)


ARM = """0 FILE main.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 arm.ldr
1 4 0 0 0 1 0 0 0 1 0 0 0 1 axle.dat
1 4 70 0 0 1 0 0 0 1 0 0 0 1 cube.dat
0 FILE arm.ldr
0 !LC TURN 0 -1 0 0 0 0 {start} {end} arm
1 1 0 0 0 1 0 0 0 1 0 0 0 1 bar.dat
1 1 0 0 0 1 0 0 0 1 0 0 0 1 axle.dat
"""


def test_parse_turns_reads_axis_pivot_range_and_role():
    turns, issues = parse_turns(parse(ARM.format(start=0, end=360)))
    assert issues == []
    assert turns == [Turn("arm.ldr", (0.0, -1.0, 0.0), (0.0, 0.0, 0.0), 0.0, 360.0, "arm")]


def test_parse_turns_flags_malformed_meta():
    _, issues = parse_turns(parse("0 !LC TURN 0 -1 0 arm\n"))
    assert codes(issues) == ["turn-malformed"]
    _, issues = parse_turns(parse("0 !LC TURN 0 0 0 0 0 0 0 90 arm\n"))
    assert codes(issues) == ["turn-malformed"]  # zero axis


def test_turning_into_a_part_is_reported_once_with_the_first_angle():
    doc = parse(ARM.format(start=0, end=360))
    turns, _ = parse_turns(doc)
    issues = check_turns(doc, turns, box)
    assert codes(issues) == ["turn-interference"]
    assert "arm" in issues[0].message and "bar.dat" in issues[0].message and "cube.dat" in issues[0].message
    assert "270°" in issues[0].message


def test_parts_touching_before_turning_are_joints_not_interference():
    # The arm's axle sits inside the base axle from the start; turning keeps it there.
    doc = parse(ARM.format(start=0, end=45))
    turns, _ = parse_turns(doc)
    assert check_turns(doc, turns, box) == []


def test_turning_the_other_way_is_checked_too():
    doc = parse(ARM.format(start=-120, end=0))
    turns, _ = parse_turns(doc)
    issues = check_turns(doc, turns, box)
    assert codes(issues) == ["turn-interference"] and "-90°" in issues[0].message


def test_parts_without_geometry_are_skipped():
    doc = parse(ARM.format(start=0, end=360))
    turns, _ = parse_turns(doc)
    assert check_turns(doc, turns, lambda name: None) == []


GROUNDED = """0 FILE main.ldr
1 16 0 0 0 1 0 0 0 1 0 0 0 1 wheel.ldr
1 4 0 {y} 0 1 0 0 0 1 0 0 0 1 cube.dat
0 FILE wheel.ldr
0 !LC GROUND
1 1 0 0 0 1 0 0 0 1 0 0 0 1 cube.dat
"""


def test_ground_is_the_bottom_of_the_parts_that_touch_the_floor():
    # Wheel cube bottom at y 10 (down is +Y). A part 30 LDU higher is clear of the floor.
    assert check_ground(parse(GROUNDED.format(y=-30)), box) == []


def test_part_close_to_or_below_the_floor_is_reported():
    near = check_ground(parse(GROUNDED.format(y=-4)), box)
    assert codes(near) == ["ground-clearance"] and "cube.dat" in near[0].message and "main.ldr" in near[0].message
    below = check_ground(parse(GROUNDED.format(y=10)), box)
    assert codes(below) == ["ground-clearance"]


def test_no_ground_declared_means_no_ground_check():
    assert check_ground(parse(ARM.format(start=0, end=0)), box) == []


def test_part_boxes_follow_subfiles(tmp_path):
    from lego_creator.motion import PartBoxes

    (tmp_path / "parts" / "s").mkdir(parents=True)
    (tmp_path / "p").mkdir()
    (tmp_path / "p" / "square.dat").write_text("4 16 -1 0 -1 1 0 -1 1 0 1 -1 0 1\n")
    (tmp_path / "parts" / "s" / "half.dat").write_text("1 16 0 0 0 10 0 0 0 1 0 0 0 10 square.dat\n")
    (tmp_path / "parts" / "slab.dat").write_text("1 16 0 0 0 1 0 0 0 1 0 0 0 1 s/half.dat\n1 16 0 -8 0 1 0 0 0 1 0 0 0 1 s/half.dat\n")
    assert PartBoxes([tmp_path])("SLAB.DAT") == ((-10.0, -8.0, -10.0), (10.0, 0.0, 10.0))
    assert PartBoxes([tmp_path])("missing.dat") is None
