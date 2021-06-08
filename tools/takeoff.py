#!/usr/bin/env python3

import dronekit
from time import sleep
'''
Method to land the drone
'''

if __name__ == '__main__':
    for connection_string in ['/dev/ttyACM0', 'tcp:192.168.10.2:5762', 'tcp:192.168.10.2:5772', 'tcp:192.168.10.2:5782', 'tcp:192.168.10.2:5792', 'tcp:192.168.10.2:5802', 'tcp:192.168.10.2:5812']:
        try:
            print(connection_string)
            v = dronekit.connect(connection_string)
           
            print('Waiting to arm')
            while not v.is_armable:
                sleep(0.5)

            v.mode="GUIDED"
            v.armed=True

            while not v.armed:
                print("Waiting for arming...")
                sleep(0.5)
            
            v.simple_takeoff(5)
            v.close()
        except:
            pass

    exit(0)