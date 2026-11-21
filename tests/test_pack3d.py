import pytest

from lego_creator.pack3d import pack_model

MODEL = """0 FILE Main.ldr
0 Bot
1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat
0 STEP
1 16 0 -24 0 1 0 0 0 1 0 0 0 1 arm.ldr
0 NOFILE
0 FILE arm.ldr
0 Arm
1 14 0 0 0 1 0 0 0 1 0 0 0 1 Custom.DAT
0 NOFILE
"""


@pytest.fixture
def roots(tmp_path):
    official, custom = tmp_path / "ldraw", tmp_path / "custom"
    files = {
        official / "LDConfig.ldr": "0 LDraw.org Configuration File\n0 !COLOUR Red CODE 4 VALUE #C91A09 EDGE #333333\n",
        official / "parts" / "3001.dat": (
            "0 Brick 2 x 4\n0 !LDRAW_ORG Part\n0 !HISTORY 2001-01-01 [x] made\n0 // note\n"
            "1 16 0 0 0 1 0 0 0 1 0 0 0 1 s\\3001s01.dat\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 stud.dat\n"
        ),
        official / "parts" / "s" / "3001s01.dat": "0 ~Brick shell\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 48/1-4cyli.dat\n",
        official / "p" / "stud.dat": "0 Stud\n4 16 0 0 0 1 0 0 1 0 1 0 0 1\n",
        official / "p" / "48" / "1-4cyli.dat": "0 Cylinder\n4 16 0 0 0 1 0 0 1 0 1 0 0 1\n",
        custom / "parts" / "custom.dat": "0 Custom\n4 16 0 0 0 1 0 0 1 0 1 0 0 1\n",
    }
    for path, body in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    return [official, custom]


def _blocks(packed: str) -> dict[str, str]:
    head, *rest = packed.split("0 FILE ")
    out = {"": head}
    for block in rest:
        name, _, body = block.partition("\n")
        out[name] = body
    return out


def test_pack_embeds_every_file_under_the_name_the_loader_looks_up(roots):
    blocks = _blocks(pack_model(MODEL, "main.ldr", roots))
    assert set(blocks) == {"", "main.ldr", "arm.ldr", "3001.dat", "parts/s/3001s01.dat", "stud.dat",
                           "p/48/1-4cyli.dat", "custom.dat"}


def test_pack_starts_with_colours_only_so_the_viewer_can_pick_the_submodel(roots):
    head = _blocks(pack_model(MODEL, "main.ldr", roots))[""]
    assert head.strip() == "0 !COLOUR Red CODE 4 VALUE #C91A09 EDGE #333333"


def test_pack_keeps_geometry_and_type_but_drops_history_and_comments(roots):
    brick = _blocks(pack_model(MODEL, "main.ldr", roots))["3001.dat"]
    assert "0 !LDRAW_ORG Part" in brick and "3001s01.dat" in brick
    assert "!HISTORY" not in brick and "// note" not in brick


def test_pack_keeps_submodel_steps(roots):
    main = _blocks(pack_model(MODEL, "main.ldr", roots))["main.ldr"]
    assert main.splitlines()[1:4] == ["1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat", "0 STEP",
                                      "1 16 0 -24 0 1 0 0 0 1 0 0 0 1 arm.ldr"]
    assert "NOFILE" not in main


def test_pack_names_a_plain_ldr_after_the_main_model(roots):
    blocks = _blocks(pack_model("1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n", "solo.ldr", roots))
    assert "solo.ldr" in blocks and "3001.dat" in blocks


def test_pack_fails_on_a_missing_file(roots):
    with pytest.raises(ValueError, match="nope.dat"):
        pack_model("1 4 0 0 0 1 0 0 0 1 0 0 0 1 nope.dat\n", "solo.ldr", roots)
