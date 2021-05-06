#!/usr/bin/env python3

from BasicArducopter.BasicArdu import BasicArdu, Frames
from time import sleep
global_home = [42.477681,-71.193708,174.0]

my_drone = BasicArdu(frame=Frames.NED, connection_string='/dev/ttyACM0', global_home=global_home) 

while True:
    print(my_drone.global_home_waypoint.LLA_2_Coords(my_drone.vehicle))
    sleep(1)