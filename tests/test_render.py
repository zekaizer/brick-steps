import shutil
from pathlib import Path

import pytest

from lego_creator.render import leocad_cmd, leocad_config, render_steps, step_outputs

ROOT = Path(__file__).resolve().parents[1]


def test_leocad_config_sets_solid_background_as_abgr_int():
    conf = leocad_config("#f2f7f8")
    assert "[Settings]" in conf and "BackgroundGradient=false" in conf
    assert f"BackgroundColor={0xf2 | 0xf7 << 8 | 0xf8 << 16 | 0xff << 24}" in conf


def test_leocad_cmd_for_a_step_range_with_highlight():
    cmd = leocad_cmd(Path("m.mpd"), Path("out/s.png"), Path("ldraw"), width=800, height=600,
                     submodel="wheel.ldr", first=1, last=3, highlight="#f2cd37")
    assert cmd[:2] == ["xvfb-run", "-a"]
    joined = " ".join(cmd)
    for frag in ("-l ldraw", "-i out/s.png", "-w 800", "-h 600", "-s wheel.ldr", "-f 1", "-t 3",
                 "--highlight", "--highlight-color #FFF2CD37", "--no-fade-steps"):
        assert frag in joined
    assert cmd[-1] == "m.mpd"


def test_leocad_cmd_single_image_has_no_range_or_highlight():
    cmd = leocad_cmd(Path("m.mpd"), Path("t.png"), Path("ldraw"), width=160, height=160)
    assert "-f" not in cmd and "--highlight" not in cmd and "--no-highlight" in cmd


def test_step_outputs_maps_numbered_files(tmp_path):
    for name in ("s01.png", "s02.png", "s10.png", "other01.png"):
        (tmp_path / name).write_bytes(b"x")
    assert step_outputs(tmp_path / "s.png") == {1: tmp_path / "s01.png", 2: tmp_path / "s02.png", 10: tmp_path / "s10.png"}


@pytest.mark.skipif(shutil.which("leocad") is None or not (ROOT / "ldraw" / "parts").is_dir(), reason="needs leocad and ldraw/")
def test_render_steps_with_leocad(tmp_path):
    mpd = tmp_path / "m.mpd"
    mpd.write_text("0 FILE m.ldr\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n1 1 0 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n")
    out = render_steps(mpd, tmp_path / "s.png", ROOT / "ldraw", tmp_path / "cfg", submodel="m.ldr", count=2,
                       width=200, height=150, background="#f2f7f8", highlight="#f2cd37")
    assert sorted(out) == [1, 2] and all(p.stat().st_size > 0 for p in out.values())
