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

- **A motor's output is across its body, so decide early where the body goes.** To turn an axle that lies along the fuselage, stand the motor on end, or lay it flat and turn the drive with a pair of bevel gears. Plane 1 lays both flat: the gun motor output down, the fan motor output up, which keeps them below the cockpit and the engine pods. (plane-1, 2026-11-26, unverified)
- **Plan around the hub's buttons.** The centre button is at the hub's front end and the Bluetooth button at its rear right corner (positions in the `ldraw-spike` tables). Plane 1's canopy stops in front of the hub, and its fan intakes sit behind the hub's rear edge, not above the Bluetooth button. (plane-1, 2026-11-26)
- **Estimate the balance before placing the wheels.** Add up rough weights (hub 155 g, large motor 55 g, medium motor 38 g, beams about 0.23 g a hole) along the length. Plane 1's main wheels were first 35 LDU behind the estimated centre of gravity and were moved to 55. (plane-1, 2026-11-26, unverified)
- **Leave room behind a motor for its cable.** The cable leaves the rear end straight back. Plane 1's gun motor had 20 LDU to the hub until it was raised above the hub's top. (plane-1, 2026-11-26, unverified)

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

## Pins and holes

- **Run `ldraw_measure.py pins` after every change.** Two pins drawn in one hole look fine in a picture, and `overlap` skips connectors. Plane 1 had 16 such pairs before the check existed. (plane-1, 2026-11-26)
- **Hold every gear from both sides.** A bush, a half bush, a beam face, an axle connector, an axle with a stop, or pins through the gear's own holes into the part beside it. On a vertical axle the stop goes under the gear, or it slides off. A gear or pulley on the end of an axle has nothing in front: give the axle one more stud and a bush, as plane 1's gun and fan intakes now have. `ldraw_measure.py axles` reports a gear with no stop as `gear-free` and a gap to the stop as `gear-play`. (plane-1, 2026-11-27, unverified)
- **Check the holes a turned copy lands on.** A sub-assembly turned 180° for the other side puts its pins at mirrored positions; tank 2's left fender met the hull's own pin in one frame hole. (tank-2, 2026-11-27)
- **Make sure an axle reaches into each bearing, not just to its face.** Plane 1's gun axle was 10 LDU short of entering its rear T-beam; two axles joined by an axle connector reach it. `ldraw_measure.py axles` reports an axle that only meets a face as `touches-only`. (plane-1, 2026-11-27)
- **Join a stack of beams with one long pin through all of them, or with pins at different holes for each joint.** Two short pins at the same hole meet inside the middle beam. The same holds for three rails side by side: one 3L pin through all three. (plane-1, 2026-11-26)

## Frames and long bodies

- **Join frames end to end with posts into the hub, not with pins alone.** Pins through two abutting frame walls all sit at one height and act as a hinge. A post pinned to the hub's end face 60 LDU higher gives the joint a lever arm. (plane-1, 2026-11-26, unverified)
- **Find the hole grid two parts share before choosing where a motor sits.** The 11 x 7 frame's side holes are 40 apart and a motor's are 40 and 120 apart, so only one position along the frame lines up. (plane-1, 2026-11-26)
- **A beam that crosses another shares one hole with it.** Give a wing or a strut a second pin somewhere, with a T-beam, a bent beam or a rib, or it swings. (plane-1, 2026-11-26, unverified)
- **A frame's box includes its open centre.** `overlap` lists everything standing inside the opening; that is expected. (plane-1, 2026-11-26)

## Looks

- **Skin the frame before showing a draft.** Plane 1's first drawing was 131 parts of frames and stilts and read as a skeleton. (plane-1, 2026-11-26)
- **Give a wing a round leading edge, a taper and a different tip.** A flat perforated frame, and a deck of equal beams, both read as a board. Plane 1's wings became wings with an 11 x 3 curved panel laid lengthwise as the leading edge, a trailing edge stepping forward towards the tip and azure tips on a black wing. (plane-1, 2026-11-26)
- **Choose beam lengths by colour.** Each beam length comes in one colour in these kits (11L magenta, 7L and 13L azure, 9L and 15L black). Pick the lengths that give the colours you want, then place the ribs that hold them; plane 1's first wing had magenta stripes wherever an 11L was needed. (plane-1, 2026-11-26)
- **Fill an open frame with a part that fits its opening.** A 5 x 3 H-beam fills the 5 x 7 frame's opening and turns it into a solid fin. (plane-1, 2026-11-26, unverified)
- **Use a real photo as the checklist.** Comparing renders from several angles with photos of the real aircraft showed what was missing: canopy, intakes, fins at the tailplane tips, stores, an offset nose wheel. (plane-1, 2026-11-26)
- **Hang panels on holes a motor already has.** The curved 11 x 3 panel's two rails are one beam apart sideways and 40 apart in height, the same as a motor's side holes, so it fits a motor's flank with no adapter. (plane-1, 2026-11-26, unverified)
- **Carry a wide wing through the body.** A 19 x 11 frame under the fuselage, pinned through the middle frame into the hub, takes both wings' root rows and spreads the bending over many pins. (plane-1, 2026-11-26, unverified)

## Kits

- **Count electronics per set before choosing kits.** One 45678 has a single large motor; a two-motor drive needs two sets or the 45681 expansion. (tank-1, 2026-11-22)
- **Look a small part up before using it.** The 2L friction pin in these sets is 61332, not 2780. The plain pin 3673 is only in 45681. (tank-1, 2026-11-22)

## Instructions for children

- **Give a large repeated surface its own sub-assembly and at most ten parts a step.** Plane 1's wing deck was one step of 39 parts; as a sub-assembly per side, a row or two per step, it is 12 readable steps. (plane-1, 2026-11-26)
- **Build mirrored halves in the same step.** Left and right frames, sprockets and tracks go on together, so the child sees the symmetry and the step count stays low. (tank-1, 2026-11-22, unverified)
