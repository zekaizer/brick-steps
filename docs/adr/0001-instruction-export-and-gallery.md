# 1. Instruction export and gallery: LeoCAD renders, HTML + PDF, GitHub Pages

Date: 2026-11-22

## Status

Accepted

## Context

Each model in `models/<slug>/model.mpd` must be exportable as building instructions. They do not need to be as detailed as official LEGO books, but someone has to be able to follow them. People must be able to read them on an iPad mini, so the page has to work in mobile Safari in portrait (about 744 CSS px wide).

The instructions are for elementary-school children reading in Korean. The maintainer works in the repository and with Claude, so the site needs no management pages.

The models should also be browsable as a gallery. The gallery is served by GitHub from this repository, so it can be opened on any device without running anything locally.

The work runs on a headless Linux host and in CI. These options were considered:

- **LPub3D.** It produces full instruction books, but it is GUI-centric and distributed as an AppImage, which makes it hard to automate headlessly.
- **An in-repo Python rasterizer.** It has no external dependency, but the image quality is low and it is slow on models with hundreds of parts.
- **The LeoCAD command line.** Version 25.09 is in Ubuntu's apt. It renders step ranges (`-f`/`-t`), takes a submodel (`-s`), highlights the parts new in each step (`--highlight`), and runs under `xvfb-run`. A 4-step model renders in under a second. Custom parts are found when they are embedded in the MPD as `0 FILE` blocks.

## Decision

- **Rendering.** `lc` calls the LeoCAD CLI (`xvfb-run leocad ...`) to render step images and part thumbnails. Before rendering, custom parts from `custom/parts/` are embedded into a generated build MPD, so LeoCAD only needs the official library (`-l ldraw`).
- **Layout.** `lc` produces the layout itself as a static HTML page per model. There is one step per screen, each with the parts added in that step (thumbnail, quantity) above the step image. Sub-assemblies are shown first, as their own sections. The page is styled for tablets in portrait. The PDF is generated from the same HTML with WeasyPrint, one step per page.
- **Design.** The site follows the Brick Steps design system, a private claude.ai Design System artifact (its link is kept out of this public repository). That artifact is the single source for tokens and layout rules. The repository keeps a synced copy of its `tokens.json` under `design/`, with the artifact URL and version recorded. `lc site` compiles that copy into CSS custom properties. Nobody edits the copy by hand. Changes go to the artifact first and are then synced, because CI cannot read a private claude.ai artifact.
- **Audience and publication.** All page text is Korean and kid-facing: a gallery to pick a model, and a step-by-step manual. Only models whose `model.yaml` has `status: ready` are published. Drafts stay in the repository.
- **PWA.** The site ships a web app manifest, iOS home-screen meta tags and a service worker. The service worker serves cached pages and images first and refreshes them in the background. Once instructions have been opened, they can be read offline from the iPad home screen. It does not precache the whole site, so the cache stays proportional to what was actually viewed.
- **Hosting.** `lc site` builds a gallery (`site/index.html`) plus each model's instructions. A GitHub Actions workflow installs LeoCAD, Xvfb and the LDraw library (cached), runs `lc site`, and deploys the result to GitHub Pages. Generated images and PDFs are never committed.

## Consequences

- The `.mpd` stays the single source. Pages always reflects the default branch.
- CI and local builds need LeoCAD, Xvfb and WeasyPrint's system libraries (Pango). These are only needed for export; `lc validate` does not depend on them.
- Pages from a private repository need a paid GitHub plan, and the site is public even then (outside GitHub Enterprise). Anything in `models/` should be treated as publishable.
- LeoCAD's CLI controls the camera only through presets or angles. Per-step camera control and callout arrows are not available, so complex steps may need extra `0 STEP` splits in the model.
- Moving to LPub3D later is possible without touching the models, because the `.mpd` with `0 STEP` and `0 FILE` structure is the standard input for both tools.
