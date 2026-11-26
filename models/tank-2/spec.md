# 탱크 2호

## Purpose

Tank 1 with a real turret: a low, wide turret on a turntable that a motor turns a full circle, so children can aim it from a program. The look follows medium tanks such as the Panzer IV: hub as the front hull, turret ring flush with the hull roof, a long single gun.

## Mechanism

- The lower hull is tank 1's: two large motors side by side drive the front sprockets, and two upright 11 x 7 frames carry the rear idlers and the tracks.
- The hub sits at the front on two 7L beams across the large motors' top holes, turned so that USB faces forward. Its top face (y -150) is the hull roof and stays open.
- Fenders (`fender.ldr`): a 9L rail on each frame's outer holes at y -80 carries a 3 x 11 panel over the track. Two long pins run through frame, rail and panel; the left fender is the right one turned, so it leaves the frame hole that the hull's own pin uses on that side.
- Turret drive: the medium motor (port C, in the main model so that the cable card lists it) stands with its output up at (0, -110, 240), tied to the frames by two beams per side at y -80. The large turntable (`18938`/`18939`, centre (0, -120, 240), `turntable.ldr`) sits inside the hull with its top face level with the roof. Its base is held in a 5 x 7 frame, which two 7L beams with holes along Z tie to the hub's rear end.
- The motor's 4L axle rises through the turntable's open centre (radius 30) into a 28-tooth gear lying on the turntable top. The gear's four pin holes carry the turret, so the motor turns the turret directly and the turntable takes its weight. One motor rotation is one turret turn.
- Turret (`turret.ldr`): the 15L gun is pinned to the gear; a 3 x 3 connector on it is the mantlet. A 13L beam across it carries two 9L side walls, an 11 x 7 frame roof and two curved 11 x 3 panels as the turret sides. The turret is 220 wide and its roof is 100 above the hull roof.
- `0 !LC TURN` declares the turret. Its only warning is the turntable top against the hub, from the box check: the top is a disc of radius 77 and the hub's rear face is 90 from its centre, so the disc clears it.
- Steering is differential, as in tank 1. The missions are in `missions.yaml`.

## Ports

Declared in `model.mpd` as `0 !LC PORT` lines; `lc validate` checks them.

## Open questions

None of this has been built. To confirm on the real parts:

- **Turret drive.** The 28-tooth gear is the only link between the motor's axle and the turret; check that it does not slip up the axle and that the turntable top turns with the turret rather than dragging.
- **Turntable mount.** The base is held by six pins in a 5 x 7 frame, and the frame by two pairs of 7L beams to the hub's rear end. It may sag at the back; the medium motor below is not tied to it.
- **Turret motor mount.** The medium motor hangs on its side pins through two beams per side. It sticks out about 45 LDU behind the tracks.
- **Curved panels.** The turret sides are each held by one pin at the bottom flange.
- **Hub deck.** The two deck beams sit on 2L pins in the large motors' top holes; check that the hub does not rock. The turntable frame also pulls on the hub's rear end.
- **Cables.** Port C's cable runs from the rear of the turret motor along the hull to the hub. It must stay below the turret.
- **Motor direction.** "Clockwise" for port C may turn the turret either way when seen from above.
- Everything listed for tank 1 (track length, axle depth, frame rigidity, drive direction) still applies.
- `scripts/ldraw_measure.py overlap tank-2` lists the medium motor's output boss against the turntable base and its frame; the boss is inside the base's open centre. Pinned pairs (turntable base and its frame, top and base, curved panels and walls) are listed because their boxes meet.
