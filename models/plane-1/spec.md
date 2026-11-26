# 비행기 1호

## Purpose

An A-10 Thunderbolt II at about 1:42 (60 LDU to a metre): a low straight wing with a rounded leading edge and four missile racks, a raised cockpit with a clear canopy, the gun under the nose, two engine pods high on the rear fuselage and twin fins at the tips of the tailplane. Two things turn: the gun (port A) and both engine fans (port B). It stands on three free wheels and does not drive.

930 LDU long (37 cm), 1060 wide (42 cm), 300 tall (12 cm); 456 parts, about 700 g by a rough part-by-part estimate.

Published in the gallery on 2026-11-27, before a real build, at the maintainer's request. The open questions below are still open.

## Mechanism

- **Fuselage.** Three 11 x 7 frames lie end to end at y 0..20, joined by pins through their end walls; the hub sits on the middle one. A 19 x 11 wing frame lies under the middle frame, and long pins run through the wing frame, the middle frame and the hub. Posts at the nose end and long pins at the tail end tie the hub's end faces to the nose frame and to the fan motor.
- **Nose and cockpit.** A 3 x 11 panel stands on each side of the nose frame, and three 5L beams are stacked behind each panel up to the hub. Seven Technic plates across the top and three round plates at the very front form a deck at y -68; the plates are held by half pins, and the round plates round off the nose tip under the windscreen. On the deck, the curved windscreen faces forward as the nose, and the left and right curved slopes face backward as the canopy and the fairing behind it; they meet on two 2 x 4 bricks. A clear dish on a round plate is the canopy bubble.
- **Gun (port A).** The medium motor lies in the nose with its output down. Its 4L axle has a stop at the bottom that keeps the upper 12-tooth bevel gear on. The lower bevel gear turns the gun axle at y 50, under the nose frame: an 8L and a 5L axle joined by an axle connector, held by a T-beam hanging from each end wall. The connector stops the lower gear sliding back, and half bushes against both T-beams keep the axle in place. Six 3L axle pins in a pulley are the barrels (`gun.ldr`, `0 !LC TURN`). Ratio 1:1.
- **Engines (port B).** The large motor lies flat in the tail frame with its output up, pinned to both side panels. A 12-tooth bevel pair turns an 11L axle at y -110; at its rear a 36-tooth gear drives a 28-tooth gear on each fan axle, 80 LDU to each side. Each pod (`engine.ldr`) is two 7 x 3 curved panels and a 7L beam over the top, on a pylon of two 9L beams standing on the motor. A 13L beam across the front and the rear of both pods carries the three axles. Bushes hold the bevel gear on the 11L axle from both sides. Each 28-tooth gear sits between the rear 13L beam and a half bush. The 36-tooth gear sits between the rear 13L beam and the tail bulkhead. The intake (`fan.ldr`, `0 !LC TURN`) is a pulley with its tyre. The fans turn 1.29 times as fast as the motor, both the same way.
- **Wings.** Each wing (`wing-r.ldr`, `wing-l.ldr`) is ten spanwise rows of beams on four chordwise ribs, with two 11 x 3 curved panels laid lengthwise as a rounded leading edge. The rows over the 19 x 11 frame pin into it; the rest pin into the ribs. The trailing edge steps forward from z 110 at the root to z 30 at the tip, and the 7L beams at the tip are azure.
- **Stores.** Four racks (`missile.ldr`): a 5 x 3 H-beam with two missiles (5L axle, two bushes, a half bush on the nose), held by 3L pins through the wing row, the rib or wing frame and the rack.
- **Tail.** A 5 x 7 frame stands behind the tail frame as a bulkhead. Seven beams across, joined by long pins, are the tailplane at y -70. Each fin is a 5 x 7 frame on edge, pinned between the first and last tailplane beams and filled with a 5 x 3 H-beam that fits its opening.
- **Wheels.** Three wheels (`wheel.ldr`, `0 !LC GROUND`). The main wheels are on T-beam legs hanging from H-beams under the wing frame at z 60. The nose wheel is on a single L-beam on the right side of the nose frame, offset right like the real nose gear. The floor is at y 120.

## Ports

Declared in `model.mpd` as `0 !LC PORT` lines; `lc validate` checks them.

## Checks done on the drawing

- `lc validate`: 0 errors. The only warnings are for the `run_motor_for`, `wait` and `repeat` blocks, whose wording has not been compared with the app.
- `ldraw_measure.py pins`: 0 pins or axles sharing a hole.
- `ldraw_measure.py overlap`: 73 lines, all explained.
  - **Inside openings.** Parts stand inside an open frame (posts, uprights, the rear gun T-beam, the H-beams in the fins).
  - **Motor bosses.** A motor's box reaches as far as its output boss: the medium motor against the rear T-beam, the large motor against the pylon beams.
  - **Connections.** Bevel and spur gears mesh. Axles run through holes. Studs sit in the deck, the bricks and the canopy plate. Rims sit in tyres. The main-gear T-beams sit in the notch of their H-beams.
  - **Curved panels.** The leading-edge panels' boxes reach the wing frame and the ribs, but `slice` shows their lower rail is only 20 square, so the shell stays above and in front of them.
- Balance, estimated from rough part weights: centre of gravity near z 6, main wheels at z 60, nose wheel at z -220.

## Open questions

None of this has been built. To confirm on the real parts:

- **Wing stiffness.** Every wing pin is vertical. A 42 cm span held by pins in a 19 x 11 frame and four ribs may sag at the tips or pull apart when the plane is lifted by a wing.
- **Bevel gears.** Both 12-tooth pairs are drawn 20 LDU from where their axles cross, which comes from the gears' outlines, not from a build.
- **Gun.** The barrels are 3L axle pins in a 6 LDU web and may be loose. The stop on the motor's axle is drawn 2 LDU above the gun axle.
- **Gear faces.** The 36-tooth gear's back face turns against the tail bulkhead and may rub.
- **Engine pods.** Each pod hangs on three pins into its pylon and the pins through the two 13L beams. The three gears turn just behind the rear 13L beam, the pylons and the fan motor, touching their rear faces in the drawing; they may rub.
- **Canopy.** The dish's rim is drawn level with the top of the curved shells; it may rest on them rather than on its centre studs. The shells sit on the deck by their front lips and on the bricks by their rear blocks; how firmly is unknown.
- **Balance.** The weights are guesses (hub 155 g, large motor 55 g, medium motor 38 g, beams 0.23 g a hole). If the plane sits on its tail, move the main gear's H-beams one hole back.
- **Cables.** Neither cable is drawn. The gun motor's cable leaves its rear end 20 LDU in front of the hub and has to reach port A at the hub's rear left. The fan motor's cable leaves its front face above the tail frame and has to reach port B.
- **Buttons.** The canopy stops 10 LDU in front of the hub, clear of the centre button. The fan intakes are 12 LDU above the hub's rear edge and 5 LDU behind the Bluetooth button; check that it can still be pressed.
- **Nose shape.** The Technic plates are 8 studs wide and the cockpit shells 6, so a one-stud shelf shows on each side behind the nose tip. Below the deck the nose is a box with flat sides: the curved panels that could round it are all in the wings' leading edges and the engine pods.
- **Direction.** Which way "clockwise" turns the gun and the fans is not known; mission 2 asks the child to find out.
