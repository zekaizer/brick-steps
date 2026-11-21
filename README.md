<p align="center">
  <img src="design/brand/brick-steps-lockup.svg" alt="Brick Steps" width="420">
</p>

<p align="center"><b>AI와 함께 만들고, 한 단계씩 따라 해요</b><br>Designed with AI. Built step by step.</p>

Brick Steps is a set of original robots for LEGO® SPIKE™ Prime, designed together with AI and kept as LDraw models. Each robot is published as a step-by-step manual that elementary-school kids can follow on their own, on an iPad.

**Manuals:** https://zekaizer.github.io/brick-steps/. You can add the site to an iPad home screen, and any manual you have opened keeps working offline.

![The gallery, a build step and the finished screen on an iPad mini](docs/images/brick-steps-ipad.png)

## What's here

- `models/`: one folder per robot. It holds the LDraw model (`model.mpd`), design notes and the Pybricks program.
- `lc validate <model>`: checks a model against the LDraw library and the kits it may use, including parts, colors, rotations and hub ports.
- `lc site`: renders every step with LeoCAD and builds the manual site and PDFs that GitHub Pages serves.
- `design/`: the Brick Steps design tokens and logo, synced from the design system.

## Quick start

```bash
uv sync
uv run lc fetch-ldraw
uv run lc validate <model>
uv run lc site --include-drafts   # needs LeoCAD 25.09 and Xvfb
```

`CLAUDE.md` describes the layout and rules, `docs/adr/` records the design decisions, and `docs/releasing.md` covers versioning.

## Credits and licenses

- Code is under the MIT license (`LICENSE`). Building designs, manuals and the Brick Steps logo are under CC BY-SA 4.0 (`LICENSE-CONTENT.md`).
- Kit inventories are derived from [Rebrickable](https://rebrickable.com) catalog data.
- Part geometry comes from the [LDraw.org Parts Library](https://library.ldraw.org) (CC BY 4.0). The library is not redistributed here.
- Step images are rendered with [LeoCAD](https://www.leocad.org). The wordmark is set in [Lexend](https://www.lexend.com) (SIL OFL 1.1).

LEGO® and SPIKE™ are trademarks of the LEGO Group, which does not sponsor, authorize or endorse this project.
