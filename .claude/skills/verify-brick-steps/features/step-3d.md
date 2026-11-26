# 3D step view

On every step card the rendered picture is replaced by a 3D model of the build so far, which a child can turn with a finger. The step's new parts drop into place when the card opens. `다시 보기` replays the drop and `처음 방향` resets the view. Without WebGL the picture stays.

## Sub-features

- `3d-replace` puts a canvas labelled `돌려 볼 수 있는 3D 조립 그림` in the step figure, which gets class `has-3d`.
- `3d-drop` animates the step's new parts into place (600 ms) when the card opens.
- `3d-turn` turns the model on a drag and hides the hint `손가락으로 돌려 보세요`.
- `3d-replay` replays the drop with `다시 보기`. The button is hidden on cards with no new parts.
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
- **Proof.** Look at `3d-after-drag.png`: the model is drawn and turned, not blank. `result.json` is `"ok": true`.

## Gotchas

- Chromium logs `GPU stall due to ReadPixels` warnings while the canvas is captured; they are harmless.
- WebGL in headless WebKit is unproven on this host (WebKit lacks system libraries here), so a 3D proof is Chromium-only until a WebKit run passes.
- Wait for the drop to finish (about a second) before comparing frames, or the animation alone changes the pixels.
- Jumping by address shows the card without the slide; the drop still plays.
