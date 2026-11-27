"""End-to-end site build. Needs LeoCAD, Xvfb and the LDraw library (`lc fetch-ldraw`)."""

import json
import re
import shutil
import zlib
from html import unescape
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


def pdf_font_names(pdf):
    """Embedded font names without their subset tag, from the PDF's objects and its inflated streams."""
    data = pdf
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", pdf, re.DOTALL):
        try:
            data += zlib.decompress(m.group(1))
        except zlib.error:
            pass
    return {n.decode().split("+")[-1] for n in re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-]+)", data)}


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
                                         "  - [when_program_starts]\n  - [wait, 1]\n  - [start_moving, clockwise]\n")
    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    env = ExportEnv(ROOT / "ldraw", ROOT / "custom", tokens, tmp_path / "cfg", ROOT / ".cache" / "fonts")
    out = tmp_path / "site"

    cards, lab = build_site(root, out, env, pdf=True)

    assert [c.slug for c in cards] == ["bot"] and [c.slug for c in lab] == ["wip"]
    assert cards[0].step_count == 4 and cards[0].part_count == 4
    assert cards[0].story == "보드를 지켜요." and cards[0].series == "bot" and cards[0].number == 1
    assert 'data-story="보드를 지켜요."' in (out / "index.html").read_text(encoding="utf-8")
    for rel in ("index.html", "sw.js", "manifest.webmanifest", "assets/site.css", "assets/manual.js",
                "icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "favicon.svg",
                "favicon-32.png", "brand/brick-steps-lockup.svg", "brand/brick-steps-mark.svg", "bot/index.html", "bot/manual.pdf", "bot/img/hero.png",
                "bot/model3d.txt", "assets/viewer3d.js", "assets/vendor/three-0.187.0/three.module.js",
                "assets/vendor/three-0.187.0/three.core.js", "assets/vendor/three-0.187.0/addons/loaders/LDrawLoader.js"):
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
    # Every page and the PDF use the fonts the build cut down to their characters (ADR 0004).
    css = (out / "assets" / "site.css").read_text(encoding="utf-8")
    fonts = re.findall(r'url\("(fonts/[^"]+\.woff2)"\)', css)
    assert {f.split("/")[1].rsplit("-", 1)[0] for f in fonts} == {"noto-sans-kr", "lexend", "noto-sans-math"}
    assert sorted(f"assets/{f}" for f in fonts) == sorted(p.relative_to(out).as_posix()
                                                         for p in (out / "assets" / "fonts").iterdir())
    names = pdf_font_names((out / "bot" / "manual.pdf").read_bytes())
    # Only the site's fonts: a device font here means a character of the PDF that they lack (the mission has ↻ ▾).
    assert {"Noto-Sans-KR", "Lexend-Bold"} <= names, names
    assert all(n.startswith(("Noto-Sans-KR", "Lexend", "Noto-Sans-Math")) for n in names), names
    # The 3D model is parsed in a module worker, which has no import map: its imports are plain paths.
    worker = (out / "assets" / "viewer3d-worker.js").read_text(encoding="utf-8")
    for rel in __import__("re").findall(r'from "(\./[^"]+)"', worker):
        assert (out / "assets" / rel).is_file(), rel
    loader = (out / "assets" / "vendor" / "three-0.187.0" / "worker" / "LDrawLoader.js").read_text(encoding="utf-8")
    assert "from 'three'" not in loader and "} from '../three.module.js';" in loader
    sw = (out / "sw.js").read_text(encoding="utf-8")
    for rel in __import__("re").findall(r'"\./(assets/[^"]+)"', sw):  # the offline shell must exist
        assert (out / rel).is_file(), rel
    assert "Brick Steps v" + __import__("importlib.metadata").metadata.version("lego-creator") in (out / "index.html").read_text(encoding="utf-8")
    assert 'href="../" aria-label="처음으로"' in page and 'href="../" aria-label="처음으로"' in draft
    for html, base in ((page, out / "bot"), (draft, out / "lab" / "wip")):
        mark = __import__("re").search(r'src="([^"]+brick-steps-mark\.svg)"', html).group(1)
        assert (base / mark).resolve().is_file(), mark
    assert 'data-sub="board.ldr" data-shown="3" data-fresh="2"' in page
    # Every build step says how each of its new parts comes in; the cable and done figures add none.
    figures = re.findall(r'<figure class="step-img" data-sub="[^"]*" data-shown="\d+" data-fresh="(\d+)"'
                         r'(?: data-moves="([^"]*)")?', page)
    moves = [json.loads(unescape(m)) for _, m in figures if m]
    assert len(moves) == 4 and [len(m) for m in moves] == [int(f) for f, m in figures if m]
    assert all(set(e) == {"from", "travel", "wave"} and e["travel"] > 0 for m in moves for e in m)
    assert page.index('id="step-1"') < page.index('id="cables"') < page.index('id="step-2"') and "보드" in page
    assert "보드를 지켜요." in page and 'id="mission-1"' in page and 'data-block="wait"' in page
    packed = (out / "bot" / "model3d.txt").read_text(encoding="utf-8")
    for name in ("main.ldr", "board.ldr", "64179.dat", "lms-esp32v2.dat"):
        assert f"0 FILE {name}\n" in packed, name


def test_rebuilt_manual_drops_pictures_from_an_earlier_build(tmp_path):
    from lego_creator.export import build_manual

    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    env = ExportEnv(ROOT / "ldraw", ROOT / "custom", tokens, tmp_path / "cfg", ROOT / ".cache" / "fonts")
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


def test_a_rebuilt_manual_takes_every_picture_from_the_render_cache(tmp_path):
    from lego_creator.export import build_manual
    from lego_creator.render import RenderCache

    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    model = ("0 FILE main.ldr\n0 Two Bricks\n1 4 0 0 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n"
             "1 1 0 -24 0 1 0 0 0 1 0 0 0 1 3001.dat\n0 STEP\n0 NOFILE\n")
    builds = []
    for name in ("first", "second"):
        cache = RenderCache(tmp_path / "cache")
        env = ExportEnv(ROOT / "ldraw", ROOT / "custom", tokens, tmp_path / "cfg", ROOT / ".cache" / "fonts", render_cache=cache)
        out = tmp_path / name
        build_manual("두 블록", "bricks", model, env, out, thumbs_dir=out / "parts", thumbs_href="parts/",
                     assets_href="assets/", sw_href=None, manifest_href=None, pdf=False)
        builds.append((cache, out))
    (first, a), (second, b) = builds
    assert (first.reused, first.rendered) == (0, 3)  # one run for both steps, one per part thumbnail
    assert (second.reused, second.rendered) == (3, 0)
    for rel in ("img/s0-01.png", "img/s0-02.png", "img/hero.png"):
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel


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


def test_service_worker_lists_the_fonts_of_the_build(tmp_path):
    from lego_creator.export import stamp_service_worker

    (tmp_path / "assets" / "fonts").mkdir(parents=True)
    for name in ("lexend-bbb.woff2", "noto-sans-kr-aaa.woff2"):
        (tmp_path / "assets" / "fonts" / name).write_bytes(b"font")
    stamped = stamp_service_worker('const CACHE = "brick-steps";\nconst FONTS = [];\n', tmp_path)
    assert 'const FONTS = ["./assets/fonts/lexend-bbb.woff2", "./assets/fonts/noto-sans-kr-aaa.woff2"];' in stamped


def test_service_worker_drops_caches_of_older_builds():
    sw = (ROOT / "src" / "lego_creator" / "site_assets" / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE = "brick-steps";' in sw
    assert "caches.keys()" in sw and "caches.delete" in sw
    # Fonts and pinned three.js live in a cache no deploy deletes, so an update does not reload them.
    assert 'const STATIC = "brick-steps-static";' in sw and "n !== STATIC" in sw
    assert "const FONTS = [];" in sw and "fonts.g" not in sw
