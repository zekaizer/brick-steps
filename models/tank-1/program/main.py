from pybricks.hubs import PrimeHub
from pybricks.parameters import Direction, Port
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.tools import wait

hub = PrimeHub()
drive_left = Motor(Port.A, Direction.COUNTERCLOCKWISE)
drive_right = Motor(Port.B)
# Sprocket plus tread, and the distance between the two track centers, in mm. Calibrate on the real build.
tank = DriveBase(drive_left, drive_right, wheel_diameter=45, axle_track=118)

# Drive a square.
for _ in range(4):
    tank.straight(300)
    tank.turn(90)
    wait(200)
