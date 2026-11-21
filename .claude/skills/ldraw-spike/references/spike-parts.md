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

The Z extents above include the cable. Bare variants without a cable (`54675`, `54696p01`, `37308`, ...) also work as port devices.

Do not use these aliases: `54696c01` (moved to 54696p01c01) and `u9393c01` (moved to 45601).

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

Pybricks has no separate large or medium motor class: both use `pybricks.pupdevices.Motor`. The sensors use `ColorSensor`, `UltrasonicSensor` (the distance sensor) and `ForceSensor`. The hub is `pybricks.hubs.PrimeHub`.
