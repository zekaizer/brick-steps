"""Kid-facing manual pages, gallery and PWA shell (ADR 0001, Brick Steps design system)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape


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
    intro: str | None = None
    missions: list[MissionView] = field(default_factory=list)


@dataclass(frozen=True)
class GalleryCard:
    slug: str
    name: str
    image: str
    part_count: int
    step_count: int


FONTS = "https://fonts.googleapis.com/css2?family=Lexend:wght@600&family=Noto+Sans+KR:wght@400;500;700&display=swap"
TAGLINE = "AI와 함께 만들고, 한 단계씩 따라 해요"


def _e(text: object) -> str:
    return escape(str(text), quote=True)


def _head(title: str, *, assets: str, manifest: str | None, print_mode: bool) -> str:
    parts = [
        "<!doctype html>",
        '<html lang="ko">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
        f"<title>{_e(title)}</title>",
        f'<link rel="stylesheet" href="{FONTS}">',
        f'<link rel="stylesheet" href="{_e(assets)}site.css">',
    ]
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


def manual_html(view: ManualView, *, assets: str, sw: str | None = None, manifest: str | None = None,
                print_mode: bool = False) -> str:
    """One page holding every step as a card; manual.js shows one card at a time.

    Without JS (and in print_mode, used for the PDF) all cards are stacked.
    """
    total = len(view.steps)
    with_3d = bool(view.model3d) and not print_mode

    def hooks(sub: str | None, shown: int, fresh: int) -> str:
        if not with_3d or not sub:
            return ""
        return f' data-sub="{_e(sub)}" data-shown="{shown}" data-fresh="{fresh}"'

    cards = [
        '<section class="card cover" id="cover">'
        f'<h1 class="t-title">{_e(view.name)}</h1>'
        f'<img class="hero" src="{_e(view.hero)}" alt="완성된 {_e(view.name)}">'
        + (f'<p class="t-body intro">{_e(view.intro)}</p>' if view.intro else "")
        + f'<p class="t-body">부품 {view.part_count}개 · {total}단계</p>'
        + (f'<p class="t-caption"><a href="{_e(view.pdf)}">PDF로 보기</a></p>' if view.pdf and not print_mode else "")
        + "</section>"
    ]
    for step in view.steps:
        pct = round(100 * step.number / total) if total else 100
        label = f'<p class="sub-label t-caption">{_e(step.section_title)}</p>' if step.section_title else ""
        cards.append(
            f'<section class="card step" id="step-{step.number}">'
            '<div class="step-head">'
            f'<span class="t-step-number">{step.number}</span>'
            f'<span class="t-caption">{step.number} / {total} 단계</span>'
            "</div>"
            f'<div class="progress" aria-hidden="true"><i style="width:{pct}%"></i></div>'
            f"{label}{_tray(step.tray)}"
            f'<figure class="step-img"{hooks(step.sub, step.shown, step.fresh)}><img src="{_e(step.image)}" alt="{step.number}단계 조립 모습" loading="lazy"></figure>'
            "</section>"
        )
    cards.append(
        '<section class="card done" id="done">'
        '<p class="badge t-heading">완성!</p>'
        f'<h1 class="t-title">{_e(view.name)}</h1>'
        f'<figure class="step-img"{hooks(view.main_sub, view.done_shown, 0)}>'
        f'<img class="hero" src="{_e(view.hero)}" alt="완성된 {_e(view.name)}"></figure>'
        + ('<p class="t-caption credit">부품 모양은 LDraw.org Parts Library(CC BY 4.0)에서 왔어요.</p>' if with_3d else "")
        + "</section>"
    )
    for k, mission in enumerate(view.missions, 1):
        cards.append(
            f'<section class="card mission" id="mission-{k}">'
            f'<p class="mission-label t-caption">움직여 보기 {k} / {len(view.missions)}</p>'
            f'<h2 class="t-heading">{_e(mission.title)}</h2>'
            + (f'<p class="t-body">{_e(mission.goal)}</p>' if mission.goal else "")
            + mission.blocks
            + (f'<p class="try t-body">{_e(mission.try_)}</p>' if mission.try_ else "")
            + "</section>"
        )
    if print_mode:
        body_attrs = ' class="manual print"'
    else:
        body_attrs = ' class="manual"'
        if sw:
            body_attrs += f' data-sw="{_e(sw)}"'
        if with_3d:
            body_attrs += f' data-model3d="{_e(view.model3d)}"'
    out = [_head(f"{view.name} 만들기", assets=assets, manifest=manifest, print_mode=print_mode), f"<body{body_attrs}>",
           f'<main class="wrap deck" id="deck">{"".join(cards)}</main>']
    if not print_mode:
        out += [
            (
                '<nav class="pager" hidden><div class="pager-in">'
                '<button type="button" class="prev t-button">‹ 이전</button>'
                '<button type="button" class="next t-button">다음 ›</button>'
                "</div></nav>"
            ),
            f'<script src="{_e(assets)}manual.js" defer></script>',
        ]
    if with_3d:
        three = f"{assets}vendor/three/"
        imports = {"three": f"{three}three.module.min.js", "three/addons/": f"{three}addons/"}
        out += [
            f'<script type="importmap">{json.dumps({"imports": imports})}</script>',
            f'<script type="module" src="{_e(assets)}viewer3d.js"></script>',
        ]
    out.append("</body>\n</html>\n")
    return "\n".join(out)


def gallery_html(cards: list[GalleryCard]) -> str:
    if cards:
        items = "".join(
            f'<li><a class="model-card" href="{_e(c.slug)}/">'
            f'<img src="{_e(c.image)}" alt="" loading="lazy">'
            f'<span class="t-title">{_e(c.name)}</span>'
            f'<span class="t-caption">부품 {c.part_count}개 · {c.step_count}단계</span>'
            "</a></li>"
            for c in cards
        )
        body = f'<ul class="grid">{items}</ul>'
    else:
        body = '<p class="t-body empty">아직 완성된 작품이 없어요.</p>'
    return "\n".join([
        _head("Brick Steps", assets="assets/", manifest="manifest.webmanifest", print_mode=False),
        '<body class="gallery" data-sw="sw.js">',
        (
            '<main class="wrap"><header class="site-head">'
            '<img class="brand" src="brand/brick-steps-lockup.svg" alt="Brick Steps" width="488" height="113">'
            f'<p class="tagline t-caption">{TAGLINE}</p></header>'
            f'<h1 class="t-title">무엇을 만들까요?</h1>{body}</main>'
        ),
        '<script src="assets/manual.js" defer></script>',
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
        "orientation": "portrait",
        "background_color": paper,
        "theme_color": paper,
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }, ensure_ascii=False, indent=2)


def is_published(meta: dict, include_drafts: bool) -> bool:
    return include_drafts or meta.get("status") == "ready"
