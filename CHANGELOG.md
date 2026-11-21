# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). The release process is in `docs/releasing.md`.

## [Unreleased]

### Added
- Brick Steps branding: a logo of two stacked bricks with sparkles, the tagline "AI와 함께 만들고, 한 단계씩 따라 해요", app and maskable icons, and favicons. The gallery shows the logo and tagline.
- Manuals show each step as a 3D model that can be turned with a finger. New parts drop into place with a yellow outline, and the finished model turns on the last screen. Devices without WebGL, and the PDF, keep the rendered pictures.
- Models are named by series and number (`tank-1`, "탱크 1호"). `lc new <series>` picks the next number and `--from` starts from an existing model, `lc revise` records revisions with a date and note, and `lc list` shows every model with its status, revision and base model.
- `lc validate` also checks a model's catalog fields and its missions.
- After the finished model, manuals show "움직여 보기" mission cards: SPIKE App word blocks drawn in their palette colors, with a question that invites one change. The cover shows the model's one-line story.

### Changed
- Models no longer keep Pybricks programs. Children program in the SPIKE App with word blocks, so `lc new` writes `missions.yaml` instead of `program/main.py`.
- Headings use Lexend with Noto Sans KR instead of Jua.
- The repository is now github.com/zekaizer/brick-steps, and the manuals are served at https://zekaizer.github.io/brick-steps/. The old lego-creator Pages address no longer works.

### Fixed
- `lc new --name` with a Korean name now writes the name as readable text in `model.yaml`.
- The GitHub Pages build no longer fails in its container: git now trusts the checkout, so the site deploys.

## [0.0.1] - 2026-11-22

First beta.

### Added
- `lc` command line: `new`, `validate`, `bom`, `fetch-ldraw`, `import-inventory`, `instructions`, `site` and `release-check`.
- Model checks: line syntax, rotation matrices, LDConfig colors, missing and alias parts, kit inventory (set quantities and unknown counts) and hub port metadata.
- Kit inventories for SPIKE Prime 45678 and expansion 45681 (Rebrickable data), the LMS-ESP32 v2 board (custom LDraw part and mount template) and a third-party tank track set.
- Kid-facing Korean manuals and gallery for iPad mini: LeoCAD-rendered steps, a parts tray per step, the Brick Steps design, offline use as a home-screen app, and PDF export. Deployed to GitHub Pages.
- Release process with changelog and version checks.

[Unreleased]: https://github.com/zekaizer/brick-steps/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/zekaizer/brick-steps/releases/tag/v0.0.1
