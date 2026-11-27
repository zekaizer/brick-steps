"""Kid-facing manual pages, gallery and PWA shell (ADR 0001, Brick Steps design system)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html import escape

# Vendored three.js (ADR 0002). The version is in the path because the service worker keeps these files
# under their URL for good; sw.js lists the same folder.
THREE_DIR = "vendor/three-0.187.0/"


@dataclass(frozen=True)
class TrayItem:
    image: str
    qty: int
    label: str
    is_submodel: bool = False


@dataclass(frozen=True)
class StepView:
    number: int
    image: str
    tray: list[TrayItem] = field(default_factory=list)
    section_title: str | None = None
    sub: str | None = None  # 3D view: submodel this step builds
    shown: int = 0  # 3D view: placed references visible at this step
    fresh: int = 0  # 3D view: how many of those are new in this step
    moves: list[dict] = field(default_factory=list)  # 3D view: insertion.moves() of the new references, in order


@dataclass(frozen=True)
class CableItem:
    port: str
    label: str
    image: str


@dataclass(frozen=True)
class CableView:
    after: int  # StepView number the card follows
    sub: str
    shown: int
    image: str  # picture when there is no 3D view
    items: list[CableItem] = field(default_factory=list)
    keep: str = "[]"  # JSON list of reference indices the 3D view keeps solid while others fade
    lines: str = "[]"  # JSON for the 3D view: [{port, from, to | null, out | null}] as [x, y, z] in LDraw units


@dataclass(frozen=True)
class MissionView:
    title: str
    goal: str
    blocks: str  # HTML from missions.blocks_html
    try_: str = ""


@dataclass(frozen=True)
class ManualView:
    slug: str
    name: str
    part_count: int
    hero: str
    steps: list[StepView]
    pdf: str | None = None
    model3d: str | None = None
    main_sub: str | None = None
    done_shown: int = 0
    draft: bool = False
    cables: CableView | None = None
    intro: str | None = None
    missions: list[MissionView] = field(default_factory=list)
    version: int | None = None


@dataclass(frozen=True)
class GalleryCard:
    slug: str
    name: str
    image: str
    part_count: int
    step_count: int
    series: str = ""
    number: int = 0
    story: str | None = None
    based_on: str | None = None


TAGLINE = "AI와 함께 만들고, 한 단계씩 따라 해요"
MAKER = "만든 사람 Luke Lee"


def _e(text: object) -> str:
    return escape(str(text), quote=True)


def _head(title: str, *, assets: str, manifest: str | None, print_mode: bool, noindex: bool = False) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f"<title>{_e(title)}</title>",
        f'<link rel="stylesheet" href="{_e(assets)}site.css">',
    ]
    if noindex:
        parts.append('<meta name="robots" content="noindex">')
    if manifest and not print_mode:
        root = manifest.rsplit("/", 1)[0] + "/" if "/" in manifest else ""
        parts += [
            f'<link rel="manifest" href="{_e(manifest)}">',
            f'<link rel="icon" type="image/svg+xml" href="{_e(root)}favicon.svg">',
            f'<link rel="icon" type="image/png" sizes="32x32" href="{_e(root)}favicon-32.png">',
            f'<link rel="apple-touch-icon" href="{_e(root)}apple-touch-icon.png">',
            '<meta name="apple-mobile-web-app-capable" content="yes">',
            '<meta name="mobile-web-app-capable" content="yes">',
            '<meta name="apple-mobile-web-app-title" content="Brick Steps">',
        ]
    parts.append("</head>")
    return "\n".join(parts)


def _tray(items: list[TrayItem]) -> str:
    if not items:
        return ""
    lis = []
    for it in items:
        cls = ' class="sub"' if it.is_submodel else ""
        lis.append(
            f'<li{cls}><img src="{_e(it.image)}" alt="{_e(it.label)}" loading="lazy">'
            f'<span class="count t-count">×{it.qty}</span></li>'
        )
    return (
        '<div class="tray"><p class="tray-head t-heading">필요한 부품</p>'
        f'<ul>{"".join(lis)}</ul></div>'
    )


def _split(side: str, main: str) -> str:
    """A card's info and its picture: stacked in portrait, side by side in landscape (components.css)."""
    return f'<div class="side">{side}</div><div class="main">{main}</div>'


def _cable_card(c: CableView, hooks: str, with_3d: bool) -> str:
    items = "".join(
        f'<li><span class="port port-{_e(it.port.lower())} t-heading">{_e(it.port)}</span>'
        f'<img src="{_e(it.image)}" alt="" loading="lazy"><span class="t-body">{_e(it.label)}</span></li>'
        for it in c.items
    )
    lines = f' data-cables="{_e(c.lines)}" data-keep="{_e(c.keep)}"' if with_3d and hooks else ""
    side = (
        '<h2 class="t-heading">케이블을 꽂아요</h2>'
        '<p class="t-body">같은 글자가 적힌 포트에 꽂아요.</p>'
        f'<ul class="cable-list">{items}</ul>'
    )
    figure = f'<figure class="step-img"{hooks}{lines}><img src="{_e(c.image)}" alt="케이블을 꽂는 모습" loading="lazy"></figure>'
    return f'<section class="card cable" id="cables" data-chapter="cables">{_split(side, figure)}</section>'


def _chapters(view: ManualView, brand: str | None) -> str:
    """Section bar fixed at the top: brand mark home, a link per part of the manual, and the contents button.

    manual.js unhides it and marks the current part; without JS it stays hidden.
    """
    home = (f'<a class="home" href="../" aria-label="처음으로">'
            f'<img src="{_e(brand)}brick-steps-mark.svg" alt="" width="48" height="48"></a>') if brand else ""
    parts = [("build", "#step-1", "조립")]
    if view.cables:
        parts.append(("cables", "#cables", "케이블"))
    parts.append(("done", "#done", "완성"))
    if view.missions:
        parts.append(("play", "#mission-1", "움직여 보기"))
    links = "".join(f'<a class="chapter t-button" data-chapter="{c}" href="{href}"><span>{word}</span></a>'
                    for c, href, word in parts)
    return (f'<nav class="chapters" hidden aria-label="구간">{home}{links}'
            '<button type="button" class="toc t-button">목차</button></nav>')


def _contents(view: ManualView) -> str:
    """Contents sheet: one tile per card, opened from the section bar."""
    def tile(card_id: str, label: str, image: str | None = None, cls: str = "") -> str:
        img = (f'<img src="{_e(image)}" alt="" loading="lazy">' if image
               else '<span class="play-mark t-title" aria-hidden="true">▶</span>')
        return f'<li><a class="tile{cls}" href="#{card_id}">{img}<span class="t-heading">{_e(label)}</span></a></li>'

    tiles = [tile("cover", "처음", view.hero)]
    for step in view.steps:
        tiles.append(tile(f"step-{step.number}", str(step.number), step.image, " step"))
        if view.cables and view.cables.after == step.number:
            tiles.append(tile("cables", "케이블", view.cables.image))
    tiles.append(tile("done", "완성", view.hero))
    tiles += [tile(f"mission-{k}", f"움직여 보기 {k}", cls=" play") for k in range(1, len(view.missions) + 1)]
    return (
        '<dialog class="contents" aria-label="목차">'
        '<div class="contents-head"><h2 class="t-title">목차</h2>'
        '<button type="button" class="close t-button">닫기</button></div>'
        f'<ul class="tiles">{"".join(tiles)}</ul></dialog>'
    )



def manual_html(view: ManualView, *, assets: str, sw: str | None = None, manifest: str | None = None,
                print_mode: bool = False, brand: str | None = None) -> str:
    """One page holding every step as a card; manual.js shows one card at a time.

    Without JS (and in print_mode, used for the PDF) all cards are stacked.
    """
    total = len(view.steps)
    with_3d = bool(view.model3d) and not print_mode

    def hooks(sub: str | None, shown: int, fresh: int, moves: list[dict] | None = None) -> str:
        if not with_3d or not sub:
            return ""
        out = f' data-sub="{_e(sub)}" data-shown="{shown}" data-fresh="{fresh}"'
        if moves:
            out += f' data-moves="{_e(json.dumps(moves, separators=(",", ":")))}"'
        return out

    cover = (
        ('<p class="draft-note t-body">아직 만들어 보지 않은 설계예요. 부품이 안 맞을 수 있어요.</p>' if view.draft else "")
        + f'<h1 class="t-title">{_e(view.name)}</h1>'
        + (f'<p class="t-body intro">{_e(view.intro)}</p>' if view.intro else "")
        + f'<p class="t-body">부품 {view.part_count}개 · {total}단계</p>'
        + (f'<p class="t-caption version">버전 {view.version}</p>' if view.version else "")
        + (f'<p class="t-caption"><a href="{_e(view.pdf)}">PDF로 보기</a></p>' if view.pdf and not print_mode else "")
    )
    hero = f'<img class="hero" src="{_e(view.hero)}" alt="완성된 {_e(view.name)}">'
    cards = [f'<section class="card cover" id="cover">{_split(cover, hero)}</section>']
    for step in view.steps:
        label = f'<p class="sub-label t-button">{_e(step.section_title)}</p>' if step.section_title else ""
        side = (
            '<div class="step-head">'
            f'<span class="t-step-number">{step.number}</span>'
            f'<span class="step-total t-body">{step.number} / {total} 단계</span>'
            "</div>"
            f"{label}{_tray(step.tray)}"
        )
        figure = (f'<figure class="step-img"{hooks(step.sub, step.shown, step.fresh, step.moves)}>'
                  f'<img src="{_e(step.image)}" alt="{step.number}단계 조립 모습" loading="lazy"></figure>')
        cards.append(f'<section class="card step" id="step-{step.number}" data-chapter="build">{_split(side, figure)}</section>')
        if view.cables and view.cables.after == step.number:
            cards.append(_cable_card(view.cables, hooks(view.cables.sub, view.cables.shown, 0), with_3d))
    done = (
        '<p class="badge t-title">완성!</p>'
        f'<h1 class="t-title">{_e(view.name)}</h1>'
        + ('<p class="t-caption credit">부품 모양은 LDraw.org Parts Library(CC BY 4.0)에서 왔어요.</p>' if with_3d else "")
        + f'<p class="t-caption credit">{MAKER}</p>'
    )
    figure = (f'<figure class="step-img"{hooks(view.main_sub, view.done_shown, 0)}>'
              f'<img class="hero" src="{_e(view.hero)}" alt="완성된 {_e(view.name)}"></figure>')
    cards.append(f'<section class="card done" id="done" data-chapter="done">{_split(done, figure)}</section>')
    for k, mission in enumerate(view.missions, 1):
        side = (
            f'<p class="mission-label t-body">움직여 보기 {k} / {len(view.missions)}</p>'
            f'<h2 class="t-heading">{_e(mission.title)}</h2>'
            + (f'<p class="t-body">{_e(mission.goal)}</p>' if mission.goal else "")
            + (f'<p class="try t-body">{_e(mission.try_)}</p>' if mission.try_ else "")
        )
        cards.append(f'<section class="card mission" id="mission-{k}" data-chapter="play">{_split(side, mission.blocks)}</section>')
    if print_mode:
        body_attrs = ' class="manual print"'
    else:
        body_attrs = ' class="manual"'
        if sw:
            body_attrs += f' data-sw="{_e(sw)}"'
        if with_3d:
            body_attrs += f' data-model3d="{_e(view.model3d)}"'
    out = [_head(f"{view.name} 만들기", assets=assets, manifest=manifest, print_mode=print_mode, noindex=view.draft),
           f"<body{body_attrs}>",
           f'<main class="wrap deck" id="deck">{"".join(cards)}</main>']
    if not print_mode:
        out += [
            _chapters(view, brand),
            _contents(view),
            (
                '<nav class="pager" hidden><div class="pager-in">'
                '<button type="button" class="prev t-button">‹ 이전</button>'
                '<button type="button" class="next t-button">다음 ›</button>'
                "</div></nav>"
            ),
            f'<script src="{_e(assets)}manual.js" defer></script>',
        ]
    if with_3d:
        three = f"{assets}{THREE_DIR}"
        imports = {"three": f"{three}three.module.js", "three/addons/": f"{three}addons/"}
        out += [
            f'<script type="importmap">{json.dumps({"imports": imports})}</script>',
            f'<script type="module" src="{_e(assets)}viewer3d.js"></script>',
        ]
    out.append("</body>\n</html>\n")
    return "\n".join(out)


def _series_label(card: GalleryCard) -> str:
    """"탱크 1호" -> "탱크"; the road sign reads "탱크 길"."""
    return re.sub(r"\s*\d+호$", "", card.name) or card.series


def _map(cards: list[GalleryCard]) -> str:
    """Adventure map: a road per series, a stop per model in number order, then a 곧 나와요 stop.

    Positions are percentages of the map box (one lane per series, one column per stop), so the
    same markup fills portrait and landscape; the road SVG stretches with non-scaling strokes.
    """
    lanes: dict[str, list[GalleryCard]] = {}
    for c in sorted(cards, key=lambda c: (c.series or c.slug, c.number)):
        lanes.setdefault(c.series or c.slug, []).append(c)
    by_slug = {c.slug: c for c in cards}
    cols = max(len(v) for v in lanes.values()) + 1
    point: dict[str, tuple[float, float]] = {}
    roads, signs, stops = [], [], []
    for i, models in enumerate(lanes.values()):
        center = (i + 0.5) / len(lanes) * 100
        bend = 10 / len(lanes)
        # Columns start half a column in, leaving the road's start free for its sign.
        pts = [((k + 1) / (cols + 0.5) * 100, center + (bend if k % 2 else -bend)) for k in range(len(models) + 1)]
        d, prev = f"M 0 {center:.2f}", (0.0, center)
        for x, y in pts:
            mid = (prev[0] + x) / 2
            d += f" C {mid:.2f} {prev[1]:.2f}, {mid:.2f} {y:.2f}, {x:.2f} {y:.2f}"
            prev = (x, y)
        roads.append("".join(f'<path class="{cls}" d="{d}"/>' for cls in ("road-edge", "road", "road-line")))
        signs.append(f'<p class="sign t-heading" style="top:{center:.2f}%">{_e(_series_label(models[0]))} 길</p>')
        for (x, y), c in zip(pts, models):
            point[c.slug] = (x, y)
            base = by_slug.get(c.based_on) if c.based_on else None
            source = f' data-from="{_e(base.name)}에서 나왔어요"' if base else ""
            stops.append(
                f'<a class="stop" href="{_e(c.slug)}/" style="left:{x:.2f}%;top:{y:.2f}%" data-name="{_e(c.name)}" '
                f'data-img="{_e(c.image)}" data-story="{_e(c.story or "")}" '
                f'data-meta="부품 {c.part_count}개 · {c.step_count}단계"{source}>'
                '<span class="here t-body">다음은 여기!</span>'
                f'<span class="disc"><img src="{_e(c.image)}" alt="" loading="lazy"></span>'
                '<span class="tick t-body">✓ 다 만들었어요</span>'
                f'<span class="label t-heading">{_e(c.name)}</span></a>'
            )
        x, y = pts[-1]
        stops.append(f'<span class="stop locked" style="left:{x:.2f}%;top:{y:.2f}%">'
                     '<span class="disc"><span class="t-title">?</span></span>'
                     '<span class="label t-heading">곧 나와요</span></span>')
    branches = []
    for c in cards:
        base = by_slug.get(c.based_on) if c.based_on else None
        if base and (base.series or base.slug) != (c.series or c.slug):
            (x1, y1), (x2, y2) = point[base.slug], point[c.slug]
            mid = (y1 + y2) / 2
            branches.append(f'<path class="branch" d="M {x1:.2f} {y1:.2f} C {x1:.2f} {mid:.2f}, {x2:.2f} {mid:.2f}, {x2:.2f} {y2:.2f}"/>')
    return (
        f'<div class="map" style="--lanes:{len(lanes)};--cols:{cols}">'
        '<svg class="roads" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">'
        f'{"".join(roads)}{"".join(branches)}</svg>{"".join(signs)}{"".join(stops)}</div>'
        '<section class="sheet" hidden aria-live="polite">'
        '<button type="button" class="x t-title" aria-label="닫기">×</button>'
        '<img class="sheet-img" alt="">'
        '<div class="info"><p class="from t-caption"></p><h2 class="name t-title"></h2>'
        '<p class="story t-body"></p><p class="meta t-caption"></p>'
        '<a class="go t-button" href="#">만들기 시작 ›</a></div>'
        '<button type="button" class="clear t-caption">‘다 만들었어요’ 표시 지우기</button>'
        "</section>"
    )


def gallery_html(cards: list[GalleryCard], *, lab: bool = False, version: str | None = None) -> str:
    """The home page as an adventure map of ready models, or with lab=True the hidden lab of drafts under lab/.

    The home logo opens the lab after five taps (manual.js); nothing links to it.
    """
    up = "../" if lab else ""
    if cards:
        body = _map(cards)
    else:
        title, line = ("실험실이 비어 있어요", "새 설계가 생기면 여기에 나와요.") if lab else ("첫 작품을 만들고 있어요", "곧 여기에서 만나요!")
        body = (f'<div class="empty"><img src="{up}brand/brick-steps-mark.svg" alt="" width="96" height="96">'
                f'<p class="t-title">{title}</p><p class="t-body">{line}</p></div>')
    if lab:
        heading = ('<div class="map-title"><a class="back t-button" href="../">‹ 갤러리로</a>'
                   '<div><h1 class="t-title">실험실</h1><p class="t-body">아직 만들어 보지 않은 설계예요.</p></div></div>')
    else:
        heading = '<h1 class="map-title t-title">어디로 가 볼까요?</h1>' if cards else ""
    return "\n".join([
        _head("Brick Steps 실험실" if lab else "Brick Steps", assets=f"{up}assets/", manifest=f"{up}manifest.webmanifest",
              print_mode=False, noindex=lab),
        f'<body class="gallery" data-sw="{up}sw.js"' + ("" if lab else ' data-lab="lab/"') + ">",
        (
            '<main class="map-page"><header class="site-head">'
            f'<div class="brand-box"><img class="brand" src="{up}brand/brick-steps-lockup.svg" alt="Brick Steps" width="488" height="113">'
            f'<p class="tagline t-caption">{TAGLINE}</p></div>'
            f'{heading}</header>{body}'
            f'<footer class="site-foot t-caption">Brick Steps{" v" + _e(version) if version else ""} · {MAKER}</footer></main>'
        ),
        f'<script src="{up}assets/manual.js" defer></script>',
        "</body>\n</html>\n",
    ])


def web_manifest(paper: str) -> str:
    return json.dumps({
        "name": "Brick Steps",
        "short_name": "Brick Steps",
        "lang": "ko",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": paper,
        "theme_color": paper,
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }, ensure_ascii=False, indent=2)


def is_published(meta: dict) -> bool:
    """Ready models go to the gallery; every other model goes to the hidden lab."""
    return meta.get("status") == "ready"
