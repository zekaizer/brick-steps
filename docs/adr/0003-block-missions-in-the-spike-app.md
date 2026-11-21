# 3. Programs for children: SPIKE App word blocks, described as missions in the manual

Date: 2026-11-22

## Status

Accepted

## Context

Each model comes with something for the child to do once it is built. So far that was a Pybricks program in `models/<slug>/program/main.py`. Children build from an iPad mini (ADR 0001), and the programs should also teach them a little programming.

Pybricks Code needs Web Bluetooth. Its documentation says Safari and Chrome for iOS do not provide it, so it cannot be used from an iPad without a third-party browser. Pybricks also replaces the hub firmware, so the same hub cannot run LEGO's own app without reinstalling firmware.

The LEGO Education SPIKE App runs on iPad, connects to the hub over Bluetooth and offers Scratch-style word blocks. Children of this age learn with blocks, not text.

## Decision

- **Platform.** Programs for children are written in the SPIKE App with word blocks, on the stock hub firmware. The repository no longer keeps Pybricks programs; `program/` is removed from models and from `lc new`.
- **Missions instead of program files.** Each model has `missions.yaml`: a list of missions, each with a title, a goal, the blocks to place and a question that invites a change ("숫자를 2로 바꾸면?"). Blocks are written as ids with arguments (`[move_for, forward, 20, cm]`), not as app project files. A child copies the blocks into the app by looking at the picture; that copying is part of the learning.
- **One block table.** The ids, their Korean wording, their category and their argument kinds live in `src/lego_creator/missions.py`. The Korean wording must match the app word for word, so it is checked against the app on the iPad and corrected in that one table.
- **Manual.** The manual shows each mission as a card after the finished model: goal, the blocks drawn in their category colors, and the question. Category colors are design system tokens. The cover shows the model's one-line story (`story.intro` in `model.yaml`).
- **Validation.** `lc validate` checks that every block id is known, that each has the right number and kind of arguments, and that every hub port a mission uses is declared in the model with `0 !LC PORT`.

## Consequences

- A model's missions are part of the model and are revised with it (`lc revise`).
- Ports, wheel size and turning have to be expressed as the app's block arguments. Distances in centimetres depend on the app's wheel setting; missions use rotations or seconds where a wrong wheel size would make the result misleading.
- The repository cannot run a mission. Whether it does what it says is checked on the real build.
- The block wording and colors are only as right as the last check against the app. An app update can change them.
- The LMS-ESP32 board and other Pybricks-only work are out of scope for children's missions.
