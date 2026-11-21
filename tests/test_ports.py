from collections import Counter

from lego_creator.ldraw import parse
from lego_creator.ports import PortAssignment, check_ports, parse_ports


def codes(issues):
    return sorted(i.code for i in issues)


def test_parse_ports_reads_meta_from_all_submodels():
    doc = parse(
        "0 FILE robot.ldr\n0 !LC PORT A 54675C01 drive_left\n"
        "0 FILE arm.ldr\n0 !LC PORT C 54696p01c01.dat arm_lift\n"
    )
    assignments, issues = parse_ports(doc)
    assert assignments == [
        PortAssignment("A", "54675c01", "drive_left"),
        PortAssignment("C", "54696p01c01", "arm_lift"),
    ]
    assert issues == []


def test_parse_ports_flags_malformed_meta():
    _, issues = parse_ports(parse("0 !LC PORT A 54675c01\n"))
    assert codes(issues) == ["port-malformed"]


def test_check_ports_accepts_valid_assignment():
    bom = Counter({("54675c01", 16): 2})
    a = [PortAssignment("A", "54675c01", "l"), PortAssignment("B", "54675c01", "r")]
    assert check_ports(a, bom) == []


def test_check_ports_flags_invalid_letter_and_duplicate():
    bom = Counter({("54675c01", 16): 3})
    a = [
        PortAssignment("G", "54675c01", "x"),
        PortAssignment("A", "54675c01", "y"),
        PortAssignment("A", "54675c01", "z"),
    ]
    assert codes(check_ports(a, bom)) == ["port-duplicate", "port-invalid"]


def test_check_ports_flags_non_device_and_missing_device():
    bom = Counter({("3001", 4): 1})
    a = [PortAssignment("A", "3001", "x"), PortAssignment("B", "37308c01", "eye")]
    assert codes(check_ports(a, bom)) == ["port-device-missing", "port-not-device"]


def test_check_ports_warns_on_unassigned_device():
    bom = Counter({("54696p01c01", 16): 2})
    issues = check_ports([PortAssignment("A", "54696p01c01", "x")], bom)
    assert [(i.level, i.code) for i in issues] == [("warning", "port-unassigned")]
