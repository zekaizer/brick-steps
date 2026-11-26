# Cable and mission cards

After the step that places the hub's devices, a cable card shows which cable goes into which hub port, with the port letters on the hub. After the finished card, mission cards show SPIKE App word blocks for the child to rebuild in the app, each with a goal and a "try changing" question.

## Sub-features

- `cables` lists each device with its port letter (`.port`, class `port-a` and so on) and shows the cables reaching the hub in the 3D view.
- `missions` shows `움직여 보기 k / n`, the mission title, its goal, its word blocks and its `try` line.
- `blocks` shows each word block with its id in `data-block` and its Korean wording from `missions.py`.

## How to get to it (user POV)

- Page through the manual: the cable card follows the step that places the devices, and the missions follow `완성!`.
- Tap `케이블` or `움직여 보기` in the section bar, or use the `목차` dialog.

## Driving it with drive.mjs

Preconditions:

- The model declares hub ports with `0 !LC PORT` and has a `missions.yaml`; `tank-1` has ports A and B and three missions.

- **Cable card.** Open `tank-1/#cables`. Run `node $V/drive.mjs cables-missions --base $U --out .verify/RUN_ID/evidence --slug tank-1`. `#cables` is shown and its `.port` labels read `A B` (`01-cables`).
- **Mission.** Open `tank-1/#mission-1`. `#mission-1` is shown with blocks `when_program_starts set_movement_motors move_for move_for` (`02-mission-1`).
- **Real path.** The journey opens both cards by address. To prove the child's path, use `manual-steps` (pager and contents) or tap `케이블` in `.chapters`.
- **Proof.** The port letters and block ids in the check lines match `model.mpd` and `missions.yaml`. `result.json` is `"ok": true`.

## Gotchas

- A model without ports has no `#cables` card; the journey then reports `cable card exists` as failed rather than skipping it.
- Block wording that has not been compared with the app is flagged by `lc validate`, not by the site; the site shows whatever `missions.py` says.
