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
0 !LC PORT A lms-esp32v2 board
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

    cards, lab = build_site(root, out, env, pdf=True)

    assert [c.slug for c in cards] == ["bot"] and [c.slug for c in lab] == ["wip"]
    assert cards[0].step_count == 4 and cards[0].part_count == 4
    assert cards[0].story == "보드를 지켜요." and cards[0].series == "bot" and cards[0].number == 1
    assert 'data-story="보드를 지켜요."' in (out / "index.html").read_text(encoding="utf-8")
    for rel in ("index.html", "sw.js", "manifest.webmanifest", "assets/site.css", "assets/manual.js",
                "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon.svg",
                "favicon-32.png", "brand/brick-steps-lockup.svg", "brand/brick-steps-mark.svg", "bot/index.html", "bot/manual.pdf", "bot/img/hero.png",
                "bot/model3d.txt", "assets/viewer3d.js", "assets/vendor/three/three.module.min.js",
                "assets/vendor/three/addons/loaders/LDrawLoader.js"):
        assert (out / rel).is_file(), rel
    assert not (out / "wip").exists() and "wip" not in (out / "index.html").read_text(encoding="utf-8")
    assert 'href="wip/"' in (out / "lab" / "index.html").read_text(encoding="utf-8")
    draft = (out / "lab" / "wip" / "index.html").read_text(encoding="utf-8")
    assert "아직 만들어 보지 않은 설계예요" in draft and 'href="../../assets/site.css"' in draft
    for src in __import__("re").findall(r'src="([^"]+\.png)"', draft):
        assert (out / "lab" / "wip" / src).resolve().is_file(), src
    page = (out / "bot" / "index.html").read_text(encoding="utf-8")
    assert page.count('class="card step"') == 4 and "Board Pack" in page
    for src in __import__("re").findall(r'src="([^"]+\.png)"', page):
        assert (out / "bot" / src).resolve().is_file(), src
    assert (out / "bot" / "manual.pdf").read_bytes()[:4] == b"%PDF"
    assert "Brick Steps v" + __import__("importlib.metadata").metadata.version("lego-creator") in (out / "index.html").read_text(encoding="utf-8")
    assert 'href="../" aria-label="처음으로"' in page and 'href="../" aria-label="처음으로"' in draft
    for html, base in ((page, out / "bot"), (draft, out / "lab" / "wip")):
        mark = __import__("re").search(r'src="([^"]+brick-steps-mark\.svg)"', html).group(1)
        assert (base / mark).resolve().is_file(), mark
    assert 'data-sub="board.ldr" data-shown="3" data-fresh="2"' in page
    assert page.index('id="step-1"') < page.index('id="cables"') < page.index('id="step-2"') and "보드" in page
    assert "보드를 지켜요." in page and 'id="mission-1"' in page and 'data-block="wait"' in page
    packed = (out / "bot" / "model3d.txt").read_text(encoding="utf-8")
    for name in ("main.ldr", "board.ldr", "64179.dat", "lms-esp32v2.dat"):
        assert f"0 FILE {name}\n" in packed, name


def test_rebuilt_manual_drops_pictures_from_an_earlier_build(tmp_path):
    from lego_creator.export import build_manual

    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    env = ExportEnv(ROOT / "ldraw", ROOT / "custom", tokens, tmp_path / "cfg")
    out = tmp_path / "manual"
    (out / "img").mkdir(parents=True)
    (out / "img" / "s0-09.png").write_bytes(b"stale")  # a ninth step the model no longer has
    (out / "img" / "s7-01.png").write_bytes(b"stale")  # a section the model no longer has
    model = ("0 FILE main.ldr\n0 Two Bricks\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n"
             "1 4 0 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n0 NOFILE\n")

    build_manual("두 블록", "bricks", model, env, out, thumbs_dir=tmp_path / "parts", thumbs_href="../parts/",
                 assets_href="../assets/", sw_href=None, manifest_href=None, pdf=False)

    assert sorted(p.name for p in (out / "img").iterdir()) == ["hero.png", "s0-01.png", "s0-02.png"]
    assert (out / "img" / "hero.png").read_bytes() == (out / "img" / "s0-02.png").read_bytes()


def test_service_worker_cache_is_named_after_the_build(tmp_path):
    import re

    from lego_creator.export import stamp_service_worker

    (tmp_path / "index.html").write_text("v1")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "site.css").write_text("a")
    sw = 'const CACHE = "brick-steps";\n'
    first = stamp_service_worker(sw, tmp_path)
    assert re.fullmatch(r'const CACHE = "brick-steps-[0-9a-f]{12}";\n', first)
    assert stamp_service_worker(sw, tmp_path) == first
    (tmp_path / "assets" / "site.css").write_text("b")
    assert stamp_service_worker(sw, tmp_path) != first


def test_service_worker_drops_caches_of_older_builds():
    sw = (ROOT / "src" / "lego_creator" / "site_assets" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "brick-steps";' in sw
    assert "caches.keys()" in sw and "caches.delete" in sw
    # Fonts and pinned three.js live in a cache no deploy deletes, so an update does not reload them.
    assert 'const STATIC = "brick-steps-static";' in sw and "n !== STATIC" in sw
