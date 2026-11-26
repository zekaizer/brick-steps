# Following a manual

A manual is one page holding a cover, one card per build step (with the parts it needs and the assembly picture), an optional cable card, a finished card and mission cards. A child moves through it one card at a time with the pager, the arrow keys, the section bar or the contents. The page remembers where the child stopped.

## Sub-features

- `cover` shows the model's name, story, `부품 N개 · M단계`, version and, when built with PDF, `PDF로 보기`.
- `pager` moves with `시작하기 ›`, `다음 ›`, `‹ 이전` and, on the last card, `처음으로`, which returns to the cover.
- `keys` moves with the left and right arrow keys.
- `address` puts the current card's id in the address (`#step-3`) and opens that card from a link.
- `resume` reopens the manual at the card where the child left off.
- `step-card` shows the step number, `N / M 단계`, the sub-assembly label, the `필요한 부품` tray and the picture or 3D view.
- `sections` jumps from the section bar (`조립`, `케이블`, `완성`, `움직여 보기`) and the `목차` dialog.
- `done` shows `완성!` and marks the model as built on the map.

## How to get to it (user POV)

- Tap a stop on the map and then `만들기 시작 ›`.
- Open `SLUG/` directly, or a card link such as `SLUG/#step-5`.

## Driving it with drive.mjs

Preconditions:

- The launch includes the model; `tank-1` by default.
- `verify.sh doctor RUN_ID` lists the manual.

- **Cover.** Open `tank-1/`. Run `node $V/drive.mjs manual-steps --base $U --out .verify/RUN_ID/evidence --slug tank-1`. `#cover` has class `on`, `.pager .next` reads `시작하기 ›`, and `.pager .prev` is disabled (`01-cover`).
- **First step.** Tap `시작하기 ›`. `#step-1` is shown, the address hash is `#step-1`, its figure shows the 3D view or the picture, and `#step-1 .tray li` lists parts (`02-step-1`).
- **Pager and keys.** Tap `다음 ›`, then press the left arrow. Step 2 is shown, then step 1 again.
- **Resume.** Reopen `tank-1/` without a hash. Step 1 is shown again.
- **Contents.** Tap `목차` (`.chapters .toc`). `dialog.contents` opens (`03-contents`). Tap its link to `#done`. `#done` is shown (`04-done`).
- **Last card.** Tap `다음 ›` until the last card (the last mission). The button reads `처음으로`. Tap it and the cover is shown.
- **Proof.** Back on the map, the tank-1 stop has class `built` (`05-map-built`). `result.json` is `"ok": true`.

## Gotchas

- `#done` is not the last card when the model has missions; `처음으로` appears on the last mission.
- An address hash wins over the saved card. Open without a hash to test resume.
- With the 3D view on, the step picture is hidden and may never load; check the figure, not the `img`.
- The screen-wake lock cannot be observed in a headless browser; that sub-feature stays unverified here.
- A page cached by the service worker from an earlier build on the same port can mask a change; use a new `RUN_ID` per build.
