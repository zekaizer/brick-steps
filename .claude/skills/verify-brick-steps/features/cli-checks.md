# Model checks and builds

The maintainer checks a model and builds its manual from the terminal. `lc validate` reports errors and warnings and exits 1 on any error. `lc bom` lists the parts. `lc instructions` writes one manual. The measuring script lists box overlaps and pins drawn in one hole.

## Sub-features

- `validate` prints one line per issue and `SLUG: N error(s), M warning(s)`; it exits 0 only with no errors.
- `bom` prints `part,color,qty,title` rows.
- `instructions` writes `index.html`, `img/` and `parts/` into the output folder and prints `…/index.html: N steps, M parts`.
- `pins` prints pin or axle pairs sharing a hole and `N pin or axle pair(s) sharing a hole`.
- `overlap` prints box overlaps to explain and a count line.
- `new` and `revise` create a model folder and record a revision; they write, so they run only on the run's copy.

## How to get to it (user POV)

- `uv run lc validate SLUG`, `uv run lc bom SLUG`, `uv run lc instructions SLUG`.
- `uv run python scripts/ldraw_measure.py pins SLUG` and `… overlap SLUG`.

## Driving it with verify.sh cli

Preconditions:

- `ldraw/` exists (`uv run lc fetch-ldraw`).
- `verify.sh launch RUN_ID` has made `.verify/RUN_ID/root` for commands that write.

- **Validate.** Run `$V/verify.sh cli RUN_ID -- uv run lc validate tank-1`. Exit code 0 and the last line reads `tank-1: 0 error(s), …`.
- **BOM.** Run `$V/verify.sh cli RUN_ID -- uv run lc bom tank-1`. Exit code 0 and the first line is `part,color,qty,title`.
- **Pins.** Run `$V/verify.sh cli RUN_ID -- uv run python scripts/ldraw_measure.py pins tank-1`. The last line reads `0 pin or axle pair(s) sharing a hole`.
- **Instructions.** Run `$V/verify.sh cli RUN_ID -- uv run lc --root .verify/RUN_ID/root --ldraw ldraw instructions tank-1 --no-pdf --out .verify/RUN_ID/manual`. Exit code 0, and `.verify/RUN_ID/manual/index.html` and `img/hero.png` exist.
- **Revise on the copy.** Run `$V/verify.sh cli RUN_ID -- uv run lc --root .verify/RUN_ID/root revise tank-1 -m "verify"`. `.verify/RUN_ID/root/models/tank-1/model.yaml` gains a revision. `git status` shows `models/` unchanged.
- **Proof.** The transcripts in `.verify/RUN_ID/evidence/cli/` with command, stdout, stderr and exit code, plus a listing of any files written.

## Gotchas

- `lc instructions` without `--out` writes into `models/SLUG/out/manual` in the checkout; always pass `--out` inside the run folder.
- `--root` changes where models are read and written; `--ldraw` must still point at the checkout's `ldraw/`.
- A model with an unknown kit quantity warns `quantity-unknown`; that is expected, not a failure.
- `lc validate` exits 1 on errors only. Warnings, such as unchecked block wording or turn interference, still exit 0.
