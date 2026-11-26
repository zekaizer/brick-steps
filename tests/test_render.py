import shutil
from pathlib import Path

import pytest

from lego_creator import render
from lego_creator.render import RenderCache, leocad_cmd, leocad_config, render_image, render_steps, step_outputs

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


def test_step_outputs_takes_the_plain_file_for_a_single_step(tmp_path):
    # LeoCAD drops the step number when the range is one step long.
    (tmp_path / "s.png").write_bytes(b"x")
    assert step_outputs(tmp_path / "s.png") == {1: tmp_path / "s.png"}


@pytest.mark.skipif(shutil.which("leocad") is None or not (ROOT / "ldraw" / "parts").is_dir(), reason="needs leocad and ldraw/")
def test_render_steps_with_leocad(tmp_path):
    mpd = tmp_path / "m.mpd"
    mpd.write_text("0 FILE m.ldr\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n1 1 0 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n")
    out = render_steps(mpd, tmp_path / "s.png", ROOT / "ldraw", tmp_path / "cfg", submodel="m.ldr", count=2,
                       width=200, height=150, background="#f2f7f8", highlight="#f2cd37")
    assert sorted(out) == [1, 2] and all(p.stat().st_size > 0 for p in out.values())


def fake_leocad(monkeypatch):
    """Replace LeoCAD with a recorder that writes the files it would; returns the list of runs."""
    runs = []

    def run(cmd, config_dir, background):
        runs.append(cmd)
        out = Path(cmd[cmd.index("-i") + 1])
        body = " ".join(cmd[cmd.index("-w"):-1]).encode()
        if "-f" in cmd:
            for n in range(int(cmd[cmd.index("-f") + 1]), int(cmd[cmd.index("-t") + 1]) + 1):
                (out.parent / f"{out.stem}{n:02d}{out.suffix}").write_bytes(body + bytes([n]))
        else:
            out.write_bytes(body)

    monkeypatch.setattr(render, "_run", run)
    monkeypatch.setattr(render, "leocad_version", lambda: "LeoCAD Version 25.09")
    return runs


def small_model(tmp_path):
    lib = tmp_path / "lib"
    (lib / "parts").mkdir(parents=True)
    (lib / "LDConfig.ldr").write_text("0 !COLOUR Red CODE 4 VALUE #C91A09 EDGE #333333\n")
    (lib / "parts" / "brick.dat").write_text("0 Brick\n2 24 0 0 0 20 0 0\n")
    mpd = tmp_path / "m.mpd"
    mpd.write_text("0 FILE m.ldr\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 brick.dat\n0 STEP\n"
                   "1 4 0 -24 0 1 0 0 0 1 0 0 0 1 brick.dat\n0 STEP\n")
    return lib, mpd


def test_a_cached_render_is_reused_until_something_it_reads_changes(tmp_path, monkeypatch):
    runs = fake_leocad(monkeypatch)
    lib, mpd = small_model(tmp_path)
    cache = RenderCache(tmp_path / "cache")

    def steps(out, **changed):
        args = {"submodel": "m.ldr", "count": 2, "width": 200, "height": 150, "background": "#f2f7f8",
                "highlight": "#f2cd37"} | changed
        (tmp_path / out).mkdir()
        return render_steps(mpd, tmp_path / out / "s0-.png", lib, tmp_path / "cfg", cache=cache, **args)

    first = steps("a")
    again = steps("b")
    assert len(runs) == 1
    assert sorted(p.name for p in again.values()) == ["s0-01.png", "s0-02.png"]
    assert [p.read_bytes() for p in again.values()] == [p.read_bytes() for p in first.values()]
    steps("c", highlight="#ffffff")
    steps("d", background="#000000")
    assert len(runs) == 3
    (lib / "parts" / "brick.dat").write_text("0 Brick\n2 24 0 0 0 40 0 0\n")  # a part file it reads
    steps("e")
    (lib / "LDConfig.ldr").write_text("0 !COLOUR Red CODE 4 VALUE #FF0000 EDGE #333333\n")
    steps("f")
    mpd.write_text(mpd.read_text().replace("-24 0", "-48 0"))
    steps("g")
    assert len(runs) == 6 and (cache.reused, cache.rendered) == (1, 6)


def test_prune_keeps_only_what_this_build_used(tmp_path, monkeypatch):
    runs = fake_leocad(monkeypatch)
    lib, mpd = small_model(tmp_path)
    earlier = RenderCache(tmp_path / "cache")
    for width in (100, 200):
        render_image(mpd, tmp_path / f"t{width}.png", lib, tmp_path / "cfg", width=width, height=100,
                     background="#ffffff", cache=earlier)
    now = RenderCache(tmp_path / "cache")
    out = render_image(mpd, tmp_path / "again.png", lib, tmp_path / "cfg", width=100, height=100,
                       background="#ffffff", cache=now)
    assert len(runs) == 2 and out.read_bytes() == (tmp_path / "t100.png").read_bytes()
    assert now.prune() == 1 and len(list((tmp_path / "cache").iterdir())) == 1
