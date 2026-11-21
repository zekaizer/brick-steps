# lego-creator

Original LEGO® SPIKE™ Prime robots, kept as LDraw models and published as step-by-step manuals for kids.

**Manuals:** https://zekaizer.github.io/lego-creator/ (add it to an iPad home screen; manuals you have opened keep working offline)

## What's here

- `models/` — one folder per robot: the LDraw model (`model.mpd`), design notes and the Pybricks program
- `lc validate <model>` — checks a model against the LDraw library and the kits it may use
- `lc site` — renders every step with LeoCAD and builds the manual site and PDFs that GitHub Pages serves

## Quick start

```bash
uv sync
uv run lc fetch-ldraw
uv run lc validate <model>
uv run lc site --include-drafts   # needs LeoCAD 25.09 and Xvfb
```

See `CLAUDE.md` for the layout and rules, and `docs/adr/` for the design decisions.

## Credits and licenses

- Code: MIT (`LICENSE`). Building designs and manuals: CC BY-SA 4.0 (`LICENSE-CONTENT.md`).
- Kit inventories are derived from [Rebrickable](https://rebrickable.com) catalog data.
- Part geometry: [LDraw.org Parts Library](https://library.ldraw.org) (CC BY 4.0). It is not redistributed here.
- Step images are rendered with [LeoCAD](https://www.leocad.org).

LEGO® and SPIKE™ are trademarks of the LEGO Group, which does not sponsor, authorize or endorse this project.
