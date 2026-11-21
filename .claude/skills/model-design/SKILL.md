---
name: model-design
description: Workflow for designing a new Brick Steps model or changing an existing one, from idea to a published manual. Use when asked to create, extend or fix a build under models/, to show a draft or preview of a model, or to prepare a model for status ready.
---

# Designing a model

Work in this order. Each step has a tool; do not replace a tool with reasoning about geometry.

Before starting, read `docs/design-lessons.md`. It holds what earlier models taught us.

1. **Scaffold.** A new idea starts a series: `uv run lc new <series> --name "<Korean series name>"` makes `<series>-1`. The next model of a series starts from an existing one: `uv run lc new <series> --from <slug>`. Trim `kits` in `model.yaml` to the kits the build needs, and write `story.intro` (one short Korean sentence, 해요체).
2. **Measure.** Load the `ldraw-spike` skill. For every part that is not in its tables, run `scripts/ldraw_measure.py bbox` and `holes` and work from those numbers. When a measurement would be needed again, add it to the skill's tables in the same change.
3. **Fix the frame of reference first.** Write the axes and the two or three key positions (axle heights, wheelbase) as a comment at the top of the main model. Put every other part on that grid.
4. **Write the `.mpd`.** Place parts so that each pin, axle or bush has a named hole at both ends. Generate repetitive geometry (tread loops, rows of links) with a script in `scripts/gen_<model>_<thing>.py` and paste its output as a `0 FILE` block; record the script in the block's Author line.
5. **Check, in this order.**
   - `uv run lc validate <slug>`: must report 0 errors. Declare each turning sub-assembly with `0 !LC TURN` and the floor contact with `0 !LC GROUND` (ldraw-spike skill) first, and explain every `turn-interference` and `ground-clearance` warning or fix it.
   - `uv run python scripts/ldraw_measure.py overlap <slug>`: explain every line it prints, or move the part. A box overlap with a motor or hub is real unless `slice` shows the body does not reach that far.
   - `uv run lc instructions <slug> --no-pdf`: look at the step pictures in `models/<slug>/out/manual/img/`. A part that floats, pokes through another or faces the wrong way is visible here.
6. **Missions.** Write `missions.yaml` with one to three missions, easiest first: a goal sentence, the blocks, and a `try` question that changes one number. Use only blocks from `src/lego_creator/missions.py`; add a block there (with its wording from the app) before using it. Prefer rotations or seconds over centimetres, since centimetres depend on the app's wheel setting. A mission that needs a value only a real build can tell (how far one rotation turns the robot) asks the child to find it.
7. **Write down what was not checked.** `spec.md` is short: purpose, mechanism, ports, and open questions. Everything that only a real build can confirm goes under open questions: fit of third-party parts, tension, axle depth, cable routing, which way a motor turns.
8. **Steps for children.** One sub-assembly per `0 FILE`, 2 to 6 parts per step, mirrored left and right parts in the same step. Give each sub-assembly a Korean title on the line after `0 FILE`; it is shown in the manual.
9. **Publish only after a real build.** `status: ready` in `model.yaml` puts the model on the public site. Set it only when the maintainer has built it and the open questions are answered.

## Recording what was learned

Finish every design session by updating the repository, in the same branch as the model:

- A new measurement goes into the `ldraw-spike` tables.
- A rule about designing goes into `docs/design-lessons.md`, in the form that file describes.
- An unknown about this model goes into its `spec.md`.
- A check that was done by hand twice becomes a command in `scripts/ldraw_measure.py`.
- A change to a model that already had a revision recorded gets `uv run lc revise <slug> -m "..."`. Changes made before the first draft is shown to the maintainer do not.

When the maintainer reports how a real build went, update the lessons first: mark confirmed ones `built`, and rewrite the ones the build contradicted.

## What the tools cannot tell

`lc validate` and the overlap check know nothing about friction, gravity or flex, and the turn and floor checks only compare boxes. Say so when presenting a draft: it is a picture of the intent until someone builds it.
