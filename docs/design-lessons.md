# Design lessons

What building models has taught us, so the next model does not relearn it. The `model-design` skill reads this file before a design starts and adds to it when a session ends.

## How this file is kept

- **When.** At the end of every session that created or changed a model, and whenever a real build contradicts the model.
- **What goes where.**
  - A measured number or a part's frame (hole positions, axes, sizes) goes into the `ldraw-spike` skill's tables, not here.
  - A rule about how to design (what to check, what tends to go wrong, a pattern that works) goes here.
  - Something unknown about one model goes into that model's `spec.md` under open questions.
- **Form.** One entry per lesson under the matching heading: the lesson as an instruction, then why, in a sentence or two. Name the model and date it came from. Mark a lesson that only the drawing supports as `unverified`; change it to `built` once a real build confirms it, and delete or rewrite it when a build contradicts it.
- **Size.** Merge entries that say the same thing. When a lesson becomes a check a tool performs, replace it with a pointer to the tool.

## Measuring and tables

- **Check a table entry against the geometry the first time a design depends on it.** The beam row in the `ldraw-spike` skill said thick beams have holes along X; the part files say Y. The rounded beam end is a cylinder along Y, which settles it. (tank-1, 2026-11-22, verified against the library)
- **A box overlap is a question, not an answer.** `ldraw_measure.py overlap` reported each motor against its side frame; `slice` showed the motor body stops 20 LDU short there and only the output boss is that thick. (tank-1, 2026-11-22)

## Motors and hub

- **Keep structure away from a motor's output face.** The large motor's output boss is a disc of radius 29 that stands 20 LDU proud. Pin frames to the holes at z 80 and 120, behind the boss. (tank-1, 2026-11-22, unverified)
- **Leave the hub's top face open.** The buttons and the light matrix are there, and a child has to reach them to start a program. Put a turret or a sensor mast next to the hub, not on it. (tank-1, 2026-11-22)
- **Put every port device in the same submodel as the hub.** The manual's cable card only lists devices placed next to the hub; tank 2's turret motor in its own submodel was left off the card. (tank-2, 2026-11-22)
- **The hub's height sets the hull roof.** On its motors the hub's top is at y -150, so anything that turns above it starts there. Sink a turntable into the hull with its top face level with the hub's top, rather than stacking it on top. (tank-2, 2026-11-22, unverified)
- **Draw motors without their cable when the cable is not the point.** The cabled part has a rigid coil that sticks 160 LDU out of the model. (tank-1, 2026-11-22)

## Tracks

- **Choose the wheelbase from the link pitch, then find holes for it.** A loop is 2 × wheelbase + 10 links around the sprockets, so it closes exactly only when the wheelbase is a multiple of 15 LDU. Holes on the 20 LDU grid give that only at multiples of 60. The tank's 280 LDU needs 28.8 links and gets 29, slightly loose. (tank-1, 2026-11-22, unverified)
- **The tread is wider than the sprocket.** A 96 LDU link on a 36 LDU sprocket reaches 30 LDU past it on each side, so nothing else may stand within that band at track height. (tank-1, 2026-11-22)

- **A track that wraps more wheels needs more links.** Every wheel off the straight line between two sprockets lengthens the loop; tank 4's rhombus needs 35 links a side against tank 1's 29. Count the owned links before choosing the shape. `scripts/gen_tank_rhombus_track.py` wraps any convex set of wheels. (tank-4, 2026-11-22, unverified)
- **Let a sprung road wheel take up the slack.** Choose one link more than the loop needs and let a rubber band press a road wheel into the ground run. (tank-4, 2026-11-22, unverified)

## Moving parts

- **Build each part group that turns as its own sub-assembly, and declare it.** Then `lc validate` turns it through its range and checks the floor (`0 !LC TURN`, `0 !LC GROUND`, ldraw-spike skill); it is also the natural callout for children. (tank-1, 2026-11-22)

- **Look for overlaps at 0° yourself.** The turn check skips pairs that already touch at 0°, as joints. Tank 2's turntable top cut 7 LDU into the hub from the start, and only `ldraw_measure.py overlap` showed it. (tank-2, 2026-11-22)
- **A turntable is both bearing and drive.** Its open centre lets a motor below drive the turret straight through an axle and a 28-tooth gear, with no gear mesh to guess. (tank-2, 2026-11-22, unverified)
- **Expect turn warnings around round parts.** The box of a turntable's disc sweeps corners the disc never reaches; compare the radius with the distance by hand and write the result in `spec.md`. (tank-2, 2026-11-22)

## Kits

- **Count electronics per set before choosing kits.** One 45678 has a single large motor; a two-motor drive needs two sets or the 45681 expansion. (tank-1, 2026-11-22)
- **Look a small part up before using it.** The 2L friction pin in these sets is 61332, not 2780. The plain pin 3673 is only in 45681. (tank-1, 2026-11-22)

## Instructions for children

- **Build mirrored halves in the same step.** Left and right frames, sprockets and tracks go on together, so the child sees the symmetry and the step count stays low. (tank-1, 2026-11-22, unverified)
