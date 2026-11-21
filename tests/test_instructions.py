from pathlib import Path

from lego_creator.instructions import Section, Step, StepItem, build_mpd, plan
from lego_creator.ldraw import Library, parse

FIX = Path(__file__).parent / "fixtures"
LIB = Library(FIX / "ldraw", FIX / "custom")

ROBOT = (
    "0 FILE robot.ldr\n"
    "0 Tank Robot\n"
    "1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
    "0 STEP\n"
    "1 16 0 0 0 1 0 0 0 1 0 0 0 1 wheel.ldr\n"
    "1 16 0 0 0 1 0 0 0 1 0 0 0 1 wheel.ldr\n"
    "0 STEP\n"
    "0 STEP\n"
    "1 0 0 0 0 1 0 0 0 1 0 0 0 1 test-board.dat\n"
    "0 NOFILE\n"
    "0 FILE wheel.ldr\n"
    "0 Wheel Pack\n"
    "1 15 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
    "1 15 0 0 0 1 0 0 0 1 0 0 0 1 3020.dat\n"
    "1 71 0 0 0 1 0 0 0 1 0 0 0 1 4519.dat\n"
    "0 STEP\n"
    "0 NOFILE\n"
)


def test_plan_puts_submodels_first_and_skips_empty_steps():
    sections = plan(parse(ROBOT))
    assert [s.submodel for s in sections] == ["wheel.ldr", "robot.ldr"]
    assert [s.title for s in sections] == ["Wheel Pack", "Tank Robot"]
    assert sections[0].steps == [Step(1, [StepItem("3020", 15, 2), StepItem("4519", 71, 1)])]
    assert sections[1].steps == [
        Step(1, [StepItem("3001", 4, 1)]),
        Step(2, [StepItem("wheel.ldr", 16, 2, is_submodel=True)]),
        Step(4, [StepItem("test-board", 0, 1)]),
    ]


def test_plan_visits_each_submodel_once_in_first_use_order():
    text = (
        "0 FILE a.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 c.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 b.ldr\n"
        "0 FILE b.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 c.ldr\n"
        "0 FILE c.ldr\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
    )
    assert [s.submodel for s in plan(parse(text))] == ["c.ldr", "b.ldr", "a.ldr"]
    assert isinstance(plan(parse(text))[0], Section)


def test_build_mpd_embeds_only_custom_parts_once():
    doc = parse(ROBOT)
    out = build_mpd(ROBOT, doc, LIB, FIX / "custom")
    assert out.startswith(ROBOT)
    assert out.count("0 FILE test-board.dat") == 1
    assert "Test Custom Board" in out
    assert "0 FILE 3001.dat" not in out


def test_build_mpd_wraps_plain_ldr():
    text = "1 0 0 0 0 1 0 0 0 1 0 0 0 1 test-board.dat\n"
    out = build_mpd(text, parse(text, default_name="m.ldr"), LIB, FIX / "custom")
    assert out.startswith("0 FILE m.ldr\n")
    assert "0 FILE test-board.dat" in out
