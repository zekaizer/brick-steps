# 탱크 3호

## Purpose

Tank 2 driven from a Bluetooth gamepad. An LMS-ESP32 v2 board on port D pairs with the gamepad and passes its sticks and buttons to the hub, so the tank drives and turns its turret by remote control while the hub keeps its stock firmware and the SPIKE App.

## Mechanism

- Everything from tank 2: hub at the front, two large motors on A (left) and B (right), the turret on the turntable turned by the medium motor on C.
- The board stands at the rear, like a stowage box: a 5 x 7 frame is pinned upright to the turret motor's two rear holes (z 390), and the board sits on the frame's four corner holes with axle pins and bushes, as in `templates/lms-esp32v2-mount.mpd`. Its components face backwards. The frame's top (y -150) stays below the gun, so the turret still turns a full circle.
- The board runs Anton's Mindstorms' "BluePad LPF2" firmware (already installed on the maintainer's board). It pretends to be a SPIKE colour sensor and packs the gamepad's sticks and buttons into the sensor's raw red, green and blue values.

## Remote control program

The repository keeps no programs for the board (ADR 0003: LMS-ESP32 work is outside the children's missions), so this is for the adult setting it up:

1. Open the vendor's SPIKE 3 word-block template for BluePad (`bluepad` My Block, from antonsmindstorms.com) in the SPIKE App on the iPad.
2. Set the `bluepad` block's port to **D**.
3. Use the template's tank-drive block with the left stick for motor **A** and the right stick for motor **B**; invert one side if the tank spins on the spot instead of driving.
4. Turn the turret from a second input, for example the right stick's sideways value as the speed of motor **C**, or two buttons that run C clockwise and anticlockwise.
5. Pair the gamepad with the board once it is powered from the hub.

The missions in `missions.yaml` are tank 2's and work without the gamepad.

## Ports

Declared in `model.mpd` as `0 !LC PORT` lines; `lc validate` checks them.

## Open questions

None of this has been built. To confirm on the real parts:

- **Board mount.** The frame hangs on two pins in the medium motor's rear end. The board's weight is far behind the motor's side pins; it may tip the motor.
- **Cable.** The board's LPUP cable leaves its lower long edge and has to reach port D at the hub's side, past the turret motor and the turntable mount.
- **Template details.** The stick ranges, which colour value holds which stick, and the block names come from the vendor's articles (2024 and 2026), not from a test. Check them against the template once it is open in the app.
- **Power.** The board draws from the hub's port; with three motors running, check that the hub's battery keeps it alive.
- Everything listed for tank 2 still applies.
