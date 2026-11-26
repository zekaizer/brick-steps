"""Model checks in scripts/ldraw_measure.py. Skipped until `lc fetch-ldraw` has run."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ldraw_measure", ROOT / "scripts" / "ldraw_measure.py")
assert spec and spec.loader
measure = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = measure  # dataclasses look their module up by name
spec.loader.exec_module(measure)

pytestmark = pytest.mark.skipif(measure.find("3001.dat") is None, reason="LDraw library not fetched")

I = "1 0 0 0 1 0 0 0 1"
UP = "0 -1 0 1 0 0 0 0 1"  # local X along Y: pins and axles standing up
FLAT = "1 0 0 0 0 -1 0 1 0"  # gear axis along Y
ALONG_X = "0 0 1 0 1 0 -1 0 0"  # beam lying along X, holes vertical


def model(*steps, extra=""):
    body = "".join("".join(f"1 {line}\n" for line in step) + "0 STEP\n" for step in steps)
    return f"0 FILE main.ldr\n0 test\n{body}0 NOFILE\n{extra}"


def kinds(report, kind):
    return [w for w in report if w[0] == kind]


def test_axle_that_stops_at_a_beam_face_is_reported():
    text = model([f"0 0 0 0 {I} 32316.dat", f"0 0 -40 0 {UP} 4519.dat", f"0 0 -30 40 {UP} 4519.dat"])
    report = measure.axle_report(text)
    touching = kinds(report, "touches-only")
    assert [w[1] for w in touching] == ["4519#1"]
    assert "32316#0" in touching[0][2]


def test_gear_with_nothing_on_one_side_is_reported():
    text = model([f"0 0 0 0 {I} 32316.dat", f"0 0 -30 40 {UP} 4519.dat",
                  f"0 0 -40 40 {FLAT} 32270.dat", f"0 0 -55 40 {FLAT} 32123b.dat"])
    free = kinds(measure.axle_report(text), "gear-free")
    assert [(w[1], w[2]) for w in free] == [("32270#2", "+Y")]


def test_balance_compares_the_centre_of_gravity_with_the_wheels():
    wheel = "0 FILE wheel.ldr\n0 !LC GROUND\n1 15 0 0 0 1 0 0 0 1 0 0 0 1 56903.dat\n0 NOFILE\n"
    wheels = [f"16 100 30 0 {I} wheel.ldr", f"16 -100 30 0 {I} wheel.ldr", f"16 0 30 150 {I} wheel.ldr"]
    inside = measure.balance_report(model(wheels + [f"14 0 0 60 {I} 45601c01.dat"], extra=wheel))
    outside = measure.balance_report(model(wheels + [f"14 0 0 -100 {I} 45601c01.dat"], extra=wheel))
    assert inside["inside"] and inside["margin"] > 0
    assert not outside["inside"] and outside["margin"] < 0


def test_step_sizes_count_parts_per_step():
    text = model([f"0 0 0 0 {I} 32316.dat", f"0 0 -40 0 {UP} 4519.dat"], [f"0 0 20 0 {I} 32316.dat"])
    assert measure.step_sizes(text) == [("main.ldr", 1, 2), ("main.ldr", 2, 1)]


def test_part_with_nothing_to_hold_it_yet_is_floating():
    text = model([f"0 0 0 0 {I} 32316.dat"], [f"0 0 0 400 {I} 32316.dat"])
    assert [w[1] for w in kinds(measure.assembly_report(text), "floating")] == ["32316#1"]


def test_pin_shut_in_on_both_sides_cannot_be_inserted():
    # 3L beams across, shifted half a hole, so their solid web sits on the pin's line
    above, below = f"14 10 -20 0 {ALONG_X} 32523.dat", f"14 10 20 0 {ALONG_X} 32523.dat"
    shut = model([f"0 0 0 0 {I} 32316.dat", above, below], [f"0 0 0 0 {UP} 61332.dat"])
    open_below = model([f"0 0 0 0 {I} 32316.dat", above], [f"0 0 0 0 {UP} 61332.dat"])
    assert [w[1] for w in kinds(measure.assembly_report(shut), "pin-blocked")] == ["61332#3"]
    assert kinds(measure.assembly_report(open_below), "pin-blocked") == []
