import yaml

from lego_creator.missions import BLOCKS, blocks_html, check_missions, mission_ports, parse_missions

SQUARE = yaml.safe_load("""
- title: 앞뒤로 달리기
  goal: 앞으로 갔다가 돌아와요.
  blocks:
  - [when_program_starts]
  - [set_movement_motors, A, B]
  - [repeat, 2, [[move_for, forward, 2, rotations], [move_for, backward, 2, rotations]]]
  try: 2를 3으로 바꾸면 어떻게 될까요?
""")


def codes(issues):
    return [(i.level, i.code) for i in issues]


def test_every_block_has_a_category_and_korean_wording():
    for block in BLOCKS.values():
        assert block.category in {"events", "movement", "motors", "control"}
        assert any("가" <= ch <= "힣" for ch in block.template)


def test_parse_reads_missions_with_nested_blocks():
    missions, issues = parse_missions(SQUARE)
    assert issues == []
    (m,) = missions
    assert m.title == "앞뒤로 달리기" and m.try_.startswith("2를 3으로")
    assert [b.block for b in m.blocks] == ["when_program_starts", "set_movement_motors", "repeat"]
    assert m.blocks[2].args == (2,) and [b.block for b in m.blocks[2].body] == ["move_for", "move_for"]


def test_parse_reports_a_mission_without_title_or_blocks():
    _, issues = parse_missions([{"goal": "x"}])
    assert codes(issues) == [("error", "mission-malformed")]
    _, issues = parse_missions({"title": "not a list"})
    assert codes(issues) == [("error", "mission-malformed")]


def test_check_accepts_a_valid_mission():
    missions, _ = parse_missions(SQUARE)
    assert check_missions(missions, {"A", "B"}) == []


def test_check_flags_unknown_blocks_and_bad_arguments():
    missions, _ = parse_missions([{"title": "t", "goal": "g", "blocks": [
        ["fly_away"],
        ["move_for", "forward", 2],
        ["move_for", "sideways", 2, "rotations"],
        ["move_for", "forward", "two", "rotations"],
        ["repeat", 2, [["stop_moving"]]],
    ]}])
    assert codes(check_missions(missions, {"A", "B"})) == [
        ("error", "block-unknown"), ("error", "block-args"), ("error", "block-args"), ("error", "block-args"),
    ]


def test_check_flags_ports_the_model_does_not_declare():
    missions, _ = parse_missions(SQUARE)
    assert mission_ports(missions[0]) == {"A", "B"}
    issues = check_missions(missions, {"A"})
    assert codes(issues) == [("error", "mission-port-undeclared")] and "B" in issues[0].message


def test_blocks_html_draws_each_block_in_its_category_with_its_wording():
    missions, _ = parse_missions(SQUARE)
    html = blocks_html(missions[0].blocks)
    assert html.count('class="block ') == 5
    assert 'class="block events"' in html and 'class="block control c"' in html
    assert BLOCKS["when_program_starts"].template in html
    assert ">A+B<" in html.replace(" ", "")
    assert html.index("repeat-body") < html.rindex("move")
