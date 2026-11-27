# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). The release process is in `docs/releasing.md`.

## [Unreleased]

### Added
- In the 3D step view each new part comes in the way it is put on: a pin along its own axis, a beam, the hub or a gear along the pins or axle it goes onto, a track from the side. Parts that go onto others in the same step wait their turn. A yellow arrow shows the way in just before a part that does not come from above moves, and stays beside it.
- `lc insertions <slug>` lists, in build order, the side each part comes in from, how far it travels and in which wave, what it goes into or onto and what is in its way.
- `0 !LC INSERT FROM <side>` above a reference in a model sets the side its part comes in from. `lc validate` checks these lines and warns when the path from that side runs into an earlier part or when the side is the one the part would take anyway.
- `lc site --render-cache DIR` reuses step pictures and part thumbnails from an earlier build when nothing they depend on changed (the model, the LDraw files it uses, the colours, LeoCAD), and the Pages build keeps them between runs.
- The cable card also lists a motor or sensor built as its own sub-assembly beside the hub, and lists cables by port letter.
- `lc bom <slug> --left` lists what the model's kits still hold once the model is built, by kit part and colour.
- 비행기 1호 is published in the gallery.
- 비행기 1호: an A-10 at about 1:42, 42 cm across, with a raised canopy, a gun under the nose turned through bevel gears, two engine pods whose intakes spin on one motor, tapered wings with a rounded leading edge, four missile racks and twin fins.
- 탱크 1호 is published in the gallery.
- 탱크 4호 (draft, in the lab): tank 1 with rhombus tracks around a high front horn and a road wheel sprung by a rubber band.
- 탱크 3호 (draft, in the lab): tank 2 with an LMS-ESP32 board on port D for driving from a Bluetooth gamepad.
- 탱크 2호 (draft, in the lab): tank 1 with a low, wide turret on the large turntable, turned a full circle by a medium motor, fenders over the tracks and turret missions.
- The screen stays on while a manual is open (where the browser supports it), so the iPad does not lock between steps.
- `lc validate` warns when a moving sub-assembly declared with `0 !LC TURN` runs into the rest of the model within its declared range, and when a part comes within a plate of the floor set by `0 !LC GROUND` (wheels, tracks). Both are box approximations.
- Brick Steps branding: a logo of two stacked bricks with sparkles, the tagline "AI와 함께 만들고, 한 단계씩 따라 해요", app and maskable icons, and favicons. The gallery shows the logo and tagline.
- Manuals show each step as a 3D model that can be turned with a finger. New parts drop into place with a yellow outline, and the finished model turns on the last screen. Devices without WebGL, and the PDF, keep the rendered pictures.
- Models are named by series and number (`tank-1`, "탱크 1호"). `lc new <series>` picks the next number and `--from` starts from an existing model, `lc revise` records revisions with a date and note, and `lc list` shows every model with its status, revision and base model.
- `lc validate` also checks a model's catalog fields and its missions.
- After the finished model, manuals show "움직여 보기" mission cards: SPIKE App word blocks drawn in their palette colors, with a question that invites one change. The cover shows the model's one-line story.
- Mission blocks look like the SPIKE App's: as wide as their words, joined by notches, a hat on event blocks, C-shaped repeat blocks, white number inputs and darker dropdowns.
- A "케이블을 꽂아요" card right after the hub and its motors are placed. It lists each port letter with the device to plug in, and in 3D draws each cable as a flat ribbon in its port's color, from the device around the hub into a real-size plug, with the port letter beside it. The cables slide into their ports when the card opens, and other parts fade so the cables stay in sight.
- A section bar at the top of every manual screen jumps straight to 조립, 케이블, 완성 or 움직여 보기, and its 목차 button opens a sheet with a tile for every screen, ticking the steps already seen. The bar starts with the Brick Steps mark, which leads back to the gallery. It replaces the step progress line.
- The gallery and lab end with the site version and "만든 사람 Luke Lee". Manual covers show the model's version, and the finished screen names the maker.
- A hidden lab at `/lab/` shows models that are still drafts, marked as untested. Tap the gallery logo five times to open it.

### Changed
- Every device shows the site and the PDF manuals in the same letters: the fonts come with the site, cut down to the characters its pages use, instead of from Google Fonts, where a slow first load left the page in the device's own font (ADR 0004).
- Buttons are lighter: everything a child taps is at least 48 px instead of 56 px, the portrait Back and Next buttons fit their words at either end instead of filling the width, and a mission's question is as wide as its text.
- The footer shows the site version as v0.0.1.
- Steps no longer change by swiping, which fired when a finger slipped; the buttons, section bar and contents move between them.
- Touch is calmer for children on an iPad: double-tap never zooms on any page, holding a finger does not select text or open an image menu, the page does not rubber-band, pressed buttons shrink slightly instead of flashing grey, and tapping beside the map sheet closes it.
- Larger text for what children read: the step total sits next to the step number, sub-assembly names, hints and mission numbers use body size or more, and 완성! is bigger. Part pictures are larger with the count on their corner, the lab's back link is a button, the map's title moved under the logo, an empty home page says the first model is on its way, and in landscape mission blocks sit in the middle.
- Each deploy starts a fresh offline cache and removes the old one, and an open page reloads once when the new version takes over. Manuals opened before an update have to be opened again to be read offline.
- 탱크 1호 builds its turret head (cross block and barrels) as a small sub-assembly before setting it on the pin.
- The home page and the lab are an adventure map instead of a list: a road per series with a stop per model, a 곧 나와요 stop at the end, and dotted lines to the model another series grew from. Tapping a stop opens a sheet with the story and a start button. Stops reached to the finished screen on this device show ✓ 다 만들었어요, which a small two-tap link in the sheet can clear (the model itself stays), and the first unbuilt stop says 다음은 여기!
- Manuals fit one card on the iPad mini screen without scrolling, in portrait and in landscape. In landscape the step number, parts and buttons sit in a panel beside a larger picture, and the gallery shows three models per row.
- `lc site` always builds drafts into the lab; `--include-drafts` is gone.
- Models no longer keep Pybricks programs. Children program in the SPIKE App with word blocks, so `lc new` writes `missions.yaml` instead of `program/main.py`.
- Headings use Lexend with Noto Sans KR instead of Jua.
- The repository is now github.com/zekaizer/brick-steps, and the manuals are served at https://zekaizer.github.io/brick-steps/. The old lego-creator Pages address no longer works.

### Fixed
- Opening the finished model, or any step, the first time no longer freezes the manual. 비행기 1호 used to stand still for about 13 seconds after a tap on 완성. The 3D model is now prepared in the background, starting as the manual opens, and until it is ready the step picture shows with a "곧 돌려 볼 수 있어요" pill.
- 탱크 2호 and 탱크 3호 (lab): the turret motor and its mount are built first as their own sub-assembly, because the pins beside the motor cannot be pushed in once it sits between the frames.
- 탱크 4호 (lab): the horn idlers and road wheels can no longer slide along their axles, and the rubber band's pins go in before the road wheel covers them.
- 비행기 1호's gun barrels and engine fans have a bush in front of them, so they cannot slide off the end of their axles.
- Rebuilding a manual no longer picks up step pictures left from an earlier build, which could show an old picture as a sub-assembly's result or as the cover.
- 탱크 2호 and 탱크 3호 (lab): the fenders and the turret axle no longer show two pins, or a pin and an axle, in one hole; the turret axle now sits 20 LDU deep in the motor instead of 10.
- The first screen after an update no longer starts large and then shrinks: fonts stay cached across updates, and a font that is not ready when the page appears is not swapped in mid-view.
- After an update, a manual opened before could show its old page with the new styles, which broke the layout. The site now loads pages, styles and scripts from the network first and uses the offline copy only when the network is missing or slow.
- Tapping twice quickly on an iPad no longer zooms the page.
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
