# Brick Steps verification map

This directory is the maintained source for verifying what children and the maintainer can do with Brick Steps. Read this index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch with `.claude/skills/verify-brick-steps/scripts/verify.sh launch RUN_ID tank-1`. `tank-1` is `status: ready`, so it has a stop on the map. It has 15 build steps, a cable card for ports A and B, and three missions.
- Add a draft model (for example `tank-4`) to the launch when the lab must list a manual.
- `verify.sh doctor RUN_ID` exits 0 before any journey.
- `U=http://127.0.0.1:$(cat .verify/RUN_ID/port)/` is the base URL.
- Never drive a server this run did not start: not `site/` in the checkout, not a server the user runs, not the published site.

## Driving conventions

- Run browser journeys with `node .claude/skills/verify-brick-steps/scripts/drive.mjs JOURNEY --base $U --out .verify/RUN_ID/evidence --slug SLUG`.
- Every journey starts with a fresh browser profile, so saved progress and "built" marks start empty.
- The manual shows one card at a time; the visible card has class `on` and its id is the address hash.
- Prefer the handles named in the feature files (ids, `.pager` buttons, `a.stop[data-name]`, `[data-block]`) over screen positions.
- Run CLI checks through `verify.sh cli RUN_ID -- COMMAND`. Commands that write go to `.verify/RUN_ID/`, never to `models/`.

## Proof and skip reporting

- Capture the action and the resulting state: each journey writes numbered screenshot and accessibility-snapshot pairs, `console.log` and `result.json`.
- Prove persistence from a second view: reopen the manual to see it resume, or go back to the map to see the built mark.
- CLI proof is the transcript with the command, stdout, stderr and exit code.
- Record the engine with every browser proof. Chromium proof does not stand for WebKit (iPad Safari).
- Report an unreachable path with the command tried and the missing precondition. Do not report a path as verified through a different entry point.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph on the user-visible behaviour, then exactly these H2 sections in order: `Sub-features`, `How to get to it (user POV)`, `Driving it with drive.mjs` (or `with verify.sh cli` for the CLI) starting with `Preconditions:`, and `Gotchas`. Keep implementation details out; name user paths, stable handles, required state, commands and observable proof.

## Features

- [Gallery map and lab](./gallery.md): the adventure map, the model sheet, starting a manual, the built mark and the hidden lab.
- [Following a manual](./manual-steps.md): cover, pager, keyboard, saved progress, section bar, contents and the finished card.
- [3D step view](./step-3d.md): the turnable model that replaces each step picture, its hint and its two buttons.
- [Cable and mission cards](./cables-missions.md): which cable goes to which hub port, and the SPIKE App word-block missions.
- [Model checks and builds](./cli-checks.md): `lc validate`, `lc bom`, `lc instructions` and the measuring checks the maintainer runs.
