from lego_creator.cables import CABLE_EXIT, HUB_PORT_POINTS, cable_plan
from lego_creator.ldraw import parse

RZP = "0 -1 0 1 0 0 0 0 1"
RZM = "0 1 0 -1 0 0 0 0 1"
MODEL = f"""0 FILE main.ldr
0 !LC PORT A 54675 drive_left
0 !LC PORT B 54675 drive_right
1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat
0 STEP
1 322 -40 0 0 {RZM} 54675.dat
1 322 40 0 0 {RZP} 54675.dat
0 STEP
1 14 0 -40 100 1 0 0 0 1 0 0 0 1 45601c01.dat
0 STEP
1 4 0 -200 0 1 0 0 0 1 0 0 0 1 3001.dat
0 STEP
"""


def test_cable_plan_puts_cables_in_after_the_hub_and_devices_are_placed():
    plan = cable_plan(parse(MODEL))
    assert plan.submodel == "main.ldr" and plan.after_step == 2 and plan.shown == 4
    assert [(c.port, c.part, c.label) for c in plan.cables] == [("A", "54675", "왼쪽 큰 모터"), ("B", "54675", "오른쪽 큰 모터")]


def test_the_nth_port_line_of_a_part_belongs_to_its_nth_placement():
    plan = cable_plan(parse(MODEL))
    ex, ey, ez = CABLE_EXIT["54675"]
    # left motor at x -40 with Rz-90: local (x, y, z) -> (y, -x, z)
    assert plan.cables[0].device_point == (-40 + ey, -ex, ez)
    # right motor at x 40 with Rz+90: local (x, y, z) -> (-y, x, z)
    assert plan.cables[1].device_point == (40 - ey, ex, ez)


def test_hub_points_are_the_ports_moved_with_the_hub():
    plan = cable_plan(parse(MODEL))
    hx, hy, hz = HUB_PORT_POINTS["A"]
    assert plan.cables[0].hub_point == (hx, hy - 40, hz + 100)
    assert plan.cables[0].hub_out == (-1, 0, 0) and plan.cables[1].hub_out == (1, 0, 0)


def test_no_plan_without_ports_and_no_hub_point_without_a_hub():
    assert cable_plan(parse("0 FILE main.ldr\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n")) is None
    plan = cable_plan(parse("0 FILE main.ldr\n0 !LC PORT A 54675 m\n1 322 0 0 0 1 0 0 0 1 0 0 0 1 54675.dat\n"))
    assert plan.cables[0].hub_point is None and plan.after_step == 0 and plan.cables[0].label == "큰 모터"
