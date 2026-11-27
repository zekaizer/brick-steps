"""Fonts cut down to the characters the site shows (ADR 0004)."""

import hashlib
import re
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

from lego_creator.fonts import SOURCES, fetch_fonts, uncovered, used_chars, write_fonts

CACHE = Path(__file__).resolve().parents[1] / ".cache" / "fonts"
needs_fonts = pytest.mark.skipif(not all((CACHE / s.file_name).is_file() for s in SOURCES),
                                 reason="source fonts not in .cache/fonts (lc site downloads them)")


def test_used_characters_are_printable_ascii_and_every_other_character_once():
    chars = used_chars(["탱크 1호\n", "<b>만들기</b> 탱크 ·"])
    assert set("탱크호만들기·") <= set(chars) and all(chr(c) in chars for c in range(0x20, 0x7F))
    assert "\n" not in chars and len(chars) == len(set(chars)) == 95 + 7


def test_a_cached_font_that_is_not_the_pinned_file_is_refused(tmp_path):
    for source in SOURCES:
        (tmp_path / source.file_name).write_bytes(b"not a font")
    with pytest.raises(ValueError, match=r"NotoSansKR\[wght\]\.ttf is not the pinned"):
        fetch_fonts(tmp_path)


def faces(css):
    """{file slug: {family, file, weight, range}} of each @font-face rule."""
    return {m["file"].rsplit("-", 1)[0]: m.groupdict() for m in re.finditer(
        r'@font-face \{ font-family: "(?P<family>[^"]+)"; src: url\("fonts/(?P<file>[^"]+)"\) format\("woff2"\); '
        r"font-weight: (?P<weight>[\d ]+);(?: unicode-range: (?P<range>[^;]+);)? font-display: block; \}", css)}


@needs_fonts
def test_each_font_keeps_only_the_used_characters_and_weights_in_a_file_named_after_its_bytes(tmp_path):
    dest = tmp_path / "assets" / "fonts"
    dest.mkdir(parents=True)
    (dest / "noto-sans-kr-000000000000.woff2").write_bytes(b"from an earlier build")
    chars = used_chars(["탱크 만들기"])

    css = write_fonts(dest, fetch_fonts(CACHE), chars)

    found = faces(css)
    assert {slug: (v["family"], v["weight"], v["range"]) for slug, v in found.items()} == {
        "noto-sans-kr": ("Noto Sans KR", "400 700", None), "lexend": ("Lexend", "600 700", None)}
    assert sorted(p.name for p in dest.iterdir()) == sorted(v["file"] for v in found.values())
    for slug in ("noto-sans-kr", "lexend"):
        name = found[slug]["file"]
        assert name == f"{slug}-{hashlib.sha256((dest / name).read_bytes()).hexdigest()[:12]}.woff2"
    noto, lexend = (TTFont(dest / found[slug]["file"]) for slug in ("noto-sans-kr", "lexend"))
    assert {chr(c) for c in noto.getBestCmap()} == set(chars)
    assert {chr(c) for c in lexend.getBestCmap()} == {chr(c) for c in range(0x20, 0x7F)}
    assert [(a.axisTag, a.minValue, a.maxValue) for a in noto["fvar"].axes] == [("wght", 400, 700)]
    assert [(a.axisTag, a.minValue, a.maxValue) for a in lexend["fvar"].axes] == [("wght", 600, 700)]
    assert [noto["name"].getDebugName(1), lexend["name"].getDebugName(1)] == ["Noto Sans KR", "Lexend SemiBold"]
    assert write_fonts(dest, fetch_fonts(CACHE), chars) == css


@needs_fonts
def test_symbols_noto_sans_kr_lacks_come_from_noto_sans_math_under_its_name(tmp_path):
    css = write_fonts(tmp_path / "fonts", fetch_fonts(CACHE), used_chars(["다시 ↻ ↺ 보기 ▶ ▾"]))
    math = faces(css).get("noto-sans-math", {})
    assert (math.get("family"), math.get("weight"), math.get("range")) == ("Noto Sans KR", "400 700",
                                                                           "U+21BA, U+21BB, U+25BE")
    assert {chr(c) for c in TTFont(tmp_path / "fonts" / math["file"]).getBestCmap()} == set("↺↻▾")


@needs_fonts
def test_characters_no_font_has_are_named():
    assert uncovered(fetch_fonts(CACHE), used_chars(["다시 ↻ 보기 ▶ ▾ 🧱"])) == "🧱"


@needs_fonts
def test_site_fonts_cover_the_pages_scripts_and_stylesheet(tmp_path, capsys):
    from lego_creator.export import ExportEnv, finish_manuals

    assets = tmp_path / "assets"
    assets.mkdir()
    (tmp_path / "index.html").write_text("<p>탱크</p>", encoding="utf-8")
    (assets / "manual.js").write_text('label = "다시 🧱";', encoding="utf-8")
    (assets / "viewer3d.js").write_text("", encoding="utf-8")
    (assets / "site.css").write_text('.done::before { content: "★"; }\n', encoding="utf-8")

    finish_manuals(tmp_path, [], ExportEnv(tmp_path, tmp_path, {}, tmp_path, CACHE), pdf=False)

    noto = TTFont(next((assets / "fonts").glob("noto-sans-kr-*.woff2")))
    assert set("탱크다시★") <= {chr(c) for c in noto.getBestCmap()}
    assert '@font-face { font-family: "Noto Sans KR"' in (assets / "site.css").read_text(encoding="utf-8")
    assert "warning: no site font has 🧱; it shows in the device's font" in capsys.readouterr().out
