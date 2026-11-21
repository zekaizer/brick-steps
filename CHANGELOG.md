# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). The release process is in `docs/releasing.md`.

## [Unreleased]

### Fixed
- The GitHub Pages build no longer fails in its container: git now trusts the checkout, so the site deploys.

## [0.0.1] - 2026-11-22

First beta.

### Added
- `lc` command line: `new`, `validate`, `bom`, `fetch-ldraw`, `import-inventory`, `instructions`, `site` and `release-check`.
- Model checks: line syntax, rotation matrices, LDConfig colors, missing and alias parts, kit inventory (set quantities and unknown counts) and hub port metadata.
- Kit inventories for SPIKE Prime 45678 and expansion 45681 (Rebrickable data), the LMS-ESP32 v2 board (custom LDraw part and mount template) and a third-party tank track set.
- Kid-facing Korean manuals and gallery for iPad mini: LeoCAD-rendered steps, a parts tray per step, the Brick Steps design, offline use as a home-screen app, and PDF export. Deployed to GitHub Pages.
- Release process with changelog and version checks.

[Unreleased]: https://github.com/zekaizer/lego-creator/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/zekaizer/lego-creator/releases/tag/v0.0.1
