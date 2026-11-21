---
name: ldraw-spike
description: LDraw geometry and SPIKE Prime part reference for this repo. Use whenever writing, editing or reviewing a models/*/model.mpd (type 1 placement lines, rotation matrices, submodels, STEP), choosing part ids for a 45678/45681 build, placing Technic beams, pins, axles or gears, declaring hub ports with `0 !LC PORT`, or adding rows to inventory/id-map.csv.
---

# LDraw for SPIKE Prime builds

Every number below was measured from the official library in `ldraw/` (fetched 2026-11-21) or computed and checked by script. Anything not listed here is unknown: measure it from `ldraw/parts` before using it, never guess.

## Ground rules

- `models/<slug>/model.mpd` is the source of truth. After every edit run `uv run lc validate <slug>`; the model is not done until it reports 0 errors.
- Never reference an alias file (title `~Moved to ...`). The validator rejects it and names the target.
- Electronics use the cabled shortcuts so the BOM matches the kit: `45601c01` (hub, includes battery), `54675c01`, `54696p01c01`, `37308c01`, `37316c01`, `37312c01`. Details in [references/spike-parts.md](references/spike-parts.md).
- Parts must be in the kits listed in `model.yaml`. `uv run lc bom <slug>` shows what the model uses.
- A new row in `inventory/id-map.csv` needs the LDraw title (`head -1 ldraw/parts/<id>.dat`) and the Rebrickable name (`inventory/<kit>.csv`) to describe the same part. Mark anything inferred from names alone in the `note` column.

## Units and axes

- 1 LDU = 0.4 mm. Stud pitch and Technic hole pitch are 20, brick height is 24, plate height is 8.
- **-Y is up.** Stacking a brick on top of another subtracts 24 from y.
- Type 1 line: `1 <color> x y z a b c d e f g h i <file>`. A local point (u,v,w) lands at `x + a·u + b·v + c·w`, `y + d·u + e·v + f·w`, `z + g·u + h·v + i·w`. Read each column of the matrix as "where this local axis points".
- Color `16` inherits the parent's color. Use it for submodel contents and electronics.

## Rotation table

Copy matrices from this table instead of composing them by hand. Every entry has determinant 1. `lc validate` rejects any other kind of matrix with `bad-matrix`, whether it is mirrored (det -1), scaled or sheared, or singular.

| name | a b c d e f g h i | local X → | local Y → | local Z → |
|---|---|---|---|---|
| identity | `1 0 0 0 1 0 0 0 1` | +X | +Y (down) | +Z |
| Ry+90 | `0 0 1 0 1 0 -1 0 0` | -Z | +Y (down) | +X |
| Ry-90 | `0 0 -1 0 1 0 1 0 0` | +Z | +Y (down) | -X |
| Ry180 | `-1 0 0 0 1 0 0 0 -1` | -X | +Y (down) | -Z |
| Rx+90 | `1 0 0 0 0 -1 0 1 0` | +X | +Z | -Y (up) |
| Rx-90 | `1 0 0 0 0 1 0 -1 0` | +X | -Z | +Y (down) |
| Rx180 | `1 0 0 0 -1 0 0 0 -1` | +X | -Y (up) | -Z |
| Rz+90 | `0 -1 0 1 0 0 0 0 1` | +Y (down) | -X | +Z |
| Rz-90 | `0 1 0 -1 0 0 0 0 1` | -Y (up) | +X | +Z |

## Part frames (measured bounding boxes)

| part | origin and axes |
|---|---|
| brick 3001 (2x4) | top center. Body spans y 0..24 and studs reach y -4. Long side on X |
| plate 3020 (2x4) | top center. Body spans y 0..8 |
| Technic beam 1xN thick (32523, 32316, 41239, 32278) | center. Length along **Z**, hole axis along **X**, 18 thick (X) by 20 tall (Y). Hole i (0-based) sits at z = (i − (N−1)/2)·20 |
| axle N (3705 = 4L) | center. Along **X**, length N·20 |
| pin 61332 / axle pin 3749 / long pin 6558 | center. Along **X**, length 40 / 40 / 60 |
| gears 32270, 18575, 46372, 32498 | center. Axis along **Z**, so a gear on an X axle needs Ry+90 or Ry-90 |
| wheels 39367p01, 56903 | center. Axis along **Z** |
| hub 45601c01 | bottom center. Body spans y -80..0, 140 on X (7 studs), 220 on Z (11 studs) |
| 19x11 frame 39369 | center. Spans 220 on X, 380 on Z, 20 thick (Y) |

With identity rotation, a pin or axle along X goes straight through a beam hole. A beam on identity therefore takes pins at the same (y, z) as a hole center, with x set to wherever the pin should stick out.

Motors and sensors have offset origins and attachment holes that this table does not cover. Measure their hole centers from the subfiles before placing one.

## Gears (module 1 mm)

Two parallel gears mesh when their axle centers are 1.25·(T1+T2) LDU apart:

| pair | distance (LDU) | studs |
|---|---|---|
| 12+12 | 30 | 1.5 |
| 12+20 | 40 | 2 |
| 12+28 | 50 | 2.5 |
| 12+36 | 60 | 3 |
| 20+20 | 50 | 2.5 |
| 20+28 | 60 | 3 |
| 20+36 | 70 | 3.5 |
| 28+28 | 70 | 3.5 |
| 28+36 | 80 | 4 |
| 36+36 | 90 | 4.5 |

Half-stud distances cannot sit on a straight beam. They need diagonal placement or offset beams. Perpendicular (bevel) meshing is not tabulated: measure it.

## Hub ports

Declare ports in the `.mpd` with one line per device, written in the submodel that contains the device:

```
0 !LC PORT A 54675c01 drive_left
```

Rules: ports go from A to F, each port is used once, the part must be a hub device, and the model must contain at least as many of that device as it has assignments. A device without a port is reported as a warning. The `role` (snake_case) becomes the Pybricks variable name later.

## Instruction structure

- The first `0 FILE` is the main model. Make each subassembly (drivebase, arm, sensor mount) its own `0 FILE` so that it becomes an instruction callout.
- End each build step with `0 STEP`. Aim for 2–6 parts per step, and always start a new step when the view would need to rotate.
- `lc validate` also catches malformed lines (`malformed-line`) and color codes that are not in LDConfig (`unknown-color`). It does not check physical connectivity, collisions or grid alignment. When placement is uncertain, say so in `spec.md` under "Open questions".
