"""Generate custom/parts/tank-diff-gearbox.dat, an approximate LDraw model of a Technic-compatible tank
differential-steering gearbox bought assembled from AliExpress and kept assembled.

The part is drawn from official LDraw parts, so it renders like the real box while models count it as one
part. Read from six photos of the box (no part list exists), positions taken from the frame's hole pitch:
- Two 11 x 7 frames (39794) lie flat 40 LDU apart (six round holes on each long side, two on each short side
  between the corners, five side holes). Long 3L pins through both frames hold them; parts in the 20 LDU gap
  between them carry the side axles.
- At each short end a 3L beam stands across both frame ends at x 0, pinned into them, and carries an output
  axle on the middle line; the axle sticks out about one module.
- Two open differentials (62821) sit on that line at z +-62, ring gears outwards. The 12T bevels inside them
  are left out: the LDraw case leaves no room for them at the distance where they mesh.
- Four 20T double bevels at x +-40, z +-60 mesh the ring gears. On +X the two 20Ts and a 28T double bevel
  between them (z 0) make a 20-28-20 chain, 60 LDU apart.
- A black U bracket (a 3L beam at x -40 and two thin beams as arms at z +-27) holds a short axle from each
  differential's inner side at x 0: a 20T bevel on the -Z one (the steering side), a yellow bush on the +Z one.
  Along X at z 0 sit, end to end, the bracket block, a 12T bevel and a yellow bush on the black drive axle,
  a black round connector and the 28T.
- Inputs on -X at y 0: the black drive axle (z 0) and the grey steering axle (z -60, on the -Z ring's 20T);
  the +Z 20T on -X turns on an axle pin. Turning the steering axle turns the outputs opposite ways (owner's
  test). How the drive axle reaches the differentials is not clear from the photos.
- The connectors in the gap and the bracket are stand-ins of the right size; the real ones are not identified.
- Places come from the photos and were then set so gears mesh and nothing else touches, checked by crossing
  triangles and by how far the gears' tip outlines overlap.
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "custom" / "parts" / "tank-diff-gearbox.dat"

BLACK, BLUE, YELLOW, TAN, LIGHT_GREY, DARK_GREY = 0, 1, 14, 19, 71, 72
FRAME_Y = 20  # the frames' centre planes are at y = -20 and 20; the gap between them is y -10..10
GEAR_X, GEAR_Z = 40, 60  # the 20T double bevels on the ring gears; 60 from the 28T between them on +X
# Differential centres: the ring gear meshes the 20T (tips overlap 5.5 LDU) and clears the frame end, which
# it reaches from z 63. The 20Ts are turned 9 degrees so their teeth fall between the ring's.
DIFF_Z = 62
GEAR_PHASE = 9
SIDE_X = 60  # parts in the gap along the long sides

IDENTITY = (1, 0, 0, 0, 1, 0, 0, 0, 1)
RY180 = (-1, 0, 0, 0, 1, 0, 0, 0, -1)
RY90 = (0, 0, 1, 0, 1, 0, -1, 0, 0)  # local Z -> +X, local X -> -Z
RX90 = (1, 0, 0, 0, 0, -1, 0, 1, 0)  # local Y -> +Z, local Z -> -Y
RZ90 = (0, -1, 0, 1, 0, 0, 0, 0, 1)  # local X -> +Y, local Y -> -X
BEARING = (0, 0, 1, 1, 0, 0, 0, 1, 0)  # 32184 lying along Z, centre hole along X
ARM = (0, 0, 1, 1, 0, 0, 0, 1, 0)  # thin beam lying along X, holes along Z
DIFF_POS = (0, -1, 0, 1, 0, 0, 0, 0, 1)  # 62821 with its windows up, ring gear towards +Z
DIFF_NEG = (0, -1, 0, -1, 0, 0, 0, 0, -1)  # the same, ring gear towards -Z


def ref(color: int, x: float, y: float, z: float, m: tuple[float, ...], name: str) -> str:
    return f"1 {color} {x:g} {y:g} {z:g} {' '.join(f'{v:.6g}' for v in m)} {name}.dat"


def on_x(deg: float) -> tuple[float, ...]:
    """A gear whose local Z axis points along +X, turned deg about it."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (0, 0, 1, s, c, 0, -c, s, 0)


def frames() -> list[str]:
    lines = [ref(BLACK, 0, y, 0, IDENTITY, "39794") for y in (-FRAME_Y, FRAME_Y)]
    for z in (-100, 100):
        lines += [ref(LIGHT_GREY, x, 0, z, RZ90, "6558") for x in (-SIDE_X, SIDE_X)]  # corners
        lines += [ref(BLUE, x, 0, z, RZ90, "6558") for x in (-20, 20)]  # short sides
    for side in (-1, 1):
        lines += [ref(LIGHT_GREY, side * SIDE_X, 0, z, BEARING, "32184") for z in (-GEAR_Z, GEAR_Z)]
        lines.append(ref(BLACK, side * SIDE_X, 0, 0, RZ90, "32523"))  # holes along X at z 0, +-20
    return lines


def outputs() -> list[str]:
    lines = []
    for end in (-1, 1):
        lines.append(ref(BLACK, 0, 0, end * 120, RX90, "32523"))
        lines += [ref(BLUE, 0, y, end * 110, RY90, "61332") for y in (-FRAME_Y, FRAME_Y)]
        lines.append(ref(LIGHT_GREY, 0, 0, end * 100, RY90, "32073"))  # z 50..150
        # the ring gear is the part's +Z end
        lines.append(ref(DARK_GREY, 0, 0, end * DIFF_Z, DIFF_POS if end > 0 else DIFF_NEG, "62821"))
        # inner side axle through the bracket arm: z -52..-12 into the 20T bevel, z 12..52 into the bush
        lines.append(ref(LIGHT_GREY, 0, 0, end * 32, RY90, "32062"))
    return lines


def gears() -> list[str]:
    lines = [ref(TAN, x, 0, z, on_x(GEAR_PHASE), "32269") for x in (-GEAR_X, GEAR_X) for z in (-GEAR_Z, GEAR_Z)]
    lines.append(ref(LIGHT_GREY, GEAR_X, 0, 0, on_x(0), "46372"))  # x 30..50
    lines.append(ref(BLACK, 40, 0, 0, IDENTITY, "4519"))  # 28T axle, x 10..70
    # +X 20Ts turn on axle pins, pin end in the bearing block
    lines += [ref(BLACK, 50, 0, z, IDENTITY, "43093") for z in (-GEAR_Z, GEAR_Z)]
    lines.append(ref(TAN, -50, 0, GEAR_Z, RY180, "43093"))
    lines.append(ref(LIGHT_GREY, -60, 0, -GEAR_Z, IDENTITY, "4519"))  # steering input, x -90..-30
    # Middle, end to end along X at z 0 as in the photos: bracket block, 12T bevel, bush, a 2L round connector and
    # the 28T. The connector's round holes take the drive axle and the 28T's axle, so the two turn apart. The 12T
    # meshes a 20T bevel on the -Z inner axle (tips overlap 3 LDU).
    lines.append(ref(BLACK, -55, 0, 0, IDENTITY, "32073"))  # drive input, x -105..-5
    lines.append(ref(BLACK, -40, 0, 0, RZ90, "32523"))  # bracket block, x -50..-30
    lines += [ref(BLACK, -20, 0, z, ARM, "41677") for z in (-27, 27)]  # bracket arms z +-(22..32), holes at x -20, 0
    lines.append(ref(TAN, -27, 0, 0, RY90, "6589"))  # 12T, x -30..-20, teeth towards +X
    lines.append(ref(YELLOW, -15, 0, 0, RY90, "32123b"))  # x -20..-10
    lines.append(ref(BLACK, 10, 0, 0, IDENTITY, "62462"))  # round connector, x -10..30
    lines.append(ref(TAN, 0, 0, -14, IDENTITY, "32198a"))  # 20T bevel, z -21..-11
    lines.append(ref(YELLOW, 0, 0, 17, IDENTITY, "32123b"))  # z 12..22
    return lines


HEADER = """\
0 Tank Differential-Steering Gearbox (Approximate)
0 Name: tank-diff-gearbox.dat
0 Author: Brick Steps (generated by scripts/gen_tank_diff_gearbox.py)
0 !LDRAW_ORG Unofficial_Part
0 BFC NOCERTIFY
0 // Origin: box centre. Two 11 x 7 frames flat (XZ), long side along Z, centre planes at y = -20 and 20.
0 // Output axles along Z on the middle line (x 0, y 0), ends at z = +-150.
0 // Inputs on -X at y 0: drive axle at z 0 out to x -105, steering axle at z -60 out to x -90.
0 // Read from photos; positions within about half a module. See the generator's docstring.
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(HEADER + "\n".join(frames() + outputs() + gears()) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
