---
name: verify-brick-steps
description: Drive the real Brick Steps app and capture proof. Covers the kid-facing manual site (gallery map, step-by-step manuals, the 3D step view, cable and mission cards) in a headless browser on an iPad Mini screen, and the `lc` CLI that checks models and builds the site. Use after changing `site_assets/` (manual.js, viewer3d.js, components.css), `site.py`, `export.py`, `pack3d.py`, `missions.py` or a model, and whenever a change must be shown working in the app rather than only in pytest.
---

# Verify Brick Steps

Brick Steps has two surfaces:
- **The manual site** is the primary one: children use it on an iPad. `lc site` renders it with LeoCAD into static HTML.
- **The `lc` CLI** is the maintainer's surface.

This skill builds a site from a copy of the models you name and serves it on a free local port. It drives the site with Playwright and keeps screenshots, accessibility snapshots, console logs and CLI transcripts as evidence.

All commands run from the repository root. `V=.claude/skills/verify-brick-steps/scripts` below. Pick a `RUN_ID` (letters, digits, `. _ -`), for example `fix-pager-1`. Every run lives in `.verify/RUN_ID/`, which git ignores.

## Launch

```bash
V=.claude/skills/verify-brick-steps/scripts
$V/verify.sh launch RUN_ID tank-1          # one or more model slugs; default tank-1
```

What it does:
- Copies `design/`, `custom/` and the named models (`model.yaml`, `model.mpd`, `missions.yaml`) into `.verify/RUN_ID/root/`.
- Runs `uv run lc --root .verify/RUN_ID/root --ldraw ldraw site --out .verify/RUN_ID/site --no-pdf`.
- Serves that folder with `python3 -m http.server` on `127.0.0.1` and a free port.

It is ready when it prints `ready: http://127.0.0.1:PORT/`. The build log is `evidence/build.log`.
- **Build time:** LeoCAD renders every step, so a model costs about a second per two steps. `tank-1` (15 steps plus sub-assemblies) builds and serves in about 10 s, `plane-1` (84 steps) takes minutes.
- **Which models appear where:** a model with `status: ready` appears on the gallery map; a draft appears only in the lab (`/lab/`). Launch with at least one ready model for gallery journeys, and add a draft (such as `tank-4`) when the lab must list something.
- **Prerequisites:** `ldraw/` (`uv run lc fetch-ldraw`), LeoCAD 25.09 and Xvfb (ADR 0001), and Node with a global `playwright` whose browsers are installed (`playwright install chromium`).

Launch refuses to start a second server for a `RUN_ID` that is still serving. Use a new `RUN_ID` to run side by side; runs never share ports, folders or browser profiles.

## Doctor

```bash
$V/verify.sh doctor RUN_ID
```

Read-only. It checks:
- the site build exists;
- the pid it recorded is alive and is this run's own `http.server` on this run's port and folder;
- the page serves `Brick Steps v<pyproject version>`;
- every launched model has a manual, in the gallery or in the lab;
- Playwright loads, and Chromium and WebKit can be started.

Run it first whenever anything looks off. Exit code 0 means worth driving. A `warn` line for WebKit is not a failure (see Gotchas in the feature map).

## Drive

```bash
U=http://127.0.0.1:$(cat .verify/RUN_ID/port)/
node $V/drive.mjs JOURNEY --base $U --out .verify/RUN_ID/evidence --slug tank-1 [--engine chromium|webkit]
node $V/drive.mjs shot --url ${U}tank-1/#step-3 --out .verify/RUN_ID/evidence     # any page, one capture
```

`JOURNEY` is one of `gallery`, `manual-steps`, `step-3d`, `cables-missions`. Each is a mapped feature (see `features/`). It prints one `ok`/`FAIL` line per check and exits 0 only when all checks pass and no page threw.
- **Browser:** every journey starts with an empty browser profile (no saved progress) on Playwright's `iPad Mini` device with `ko-KR`.
- **Engine:** the default is Chromium. WebKit matches the iPad but needs system libraries on Linux.
- **Handles:** the stable handles are listed in each feature file. They are ids (`#cover`, `#step-N`, `#cables`, `#done`, `#mission-N`), classes (`.pager .next`, `.sheet .go`, `.stage3d canvas`, `.chapters .toc`) and data attributes (`a.stop[data-name]`, `[data-block]`). The current card is the one with class `on`.

For a behaviour no journey covers, write a short Playwright script next to the evidence, using the same device and the same handles. Or add a journey to `drive.mjs` and a line to the matching feature file.

CLI behaviour is driven through the recorder, which writes the command, stdout, stderr and exit code to `evidence/cli/NN.txt`:

```bash
$V/verify.sh cli RUN_ID -- uv run lc validate tank-1
$V/verify.sh cli RUN_ID -- uv run lc --root .verify/RUN_ID/root --ldraw ldraw instructions tank-1 --no-pdf --out .verify/RUN_ID/manual
```

Commands that write (`lc new`, `lc revise`, `lc instructions`) must point at the run's copy: use `--root .verify/RUN_ID/root` with `--ldraw ldraw`, or `--out` inside `.verify/RUN_ID/`. They must never touch `models/` in the checkout.

## Evidence

Evidence goes to `.verify/RUN_ID/evidence/`:
- `build.log`;
- `<journey>-<engine>/` with numbered `NN-label.png` and `NN-label.aria.txt` pairs (the snapshot's first line is the URL), `console.log` and `result.json`;
- `cli/NN.txt` transcripts.

Proof standards:
- Drive the real user path: taps on the map, the pager buttons, the contents dialog, a drag on the canvas. Jumping straight to `#step-N` proves only that the card renders, not that a child can get there.
- Capture the action and the state it leads to. A screenshot of the end screen alone is not proof.
- Check the side effects too: saved progress (reopening the manual resumes where it stopped), the "다 만들었어요" mark on the map, files written by a CLI command and its exit code.
- The site has no test mode and no mocks. The service worker and `localStorage` are real; a fresh browser profile per journey is the isolation.
- Report a journey as failed with the failing check and the evidence folder. Never weaken a check to make it pass: if a precondition is missing (for example no draft for the lab), say so.

## Cleanup

```bash
$V/verify.sh stop RUN_ID
```

It kills only the pid it recorded, and only after confirming that it is this run's own `http.server` (never by process name). Then it deletes `.verify/RUN_ID/root`, `site/`, the port and pid files. `evidence/` stays, and the command prints its path. Run it after every attempt, including failed ones. Delete an evidence folder only when its proof is no longer needed.

## Helpers

Both helpers are executable and print their usage when called without arguments.
- `scripts/verify.sh`: `launch RUN_ID [SLUG...]`, `doctor RUN_ID`, `stop RUN_ID`, `cli RUN_ID -- COMMAND...`. Set `VERIFY_HOME` to keep runs somewhere other than `.verify/`.
- `scripts/drive.mjs`: `JOURNEY --base URL --out DIR [--slug SLUG] [--engine chromium|webkit]`, or `shot --url URL --out DIR`. It loads the global `playwright` package (`npm root -g`).

## Feature map

`features/README.md` indexes the user-facing features with their entry points, the commands that drive them and the end state that proves them. Read the matching feature file before driving. Keep it current with `/pstack:maintain-verification-skill` when the site changes.
