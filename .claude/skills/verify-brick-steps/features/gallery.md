# Gallery map and lab

The gallery is an adventure map with a road per model series and a stop per ready model. Tapping a stop opens a sheet with the model's picture, story and size, and its button opens the manual. Five quick taps on the logo open the hidden lab of draft models.

## Sub-features

- `map-stops` shows one stop per ready model, labelled with its name, plus a locked `곧 나와요` stop.
- `map-sheet` opens a sheet with the name, story, `부품 N개 · M단계` and an optional `… 에서 나왔어요` line.
- `map-start` opens the manual from the sheet's `만들기 시작 ›` (`다시 만들기 ›` once built).
- `map-built` marks a finished model `✓ 다 만들었어요` and moves `다음은 여기!` to the next stop.
- `map-clear` removes the built mark after two taps on `‘다 만들었어요’ 표시 지우기`.
- `lab` opens `/lab/` with heading `실험실`, the drafts and a `‹ 갤러리로` link.

## How to get to it (user POV)

- Open the site root.
- Tap a stop on the map, then the sheet's button.
- Tap the Brick Steps logo five times within two seconds for the lab.

## Driving it with drive.mjs

Preconditions:

- The launch includes at least one `status: ready` model; `tank-1` by default.
- `verify.sh doctor RUN_ID` exits 0.

- **Map.** Open the root. Run `node $V/drive.mjs gallery --base $U --out .verify/RUN_ID/evidence --slug tank-1`. A stop `a.stop[href="tank-1/"]` with `data-name="탱크 1호"` is visible (`01-map`).
- **Sheet.** Tap the stop. The journey clicks it. `.sheet.on` shows `.name` equal to the stop's name and `.meta` matching `부품 N개 · M단계` (`02-sheet`).
- **Start.** Tap `만들기 시작 ›` (`.sheet .go`). The address becomes `tank-1/`, and the cover `#cover h1` shows the same name (`03-manual-cover`).
- **Lab.** Back on the root, tap `.site-head .brand` five times. The address becomes `/lab/` and the heading reads `실험실` (`04-lab`).
- **Built mark and clear.** Run the `manual-steps` journey: its last capture `map-built` shows the stop with class `built`. The two-tap clear has no journey yet. In a Playwright script, tap the built stop, tap `.sheet .clear` twice, and check that the stop loses `built`.
- **Proof.** `result.json` is `"ok": true`, and the screenshots show the map, the sheet over it, the manual cover and the lab heading.

## Gotchas

- A draft has no stop on the map; it appears only in the lab. With no draft in the launch, the lab shows its empty message, which still proves the entry.
- The sheet slides up over two animation frames; wait for `.sheet.on` before reading it.
- The five logo taps must fall within two seconds.
- Built marks live in the browser's `localStorage`, so they show only in the profile that finished the manual.
