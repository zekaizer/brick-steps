# SPIKE Prime electronic and frame parts

Checked against `ldraw/parts` (official library, 2026-11-21) and Rebrickable inventory 45678-1 v2.

## Hub devices

| LDraw id (use this) | LDraw title | kit part (Rebrickable) | `ports.DEVICES` kind | bbox X / Y / Z (LDU) |
|---|---|---|---|---|
| `45601c01` | Electric Powered Up 6 Port Hub with Yellow Bottom | 45601 + 55422 (battery) | hub (not a port device) | -70..70 / -80..0 / -110..110 |
| `54675c01` | Large Angular Motor, Medium Azure Back, with cable | 54675 | large_motor | -50..65 / -65..30 / -30..314 |
| `54696p01c01` | Medium Angular Motor, Medium Azure Back, with cable | 54696 | medium_motor | -30..65 / -79..30 / -29..314 |
| `37308c01` | Colour Sensor with Coiled Cable | 37308 | color_sensor | -30..65 / -79..29 / -98..126 |
| `37316c01` | Distance Sensor with Coiled Cable | 37316 | distance_sensor | -70..70 / -65..29 / -129..115 |
| `37312c01` | Force Sensor with Coiled Cable | 37312 | force_sensor | -30..65 / -79..30 / -70..216 |

The Z extents above include the cable. Bare variants without a cable (`54675`, `54696p01`, `37308`, ...) also work as port devices; use them when the fixed cable shape would mislead in a picture.

### Large motor `54675` holes (measured)

Body: X -50..50, Y -30..30, Z -30..150. The output boss is the only part that reaches Y -50; it is a disc of radius 29 around (x 0, z 0).

- Output: axle hole along **Y** through (0, ·, 0), open at Y -50 and Y 30. Four pin holes on the rotating face at (±20, -50, 0) and (0, -50, ±20).
- Through holes along Y (Y -30..30) at x ±40, z 0, 80, 120.
- Holes along X on both side faces (x ±50) at y ±20, z -20, 20, 100, 140.
- Holes along Z on the end faces at (±40, 0, -30) and (±40, 0, 150).
- Lying on its side with the output outward: Rz+90 for the right motor (output towards +X), Rz-90 for the left. Two motors placed at x ±40 leave a 20 LDU gap for a beam between them.

### Medium motor `54696p01` holes (measured)

Body: X -30..30, Y -30..30, Z -29..150; the output boss (radius 29) reaches Y -50.

- Output: axle hole along **Y** through (0, ·, 0), open at Y -50 and Y 30. Four pin holes on the rotating face at (±20, -50, 0) and (0, -50, ±20), the same square as a 3 x 3 connector or a 28-tooth gear.
- Holes along X on both side faces (x ±30) at y ±20, z -20, 20 and 140. Holes along Z on the rear end at (±20, 0, 150). The cable leaves the housing at (0, 0, 150).
- Standing with the output up (identity), it is 80 tall with the boss and 180 long on Z.

### Hub `45601c01` ports (measured, letters from a real hub)

USB and the Bluetooth button are at +Z, the Bluetooth button on +X. The six port sockets face out of the long sides at x ±70, y -68, z 40/0/-40. A/C/E are on -X and B/D/F on +X, A and B at the +Z end: with the Bluetooth end up, the left side reads A, C, E from the top. `src/lego_creator/cables.py` holds these points. The large motor's cable leaves the housing at (0, 14, 150).

### Hub `45601c01` holes (measured)

Bottom center origin. Vertical holes on the bottom face (y 0) at (±60, ±100), (±20, ±100) and (±60, ±60); on the top face at (±60, -80, ±100). Holes along Z on both ends at x ±40, y -10, -30, -50. Holes along X on the sides at (±70, -50, ±80).

Buttons on the top face (y -80), read from a render to about ±5: the centre button, with the left and right buttons beside it, is round (0, -75) with radius about 22; the Bluetooth button is round (40, 80) with radius about 12. Keep both uncovered.

### Frame `39794` (11 x 7) holes (measured)

Flat in XZ, 20 thick on Y, X -70..70, Z -110..110. Holes alternate around the rim:
- through the plane (along Y) every 40 LDU: x ±60 at z ±100, ±60, ±20, and x ±20 at z ±100;
- in the plane: along X through the long sides at z 0, ±40, ±80; along Z through the short sides at x 0, ±40.

Do not use these aliases: `54696c01` (moved to 54696p01c01) and `u9393c01` (moved to 45601).

## Turning and covering parts (measured)

| part | frame and holes |
|---|---|
| turntable top `18938` (60 teeth) | centre origin. Y -30..10, radius 77. Teeth: pitch radius 75, band y -5..10. Side holes along X at (±50, -20, z -20/0/20). Open centre, radius 30 |
| turntable base `18939` | same origin as the top. Y -5..30, flange radius 67 down to y 12, block x ±50, z ±30 below it. Side holes along X at (±50, 20, z -20/0/20). Open centre, radius 30 |
| 5 x 7 frame `64179` turned Ry+90 | its opening is x ±50, z ±30, the turntable base's block. The in-plane holes at (x ±50..±70, z -20/0/20) meet the base's side holes |
| 28-tooth gear `46372` | axle hole at the centre and four pin holes at (±20, 0), (0, ±20); turned Rx+90 it lies flat and couples a vertical axle to a 3 x 3 square of pins |
| 36-tooth gear `32498` | radius 47; an axle hole at the centre and pin holes at (±20, 0) |
| curved panel `11954` (11 x 3) | X -30..10, Y -49..10, long side on Z (±110). Lower rail around (0, 0), 20 square: pin holes along Y from below at z 0/±40/±80 and along X at z ±20/±60. Upper rail around (-20, -40): holes along X at z ±40/±60/±80. The wall between bulges to x 7, so +X is the outside. Against a motor's side, the lower rail stands one beam away and the upper rail touches. The 7 x 3 panel `24119` has the same section but only vertical holes below (z 0, ±20, ±40) and X holes at z ±40 above. Both rails of both panels have holes along Z at their ends |
| curved panel `11954` as a leading edge | with `0 0 -1 -1 0 0 0 1 0` it lies along X: the lower rail at (y0, z0) is the rear edge, the upper rail at (y0 + 20, z0 - 40) the front, and the skin curves down and forward between them to a nose at z0 - 49. Its rear rail has vertical holes at x ±20, ±60 from the centre. With y0 10 the rear rail sits level with beams at y 0..20 and the nose reaches y 40 |
| two `24119` and a 7L beam as a pod | the inner panel turned Ry180 and the outer one unturned, lower rails 80 apart; the upper rails then stand 20 apart and a 7L beam with X holes fills the gap, held by one 3L pin through all three at each end. A 13L beam with Z holes across the rail ends carries an axle on the pod's centre line |
| windscreen `41751`, curved slopes `41749` / `41750` | origin at the top of the rear, X ±60 / -50..10 / -10..50, Z -140..20, a thin shell that curves down to the front. Two rows of studs on top at the rear. Underneath, the rear block sits 24 below the top and the front lip 48 below. Facing each other at the rear, `41751` forward and the two slopes turned Ry180 side by side, they make a hump 320 long on a deck 48 below its top, with a 2 x 4 brick under the joint |
| dish `44375b` (6 x 6, inverted) | studs on top at the origin; Y -4..16, the rim 16 below the top. On a 2 x 2 round plate on a flat top its rim is level with that top |
| Technic plate `3738` (2 x 8) | X ±80, holes along Y at x -60..60, every 20, on the centre line |
| half pin `4274` | along X: pin from -20 to 0, then a 4 LDU stud end. Through a Technic plate into a hole below, it ends flush with the plate's top |
| brick `39789` (2 x 4) | body y 0..24, three axle holes along Y at x -20, 0, 20 |
| wing frame `39369` (19 x 11) | X ±110, Z ±190, 20 thick. Holes along Y on a full grid at x -80..80, z -160..160, every 20, and on the rim at x ±100, z -180..180, every 40. Holes along X in the long sides at z -160..160, every 40, and along Z in the short sides at x -80..80, every 40. Turned Ry+90 under an 11 x 7 frame, all ten of the frame's vertical holes meet its holes |
| 5 x 7 frame `64179` | X ±50, Z ±70, 20 thick; opening x ±30, z ±50. Holes along Y at (±40, z ±20/±60), along X at (±50, z -40/0/40), along Z at (x -20/0/20, ±70). A 5 x 3 H-beam fills the opening with 1 LDU to spare |
| H-beam `14720` (5 x 3) | X ±29, Z ±49. The cross bar at z 0 has holes along X at z -20, 0, 20; the end bars at z ±40 have holes along Y at x -20, 0, 20 |
| wedge belt wheel `4185a` with tyre `2815` | same origin; the tyre is a ring of radius 38, 8 thick |
| panel `15458` (3 x 11) | X ±110, Z ±30, 20 thick. Pin holes along Z into both long edges at x -60..60, every 20; through holes along Y at (±80, ±20); holes along X into the ends at z 0/±20. On its long edge with `0 1 0 0 0 1 1 0 0` it stands on an 11 x 7 frame's side wall, pinned at the frame's ±20 and ±60 holes |
| rubber belt `85543` (15 mm) | a ring of radius 21 in the XY plane |
| T-beam `60484` (3 x 3) | holes along Y. Stem end at the origin, then (0, 0, 20); the bar is at z 40 with holes at x -20, 0, 20 |
| bent beam `32526` (3 x 5) | holes along Y. The 5-hole arm runs from the origin to (0, 0, 80); the 3-hole arm turns to +X at z 80, with holes at x 20 and 40 |
| wedge belt wheel `4185a` | axis Z, radius 30, 10 thick. Axle hole at the centre and six pin holes at radius 20, every 60° from (0, ±20); the web around them is 6 thick |
| 3L axle pin `18651` | along X. Pin from x -30 to -10, collar at -10, 2L axle from -10 to 30 |
| small wheel `56903` with tyre `61254` | axis Z, both at the same origin. Rim radius 21, 20 wide; tyre radius 30, 18 wide |
| round plate `4032a`, round tile `14769p0e` | top centre origin, body y 0..8, 40 across. The tile's origin goes 8 above the plate's |

A gear of 20 teeth meshes with the turntable's 60 at 100 LDU from its centre (module 1).

Two 12-tooth double bevel gears `32270` (radius 17, 20 thick) on axles that cross at a right angle: draw each gear's centre 20 LDU from the crossing point, so the tooth rims overlap 7 x 7. Computed from the outlines for plane 1, not checked on a build. By the same sum a 20-tooth gear pairs with another at 30 each, and a 12 with a 20 at 30 and 20.

## SPIKE-specific structural parts in 45678

| LDraw id | LDraw title | kit qty (color) |
|---|---|---|
| 39369 | Technic Beam 19 x 11 Baseplate | 2 (yellow 14) |
| 39790 | Technic Beam 15 x 11 with Open Center 13 x 9 | 2 (medium azure 322) |
| 39794 | Technic Beam 11 x 7 with Open Center 9 x 5 | 2 (magenta 26) |
| 39793 | Technic Connector Block 3 x 3 with 9 Perpendicular Holes | 6 black + 8 magenta |
| 39370 | Technic Beam 5 x 3 H-shaped with Ball Socket | 1 (medium azure) |
| 52629 | Technic Ball 19mm for Ball Castor | 1 (white) |
| 39789 | Brick 2 x 4 with 3 Axleholes Vertical | 3 each in 5 colors |
| 39367p01 | Wheel 14 x 48, integral medium azure tyre | 4 (kit id 39367pat0001) |

## Kit IDs that differ from LDraw

`inventory/id-map.csv` is authoritative. The entries for 45678 and 45681 are:
- `4185a` maps to 4185 and `32198a` maps to 32198, because the plain LDraw ids are aliases.
- `14769p0e` maps to 14769pr0080 (spiral print).
- `32005` maps to 32005a. This mapping is inferred from the part names only.

Kit items with no LDraw model are the USB cable 39881, storage bins and trays, and the sticker sheet. Print tiles `98138pr0062` and `98138pr0076` have not been matched to an LDraw id yet.

## Pybricks

Children's missions use the SPIKE App, not Pybricks (ADR 0003). Pybricks remains relevant for maintainer projects such as the LMS-ESP32 board.

Pybricks has no separate large or medium motor class: both use `pybricks.pupdevices.Motor`. The sensors use `ColorSensor`, `UltrasonicSensor` (the distance sensor) and `ForceSensor`. The hub is `pybricks.hubs.PrimeHub`.

## Third-party: LMS-ESP32 v2.0 (Anton's Mindstorms)

Source: product page (SKU CM0047B), read 2026-11-22. The board has no LDraw part.

- Connects through the included LPUP cable to a hub port, so it uses one of ports A–F. With Pybricks the hub talks to it over UART (PUPRemote / uRemote). Plan for UART, not hub-side I2C.
- The board measures 39.8 × 55.8 mm, which the vendor calls "the exact footprint of a LEGO Technic 5×7 frame". That matches LDraw `64179` (Technic Beam 7 x 5 with Open Center 5 x 3), whose bounding box is 100 × 140 LDU on X × Z and 20 LDU thick.
- The four mounting holes sit on the corner vertical holes of `64179`, at (±40, ±60) LDU, which is 32 × 48 mm center to center. This comes from a vendor photo of the board pinned to that frame.
- The board can power servos and LEDs at up to 1000 mA from the LEGO battery. It has a 28-pin 2.54 mm header, STEMMA QT/Qwiic, Grove I2C, a 10-pin JST-SH display connector and USB-C.
- It comes with MicroPython 1.24 and the lpf2, PUPRemote, SerialTalk, ulab and Neopixel libraries.

### Custom part `lms-esp32v2`

- File: `custom/parts/lms-esp32v2.dat`. It is generated by `scripts/gen_lms_esp32v2.py`, so edit the script and regenerate it; never edit the `.dat` by hand.
- Frame: the origin is the center of the PCB bottom face. The PCB lies in the XZ plane with its long side along Z, and its top face is at y = -4. With identity rotation it lines up with `64179` placed with identity rotation; put the board at the frame's top face (frame y - 10).
- Layout: the LPUP socket and the ESP32 module are on the -X long edge, and the 2 × 14 header is on the +X long edge. USB-C is on the +Z short edge; Grove and Qwiic are on the -Z short edge.
- The outline and the holes are trustworthy. Every component box is a clearance envelope estimated from photos (±3 mm). The tallest part is the header, about 8.5 mm above the PCB, and the LPUP cable needs extra room above its socket.
- Port device id is `lms-esp32v2` (kind `lms_esp32`). Its kit inventory is `inventory/lms-esp32v2.csv`.
- Mount template: `templates/lms-esp32v2-mount.mpd`. It uses the frame, 4 axle pins 3749 (pin end in the frame) and 4 bushes 3713 clamping the board. Bush grip on the 16 LDU axle stub has not been checked on a real build.

## Third-party: tank track set (`inventory/tank-tracks.csv`)

Identified from photos. Exact counts are unknown; the owner reports enough for one two-track tank:
- Tread links: use `57518` (Technic Chain Tread 5 Wide). The photos cannot tell it apart from the reinforced `88323`, and both have the same geometry. The hinge-loop side is the inner side that meshes with the sprocket.
- Sprocket: `57519` (Technic Sprocket Wheel 40.4). It has 6 pin holes at radius 20 around the center axle hole, measures 102 LDU in diameter and 36 LDU wide, and its axis is along Z.
- Tread link `57518` frame: hinge pin at the origin, body towards -Z, tread face towards -Y, 96 wide on X. The link pitch is taken as 30 LDU and the hinge circle on the sprocket as radius 48.5 (10 links around); both are inferred from the geometry, not checked on the real parts. `scripts/gen_tank_track.py` places a closed loop.
- The same photos show the large turntable (`18938` top and `18939` base) and the quarter gear ring `24121`, but these come from 45681 and are not part of this set.

## Third-party: tank differential-steering gearbox (`inventory/tank-diff-gearbox.csv`)

Bought assembled from AliExpress as a "tank differential" and kept assembled, so models use it as one part. Nothing came with it to list its parts; everything below is read from six photos (2026-11-28), with positions taken from the frame's hole pitch.

- File: `custom/parts/tank-diff-gearbox.dat`, generated by `scripts/gen_tank_diff_gearbox.py` from official parts; edit the script and regenerate.
- Frame: origin at the box centre. Two 11 x 7 frames `39794` lie flat (XZ, long side along Z) with centre planes at y = -20 and 20, so the box is 140 × 60 × 220 LDU without what sticks out. Long 3L pins fill the corner holes and the short sides' x ±20 holes; the other frame holes are free for mounting, except that parts in the gap sit behind the side holes at z 0 and ±60.
- Outputs: one axle at each short end, along Z on the middle line (x 0, y 0), held by a 3L beam pinned across both frame ends at x 0 and ending at z = ±150.
- Inputs, both on -X at y 0: the black drive axle at z 0 out to x -95, and the grey steering axle at z -60 out to x -90. The other long side has none.
- Gear train: open differentials `62821` on the middle line at z ±62, ring gears outwards. Four 20T double bevels at x ±40, z ±60, turned 9° so their teeth fall between the ring's, mesh the ring gears; on +X a 28T double bevel at z 0 joins the two 20Ts (20-28-20, 60 LDU apart), so the rings turn opposite ways. The steering axle carries the -X, -Z 20T. A black U bracket (block at x -40, arms at z ±27) holds a short axle from each differential's inner side at x 0, with a 20T bevel (z -14) on the steering side and a yellow bush on the other; along X at z 0 sit end to end the block, a 12T bevel and a yellow bush on the drive axle, a black round connector and the 28T.
- Fit, checked by crossing triangles and by how far the gears' tip outlines overlap in the plane of both axes (a spur pair at book distance overlaps 4 LDU): ring and 20T 5.5, 20T and 28T 3.8, 12T and 20T bevel 3.0. Nothing else touches. The ring gear meets the frame end from z ±63, which is what holds the differentials at ±62. The 12T bevels inside the differentials are left out of the part: in the LDraw case there is no room for them at the distance where they mesh.
- Owner's test: the steering axle turns the outputs opposite ways. How the drive axle reaches the differentials, and so the ratios, is not clear from the photos: count output turns against input turns before designing around them.
- Stand-ins: the connectors in the gap and the bracket are drawn with parts of the right size, not identified ones. Positions follow the photos within about half a module, then the fit above.
