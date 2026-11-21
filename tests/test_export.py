"""End-to-end site build. Needs LeoCAD, Xvfb and the LDraw library (`lc fetch-ldraw`)."""

import json
import shutil
from pathlib import Path

import pytest

from lego_creator.export import ExportEnv, build_site

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("leocad") is None or not (ROOT / "ldraw" / "parts").is_dir(), reason="needs leocad and ldraw/"
)

MODEL = """0 FILE main.ldr
0 Test Bot
1 0 0 0 0 1 0 0 0 1 0 0 0 1 64179.dat
0 STEP
1 16 0 -10 0 1 0 0 0 1 0 0 0 1 board.ldr
0 STEP
0 NOFILE
0 FILE board.ldr
0 Board Pack
1 16 0 0 0 1 0 0 0 1 0 0 0 1 lms-esp32v2.dat
0 STEP
1 71 40 -14 60 1 0 0 0 1 0 0 0 1 3713.dat
1 71 -40 -14 60 1 0 0 0 1 0 0 0 1 3713.dat
0 STEP
0 NOFILE
"""


def test_build_site_end_to_end(tmp_path):
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "design", root / "design")
    for slug, status in (("bot", "ready"), ("wip", "draft")):
        d = root / "models" / slug
        d.mkdir(parents=True)
        (d / "model.yaml").write_text(f"name: 테스트 봇\nstatus: {status}\nkits: {{45678-1: 1}}\n"
                                      "story:\n  intro: 보드를 지켜요.\n")
        (d / "model.mpd").write_text(MODEL)
        (d / "missions.yaml").write_text("- title: 기다리기\n  goal: 잠깐 쉬어요.\n  blocks:\n"
                                         "  - [when_program_starts]\n  - [wait, 1]\n")
    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    env = ExportEnv(ROOT / "ldraw", ROOT / "custom", tokens, tmp_path / "cfg")
    out = tmp_path / "site"

    cards = build_site(root, out, env, include_drafts=False, pdf=True)

    assert [c.slug for c in cards] == ["bot"]
    assert cards[0].step_count == 4 and cards[0].part_count == 4
    for rel in ("index.html", "sw.js", "manifest.webmanifest", "assets/site.css", "assets/manual.js",
                "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon.svg",
                "favicon-32.png", "brand/brick-steps-lockup.svg", "bot/index.html", "bot/manual.pdf", "bot/img/hero.png",
                "bot/model3d.txt", "assets/viewer3d.js", "assets/vendor/three/three.module.min.js",
                "assets/vendor/three/addons/loaders/LDrawLoader.js"):
        assert (out / rel).is_file(), rel
    assert not (out / "wip").exists()
    page = (out / "bot" / "index.html").read_text(encoding="utf-8")
    assert page.count('class="card step"') == 4 and "Board Pack" in page
    for src in __import__("re").findall(r'src="([^"]+\.png)"', page):
        assert (out / "bot" / src).resolve().is_file(), src
    assert (out / "bot" / "manual.pdf").read_bytes()[:4] == b"%PDF"
    assert 'data-sub="board.ldr" data-shown="3" data-fresh="2"' in page
    assert "보드를 지켜요." in page and 'id="mission-1"' in page and 'data-block="wait"' in page
    packed = (out / "bot" / "model3d.txt").read_text(encoding="utf-8")
    for name in ("main.ldr", "board.ldr", "64179.dat", "lms-esp32v2.dat"):
        assert f"0 FILE {name}\n" in packed, name
