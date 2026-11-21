import json

from lego_creator.site import (
    GalleryCard,
    ManualView,
    CableItem,
    CableView,
    MissionView,
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


def test_only_ready_models_go_to_the_gallery():
    assert is_published({"status": "ready"})
    assert not is_published({"status": "draft"}) and not is_published({})


def test_gallery_logo_leads_to_the_hidden_lab():
    html = gallery_html([])
    assert 'data-lab="lab/"' in html and 'href="lab/' not in html


def test_lab_gallery_marks_every_card_as_in_progress_and_hides_from_search():
    html = gallery_html([GalleryCard("tank-1", "탱크 1호", "tank-1/img/hero.png", 114, 14)], lab=True)
    assert '<meta name="robots" content="noindex">' in html
    assert "실험실" in html and "만드는 중" in html and 'href="tank-1/"' in html
    assert 'href="../assets/site.css"' in html and 'src="../brand/brick-steps-lockup.svg"' in html
    assert 'data-sw="../sw.js"' in html and 'href="../"' in html and "data-lab" not in html
    assert "실험실이 비어 있어요" in gallery_html([], lab=True)


def test_draft_manual_says_it_is_untested_and_hides_from_search():
    draft = ManualView("tank-1", "탱크 1호", 1, "img/hero.png", [StepView(1, "img/s0-01.png")], draft=True)
    html = manual_html(draft, assets="../../assets/")
    assert '<meta name="robots" content="noindex">' in html and "아직 만들어 보지 않은 설계예요" in html
    plain = manual_html(VIEW, assets="./")
    assert "noindex" not in plain and "아직 만들어 보지 않은" not in plain


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


VIEW_3D = ManualView(
    slug="tank",
    name="탱크 로봇",
    part_count=42,
    hero="img/hero.png",
    model3d="model3d.txt",
    main_sub="main.ldr",
    steps=[
        StepView(1, "img/s0-01.png", sub="wheels.ldr", shown=2, fresh=2),
        StepView(2, "img/s1-01.png", sub="main.ldr", shown=3, fresh=1),
    ],
    done_shown=3,
)


def test_manual_html_tells_the_3d_view_what_each_step_shows():
    html = manual_html(VIEW_3D, assets="../assets/")
    assert 'data-model3d="model3d.txt"' in html
    assert 'data-sub="wheels.ldr" data-shown="2" data-fresh="2"' in html
    assert 'data-sub="main.ldr" data-shown="3" data-fresh="1"' in html
    assert 'data-sub="main.ldr" data-shown="3" data-fresh="0"' in html  # finished model on the done card
    assert '"three": "../assets/vendor/three/three.module.min.js"' in html
    assert '"three/addons/": "../assets/vendor/three/addons/"' in html
    assert '<script type="module" src="../assets/viewer3d.js"></script>' in html
    assert html.index('type="importmap"') < html.index("viewer3d.js")
    assert "LDraw.org Parts Library" in html


def test_manual_html_keeps_step_images_as_the_fallback_under_3d():
    html = manual_html(VIEW_3D, assets="../assets/")
    assert 'src="img/s0-01.png"' in html and 'src="img/s1-01.png"' in html


def test_manual_html_without_3d_or_in_print_has_no_3d_hooks():
    for html in (manual_html(VIEW, assets="./"), manual_html(VIEW_3D, assets="./", print_mode=True)):
        assert "data-model3d" not in html and "viewer3d.js" not in html and "importmap" not in html
        assert "data-sub" not in html


VIEW_STORY = ManualView(
    slug="tank-1",
    name="탱크 1호",
    part_count=10,
    hero="img/hero.png",
    steps=[StepView(1, "img/s0-01.png")],
    intro="울퉁불퉁한 길도 잘 가요.",
    missions=[
        MissionView("앞뒤로 달리기", "앞으로 갔다가 돌아와요.", '<ol class="blocks"><li>B</li></ol>', "2를 3으로 바꾸면?"),
        MissionView("빙글 돌기", "제자리에서 돌아요.", '<ol class="blocks"><li>C</li></ol>', ""),
    ],
)


def test_manual_html_tells_the_story_on_the_cover():
    html = manual_html(VIEW_STORY, assets="./")
    cover = html[html.index('id="cover"'):html.index('id="step-1"')]
    assert "울퉁불퉁한 길도 잘 가요." in cover


def test_manual_html_adds_a_card_per_mission_after_the_finished_model():
    html = manual_html(VIEW_STORY, assets="./")
    assert html.index('id="done"') < html.index('id="mission-1"') < html.index('id="mission-2"')
    one = html[html.index('id="mission-1"'):html.index('id="mission-2"')]
    assert 'class="card mission"' in one and "움직여 보기 1 / 2" in one
    assert "앞뒤로 달리기" in one and "앞으로 갔다가 돌아와요." in one and "<li>B</li>" in one
    assert "2를 3으로 바꾸면?" in one
    two = html[html.index('id="mission-2"'):]
    assert 'class="try' not in two


def test_manual_html_keeps_missions_in_print():
    html = manual_html(VIEW_STORY, assets="./", print_mode=True)
    assert 'id="mission-1"' in html and 'id="mission-2"' in html


def test_site_css_stops_double_tap_zoom():
    from pathlib import Path

    css = (Path(__file__).resolve().parents[1] / "src" / "lego_creator" / "site_assets" / "components.css").read_text()
    assert "touch-action: manipulation" in css


VIEW_CABLES = ManualView(
    slug="tank-1",
    name="탱크 1호",
    part_count=10,
    hero="img/hero.png",
    steps=[StepView(1, "img/s0-01.png", sub="main.ldr", shown=2, fresh=2), StepView(2, "img/s0-02.png", sub="main.ldr", shown=3, fresh=1)],
    model3d="model3d.txt",
    main_sub="main.ldr",
    cables=CableView(after=1, sub="main.ldr", shown=2, image="img/s0-01.png",
                     items=[CableItem("A", "왼쪽 큰 모터", "parts/54675-322.png"), CableItem("B", "오른쪽 큰 모터", "parts/54675-322.png")],
                     lines='[{"port": "A", "from": [1, 2, 3], "to": [4, 5, 6]}]', keep="[0, 1]"),
)


def test_manual_html_puts_the_cable_card_right_after_its_step():
    html = manual_html(VIEW_CABLES, assets="../assets/")
    assert html.index('id="step-1"') < html.index('id="cables"') < html.index('id="step-2"')
    card = html[html.index('id="cables"'):html.index('id="step-2"')]
    assert "케이블을 꽂아요" in card and "왼쪽 큰 모터" in card and "오른쪽 큰 모터" in card
    assert '<span class="port port-a t-heading">A</span>' in card and 'src="parts/54675-322.png"' in card
    assert '<span class="port port-b t-heading">B</span>' in card
    assert 'data-sub="main.ldr" data-shown="2" data-fresh="0"' in card
    assert "data-cables=" in card and "&quot;port&quot;: &quot;A&quot;" in card and 'data-keep="[0, 1]"' in card


def test_cable_card_in_print_has_no_3d_hooks():
    html = manual_html(VIEW_CABLES, assets="./", print_mode=True)
    card = html[html.index('id="cables"'):html.index('id="step-2"')]
    assert "케이블을 꽂아요" in card and "data-cables" not in card


def _card(html: str, card_id: str) -> str:
    start = html.index(f'id="{card_id}"')
    return html[start:html.index("</section>", start)]


def test_every_card_splits_into_info_and_picture():
    html = manual_html(VIEW_CABLES, assets="../assets/")
    for card_id in ("cover", "step-1", "cables", "done"):
        card = _card(html, card_id)
        assert '<div class="side">' in card and '<div class="main">' in card, card_id
        assert card.index('<div class="side">') < card.index('<div class="main">'), card_id
    step = _card(html, "step-1")
    side, main = step.split('<div class="main">')
    assert "step-head" in side and "<figure" in main and "<figure" not in side
    assert 'class="hero"' in _card(html, "cover").split('<div class="main">')[1]


def test_mission_card_puts_the_blocks_beside_the_goal():
    view = ManualView("t", "t", 1, "h.png", [StepView(1, "a.png")],
                      missions=[MissionView("앞뒤로", "앞으로 가요.", '<ul class="blocks"></ul>', "바꿔 봐요")])
    side, main = _card(manual_html(view, assets="./"), "mission-1").split('<div class="main">')
    assert "앞뒤로" in side and "바꿔 봐요" in side and 'class="blocks"' in main


def test_web_manifest_allows_both_orientations():
    assert json.loads(web_manifest("#fff"))["orientation"] == "any"


def test_site_css_has_a_landscape_layout_and_fills_the_screen():
    from pathlib import Path

    css = (Path(__file__).resolve().parents[1] / "src" / "lego_creator" / "site_assets" / "components.css").read_text()
    assert "(orientation: landscape)" in css and "var(--side-panel)" in css and "100dvh" in css


VIEW_ALL = ManualView(
    slug="tank-1", name="탱크 1호", part_count=10, hero="img/hero.png",
    steps=[StepView(1, "img/s0-01.png"), StepView(2, "img/s0-02.png")],
    cables=CableView(after=1, sub="main.ldr", shown=2, image="img/s0-01.png", items=[CableItem("A", "큰 모터", "p.png")]),
    missions=[MissionView("앞뒤로", "", '<ul class="blocks"></ul>'), MissionView("돌기", "", '<ul class="blocks"></ul>')],
)


def test_section_bar_jumps_to_each_part_of_the_manual():
    html = manual_html(VIEW_ALL, assets="../assets/")
    bar = html[html.index('<nav class="chapters"'):html.index("</nav>")]
    assert "hidden" in bar[:bar.index(">")]
    links = [('href="#step-1"', "조립"), ('href="#cables"', "케이블"), ('href="#done"', "완성"), ('href="#mission-1"', "움직여 보기")]
    positions = [bar.index(href) for href, _ in links]
    assert positions == sorted(positions) and all(word in bar for _, word in links)
    assert 'class="toc' in bar and "목차" in bar
    assert 'class="progress"' not in html


def test_section_bar_leaves_out_missing_parts():
    bar = manual_html(VIEW, assets="./")
    bar = bar[bar.index('<nav class="chapters"'):]
    bar = bar[:bar.index("</nav>")]
    assert "#cables" not in bar and "움직여 보기" not in bar and 'href="#step-1"' in bar


def test_cards_name_their_section():
    html = manual_html(VIEW_ALL, assets="./")
    for card_id, chapter in (("step-1", "build"), ("step-2", "build"), ("cables", "cables"), ("done", "done"),
                             ("mission-2", "play")):
        start = html.index(f'id="{card_id}"')
        assert f'data-chapter="{chapter}"' in html[html.rindex("<section", 0, start):start + 40], card_id


def test_contents_has_a_tile_for_every_card():
    html = manual_html(VIEW_ALL, assets="./")
    dialog = html[html.index('<dialog class="contents"'):html.index("</dialog>")]
    for card_id in ("cover", "step-1", "cables", "step-2", "done", "mission-1", "mission-2"):
        assert f'href="#{card_id}"' in dialog, card_id
    assert 'src="img/s0-02.png"' in dialog and "닫기" in dialog
    assert dialog.count('class="play-mark') == 2


def test_section_bar_shows_the_brand_mark_linking_home():
    html = manual_html(VIEW_ALL, assets="../../assets/", brand="../../brand/")
    bar = html[html.index('<nav class="chapters"'):html.index("</nav>")]
    assert 'href="../" aria-label="처음으로"' in bar and 'src="../../brand/brick-steps-mark.svg"' in bar
    assert "brick-steps-mark" not in manual_html(VIEW_ALL, assets="./")


def test_print_has_no_section_bar_or_contents():
    html = manual_html(VIEW_ALL, assets="./", brand="../brand/", print_mode=True)
    assert 'class="chapters"' not in html and "<dialog" not in html


def test_cover_shows_the_model_version_and_done_names_the_maker():
    view = ManualView("t", "탱크 1호", 1, "h.png", [StepView(1, "a.png")], version=3)
    html = manual_html(view, assets="./")
    assert "버전 3" in _card(html, "cover") and "만든 사람 Luke Lee" in _card(html, "done")
    assert "버전" not in _card(manual_html(ManualView("t", "t", 1, "h.png", [StepView(1, "a.png")]), assets="./"), "cover")


def test_gallery_and_lab_footer_show_site_version_and_maker():
    for html in (gallery_html([], version="0.0.1"), gallery_html([], lab=True, version="0.0.1")):
        foot = html[html.index("<footer"):html.index("</footer>")]
        assert "Brick Steps 0.0.1" in foot and "만든 사람 Luke Lee" in foot
