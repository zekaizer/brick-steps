import json

from lego_creator.site import (
    GalleryCard,
    ManualView,
    StepView,
    TrayItem,
    gallery_html,
    is_published,
    manual_html,
    web_manifest,
)

VIEW = ManualView(
    slug="tank",
    name="탱크 로봇",
    part_count=42,
    hero="img/hero.png",
    pdf="manual.pdf",
    steps=[
        StepView(1, "img/s0-01.png", [TrayItem("thumbs/3020-15.png", 2, "3020")], section_title="바퀴 묶음"),
        StepView(2, "img/s1-01.png", [TrayItem("img/s0-01.png", 2, "바퀴 묶음", is_submodel=True)]),
    ],
)


def test_manual_html_is_korean_tablet_page_with_pwa_links():
    html = manual_html(VIEW, assets="../assets/", sw="../sw.js", manifest="../manifest.webmanifest")
    assert '<html lang="ko">' in html
    assert 'name="viewport"' in html and "viewport-fit=cover" in html
    assert 'href="../manifest.webmanifest"' in html and 'data-sw="../sw.js"' in html
    assert 'href="../assets/site.css"' in html and 'src="../assets/manual.js"' in html
    assert "apple-mobile-web-app-capable" in html


def test_manual_html_has_cover_steps_and_done_cards():
    html = manual_html(VIEW, assets="./")
    assert html.count('class="card step"') == 2
    assert 'id="cover"' in html and 'id="done"' in html and "완성!" in html
    assert "탱크 로봇" in html and "부품 42개 · 2단계" in html
    assert "1 / 2 단계" in html and "2 / 2 단계" in html
    assert "필요한 부품" in html and "×2" in html
    assert 'class="sub-label t-caption">바퀴 묶음<' in html
    assert 'class="sub"' in html
    assert 'href="manual.pdf"' in html


def test_manual_html_escapes_names():
    view = ManualView("x", "<b>&", 1, "h.png", [StepView(1, "a.png")])
    assert "<b>&" not in manual_html(view, assets="./") and "&lt;b&gt;&amp;" in manual_html(view, assets="./")


def test_print_mode_has_no_script_or_pager():
    html = manual_html(VIEW, assets="./", print_mode=True)
    assert "<script" not in html and 'class="pager"' not in html


def test_gallery_lists_cards_and_has_empty_state():
    html = gallery_html([GalleryCard("tank", "탱크 로봇", "tank/img/hero.png", 42, 12)])
    assert 'href="tank/"' in html and "부품 42개 · 12단계" in html and "무엇을 만들까요?" in html
    assert 'rel="manifest"' in html
    assert "아직 완성된 작품이 없어요" in gallery_html([])


def test_web_manifest_is_standalone_app():
    m = json.loads(web_manifest("#f2f7f8"))
    assert m["display"] == "standalone" and m["start_url"] == "./" and m["lang"] == "ko"
    assert m["background_color"] == "#f2f7f8" and {i["sizes"] for i in m["icons"]} == {"192x192", "512x512"}


def test_only_ready_models_publish_unless_drafts_included():
    assert is_published({"status": "ready"}, False)
    assert not is_published({"status": "draft"}, False)
    assert is_published({"status": "draft"}, True)


def test_pages_load_brand_fonts_and_favicons():
    html = manual_html(VIEW, assets="../assets/", sw="../sw.js", manifest="../manifest.webmanifest")
    assert "family=Lexend" in html and "Jua" not in html
    assert 'rel="icon" type="image/svg+xml" href="../favicon.svg"' in html
    assert 'rel="icon" type="image/png" sizes="32x32" href="../favicon-32.png"' in html
    assert 'rel="apple-touch-icon" href="../apple-touch-icon.png"' in html


def test_gallery_header_shows_logo_and_tagline():
    html = gallery_html([])
    assert '<img class="brand" src="brand/brick-steps-lockup.svg" alt="Brick Steps"' in html
    assert "AI와 함께 만들고, 한 단계씩 따라 해요" in html


def test_web_manifest_has_maskable_icon():
    icons = json.loads(web_manifest("#f2f7f8"))["icons"]
    assert {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"} in icons
