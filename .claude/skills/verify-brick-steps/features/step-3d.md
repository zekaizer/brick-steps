# 3D step view

On every step card the rendered picture is replaced by a 3D model of the build so far, which a child can turn with a finger. The step's new parts move into place when the card opens, each from the side it is put on from, and a yellow arrow stays beside each part that did not come from above. `다시 보기` replays the motion and `처음 방향` resets the view. Without WebGL the picture stays.

## Sub-features

- `3d-replace` puts a canvas labelled `돌려 볼 수 있는 3D 조립 그림` in the step figure, which gets class `has-3d`.
- `3d-arrive` moves the step's new parts into place when the card opens: each from the side in its figure's `data-moves` (`from`, `travel` in LDU), wave by wave, each wave 450 ms after the one before and 600 ms long. Parts of a later wave wait, glowing, at their start.
- `3d-arrows` draws a yellow arrow with an ink edge at each `at` in `data-moves`, pointing the way the part went in, over the model. It appears when the last wave lands, at once under reduced motion or when going back, and is cleared and shown again on `다시 보기`. The camera does not move.
- `3d-turn` turns the model on a drag and hides the hint `손가락으로 돌려 보세요`.
- `3d-replay` replays the motion with `다시 보기`. The button is hidden on cards with no new parts.
- `3d-home` returns the camera to the starting view with `처음 방향`.
- `3d-finished` turns the finished model by itself on the `완성!` card until touched.
- `3d-fallback` keeps the rendered picture when WebGL or the model file is missing.

## How to get to it (user POV)

- Open any step card in a manual; the view appears in place of the picture.

## Driving it with drive.mjs

Preconditions:

- The launch includes the model; `tank-1` by default.
- The engine has WebGL. Chromium's software renderer works headless.

- **Open a step.** Open `tank-1/#step-1`. Run `node $V/drive.mjs step-3d --base $U --out .verify/RUN_ID/evidence --slug tank-1`. `#step-1 figure.has-3d .stage3d canvas` appears within 30 s (`01-3d-step-1`).
- **Turn it.** Drag across the canvas. `.stage3d .hint` gets class `gone`, and the canvas pixels differ before and after (`3d-before.png`, `3d-after-drag.png`, `02-3d-dragged`).
- **Reset.** Tap `처음 방향` (`.stage3d .home`). The view returns to the start (`03-3d-home`).
- **Replay.** Not in the journey. Tap `.stage3d .replay` on a step that adds parts, and capture two frames to show the parts moving.
- **Sides and arrows.** Not in the journey. Pick a step whose figure's `data-moves` has entries with `at` (`uv run lc insertions tank-1` names the parts; in tank-1 the motors slide onto the long pins from -X and +X). Capture a frame mid-motion and one after the last wave: the parts move along the pins, not down, and a yellow arrow points at each motor from outside. Go back one card and forward again without motion: the arrows are there at once.
- **Proof.** Look at `3d-after-drag.png`: the model is drawn and turned, not blank. `result.json` is `"ok": true`.

## Gotchas

- Chromium logs `GPU stall due to ReadPixels` warnings while the canvas is captured; they are harmless.
- WebGL in headless WebKit is unproven on this host (WebKit lacks system libraries here), so a 3D proof is Chromium-only until a WebKit run passes.
- Wait for the motion to finish (600 ms, plus 450 ms for each wave after the first; up to about 1.5 s) before comparing frames, or the animation alone changes the pixels.
- Jumping by address shows the card without the slide; the drop still plays.
