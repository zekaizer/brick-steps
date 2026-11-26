---
name: verify-model
description: Check a Brick Steps model (models/<slug>/model.mpd, or any .mpd file) the way a builder would meet it, and keep the reports and pictures as evidence. Runs lc validate and the geometry checks in scripts/ldraw_measure.py (shared pin holes, overlaps, loose axles and gears, build order and insertion, balance, step sizes), then renders fixed views and close-ups with LeoCAD. Use before showing a model draft, after every model change, before setting status ready, and when asked whether a model can really be put together.
---

# Verify a model

This skill answers two questions about an `.mpd` before anyone builds it:
- **Is it put together right?** No two pins share a hole, no axle stops short of its hole, no gear can slide off.
- **Can it be built in the order of the steps?** No part floats, every pin can still be pushed in, and every beam can still slide onto its pins.

Every check reads real part geometry from `ldraw/` and `custom/`, but none knows friction, flex, gravity on a part that is being held, or where fingers fit. A finding is a place to look at, and a clean report is not proof that the model works. What only a real build can tell goes into the model's `spec.md` under "Open questions".

All commands run from the repository root. Below, `M=.claude/skills/verify-model/scripts`. They need `ldraw/` (`uv run lc fetch-ldraw`); the pictures also need LeoCAD and Xvfb (ADR 0001).

## Run

```bash
M=.claude/skills/verify-model/scripts
$M/check.sh plane-1                       # a model by slug
$M/check.sh path/to/variant.mpd           # any .mpd file; lc validate is skipped, it needs a slug
uv run python $M/views.py plane-1 --out .verify/model-plane-1/views
```

`check.sh` runs `lc validate` and `lc insertions`, then `ldraw_measure.py` `pins`, `overlap`, `axles`, `assembly`, `balance` and `steps`. It prints one summary line per check:

```
validate  plane-1: 0 error(s), 3 warning(s)
insertions 436 reference(s): 232 from above, 204 with an arrow, 1 blocked, 0 set by 0 !LC INSERT
pins      0 pin or axle pair(s) sharing a hole
overlap   75 candidate overlap(s) deeper than 2 LDU among 148 parts
axles     3 axle finding(s)
assembly  0 assembly finding(s)
balance   centre of gravity is inside the contacts, 65 LDU from the nearest edge
steps     87 steps, 0 above 10 parts
evidence: .../.verify/model-plane-1
```

- **Exit code:** 1 when `lc validate` reports an error, otherwise 0. A model change is done only at 0 errors (CLAUDE.md); the other checks never fail the run, and you read their reports.
- **Time:** plane-1 (456 parts) takes about 9 s.
- **Six views:** `views.py` renders `front-left.png`, `front.png`, `side.png`, `top.png`, `rear.png` and `below.png` in about 20 s for plane-1. In `side.png` the model's front (-Z) points right; in `top.png` it points down.

## Look at a finding

Each finding names parts by label: `fender.ldr#70/61332#2` is part 61332, line 2 of submodel `fender.ldr`, which is placed on line 70 of the main model. Turn a label into a picture:

```bash
uv run python scripts/ldraw_measure.py where plane-1 gun.ldr#67/4185a#0
# gun.ldr#67/4185a#0  at 0 50 -385  box X-30..30 Y20..80 Z-390..-380
uv run python $M/views.py plane-1 --out .verify/model-plane-1/views --at 0 50 -385 --from -200 -120 -260 --name gun-wheel
```

- `--at` is the point to look at. `--from` is the camera's offset from it in LDU; the default (-350 -250 -450) looks from front-left above, and a smaller offset gets closer.
- `uv run python $M/views.py PART --part --out DIR` renders one part on its own, to see its shape before placing it.
- `uv run python scripts/ldraw_measure.py line SLUG X Y Z AXIS` lists every hole and pin on a line, to see what a pin or axle passes through.

## What each check finds

| check | finding | what it means | what to do |
|---|---|---|---|
| validate | `error` lines | syntax, matrix, colour, part, kit, port, catalog or mission problem | fix; the model is not done until 0 errors |
| validate | `turn-interference`, `ground-clearance` | a turning submodel hits a part, or a part is within a plate of the floor (boxes) | look at a close-up; fix or explain in `spec.md` |
| insertions | `BLOCKED by PART` | the 3D step view finds no clear way in for this part: earlier parts are in its path along its pins, or on every side | reorder the step so the part goes in before what closes it in, or set the side with `0 !LC INSERT FROM <side>` (ldraw-spike skill) |
| insertions | a side that is not how the part really goes in | the guess is wrong (rays and hole walls, no fingers) | add `0 !LC INSERT FROM <side>` above the reference; `lc validate` checks it |
| pins | `A x B along X at (…)` | two pins or axles drawn in the same hole | always real: use one long pin (6558) or move one to another hole |
| overlap | `A x B overlap X… Y… Z…` | two part boxes intersect | candidates only: curved panels, frames and parts nested in a frame overlap on purpose. Run `slice` on the larger part or take a close-up for each new one |
| axles | `touches-only` | an axle end meets a part's face and does not go into its hole | real: lengthen the axle or move the part |
| axles | `gear-free GEAR -Z AXLE` | nothing on the axle stops the gear or wheel on that side, so it can come off the axle's end | real: add a bush or half bush, or a beam beside it |
| axles | `gear-play GEAR -Z AXLE 8 LDU to PART` | the gear can slide that far before PART stops it | fill the gap with bushes when the gear meshes with another; a sprocket or track wheel with a few LDU of play (the track keeps it in line) goes in `spec.md` |
| assembly | `floating` | a part touches nothing placed in an earlier or the same step | move it to a later step, or add what holds it first |
| assembly | `pin-blocked` | earlier parts cover both ends of a pin, so it cannot be pushed in | put the pin in an earlier step, before the parts that close it in |
| assembly | `no-slide` | a part goes onto earlier pins but earlier parts block both ways along them | reorder: fit this part before what blocks it, or put the pins in with it |
| balance | `OUTSIDE` or a small margin | the centre of gravity is outside or near the edge of the floor contacts | move weight (the hub, motors) or widen the stance; the masses are a rough table |
| steps | `step N: K parts` | a step above 10 parts | split it; children's steps hold 2 to 6 parts (model-design skill) |

`axles` counts a gear pinned to a neighbour through its own pin holes as held, and a rubber band as no stop.

`assembly` follows the instruction steps and checks only straight pushes along the axes: a pin is pushed in along its own axis, and a part slides onto pins of strictly earlier steps. It cannot tell whether fingers reach, whether a part can be tilted in, or whether a beam flexes enough to snap over a pin.

## Compare with the last version

A model that already has many overlap candidates is reviewed by what changed. Labels carry line numbers, which shift when parts are added, so compare them without numbers:

```bash
mkdir -p .verify/model-proof
git show main:models/plane-1/model.mpd > .verify/model-proof/plane-1-main.mpd
$M/check.sh .verify/model-proof/plane-1-main.mpd
f() { grep '  x  ' "$1" | sed 's/#[0-9]*//g' | sort; }
diff <(f .verify/model-plane-1-main/overlap.txt) <(f .verify/model-plane-1/overlap.txt)   # only new or gone pairs
```

The same `f` works on `pins.txt`.

## Then the step pictures

The checks and views look at the finished model. Wrong-looking steps (a part floating mid-air because its support comes later, a view that hides the new parts) show only in the manual:

```bash
uv run lc instructions plane-1 --no-pdf     # pictures in models/plane-1/out/manual/img/, about 1 s per 2 steps
```

Open the pictures of the steps an `assembly` finding names, and of every sub-assembly's first and last step. To see the manual in the site itself (3D view, cable card, missions), use the `verify-brick-steps` skill.

## Evidence

- `check.sh` writes `.verify/model-NAME/<check>.txt`. Each file holds the command, its full output and `--- exit N`. NAME is the slug, or the file name without `.mpd`.
- Pictures go where `--out` says. Keep them next to the reports, in `.verify/model-NAME/views/`.
- `.verify/` is ignored by git. To show a result to the maintainer, send the pictures and quote the summary lines.

A proof that a model is ready shows these four things:
- `validate` at 0 errors, with every warning explained.
- `pins` at 0.
- Every `axles` and `assembly` finding either fixed or written in `spec.md` as an open question.
- The six views looked at for the model's signature features.

## Cleanup

Nothing keeps running: LeoCAD and Xvfb exit after each picture. Delete only what you created, by exact name: a variant file you wrote into `.verify/model-proof/`, or a `.verify/model-NAME/` folder that is no longer needed. `models/<slug>/out/` is generated and ignored.

## Proven

On 2026-11-27:
- `check.sh plane-1` ran in 9 s; `views.py` rendered six views in 20 s.
- The tank-2 before its pin fix (`git show 09dfdcd:models/tank-2/model.mpd`) reports `6 pin or axle pair(s) sharing a hole`, and today's tank-2 reports 0.
- The `gear-free` finding on plane-1's gun is visible in a close-up: the wheel 4185a ends flush with its axle's end.
