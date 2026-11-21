from collections import Counter
from pathlib import Path

from lego_creator.ldraw import Library, parse
from lego_creator.validate import validate

LIB = Library(Path(__file__).parent / "fixtures" / "ldraw")


def codes(issues, level="error"):
    return sorted(i.code for i in issues if i.level == level)


CLEAN = (
    "0 FILE robot.ldr\n"
    "0 !LC PORT A 54675c01 drive_left\n"
    "1 16 0 0 0 1 0 0 0 1 0 0 0 1 54675c01.dat\n"
    "1 4 0 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n"
)


def test_clean_model_has_no_errors():
    available = Counter({("54675", 322): 1, ("3001", 4): 1})
    id_map = {"54675c01": [("54675", 1, None)]}
    assert codes(validate(parse(CLEAN), LIB, available, id_map)) == []


def test_missing_and_alias_parts_are_errors():
    doc = parse(
        "1 16 0 0 0 1 0 0 0 1 0 0 0 1 54696c01.dat\n"
        "1 4 0 0 0 1 0 0 0 1 0 0 0 1 nope.dat\n"
    )
    issues = validate(doc, LIB, None, {})
    assert codes(issues) == ["alias-part", "missing-part"]
    assert any("54696p01c01" in i.message for i in issues if i.code == "alias-part")


def test_inventory_shortage_is_error_in_kit_space():
    available = Counter({("3001", 4): 0})
    assert "inventory-shortage" in codes(validate(parse(CLEAN), LIB, available, {}))


def test_submodel_cycle_is_reported_not_raised():
    doc = parse(
        "0 FILE a.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 b.ldr\n"
        "0 FILE b.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 a.ldr\n"
    )
    assert codes(validate(doc, LIB, None, {})) == ["submodel-cycle"]


def test_port_errors_are_included():
    doc = parse("0 !LC PORT A 3001 x\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")
    assert codes(validate(doc, LIB, None, {})) == ["port-not-device"]


def test_unknown_quantity_part_is_warning_not_error():
    doc = parse("1 0 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")
    issues = validate(doc, LIB, Counter(), {}, unknown={"3001"})
    assert codes(issues) == []
    assert codes(issues, "warning") == ["quantity-unknown"]


def line(color="4", matrix="1 0 0 0 1 0 0 0 1", part="3001.dat"):
    return f"1 {color} 0 0 0 {matrix} {part}\n"


def test_proper_rotation_matrices_pass():
    doc = parse(line(matrix="0 0 1 0 1 0 -1 0 0") + line(matrix="0 -1 0 1 0 0 0 0 1"))
    assert codes(validate(doc, LIB, None, {})) == []


def test_mirrored_matrix_is_error():
    issues = validate(parse(line(matrix="-1 0 0 0 1 0 0 0 1")), LIB, None, {})
    assert codes(issues) == ["bad-matrix"]
    assert "mirrored" in issues[0].message and "line 1" in issues[0].message


def test_scaled_and_singular_matrices_are_errors():
    doc = parse(line(matrix="2 0 0 0 1 0 0 0 1") + line(matrix="1 0 0 0 0 0 0 0 1"))
    assert codes(validate(doc, LIB, None, {})) == ["bad-matrix", "bad-matrix"]


def test_unknown_color_is_error_but_inherit_and_known_pass():
    doc = parse(line(color="9999") + line(color="16") + line(color="71") + line(color="0x2FF0000"))
    assert codes(validate(doc, LIB, None, {})) == ["unknown-color", "unknown-color"]


def test_malformed_line_is_error_with_location():
    issues = validate(parse("0 FILE a.ldr\n1 4 0 0\n"), LIB, None, {})
    assert codes(issues) == ["malformed-line"]
    assert "a.ldr line 2" in issues[0].message
