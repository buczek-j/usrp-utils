#!/usr/bin/env python3

import dronekit
from pymavlink import mavutil

'''
Method to land the drone
'''

if __name__ == '__main__':
    for connection_string in ['/dev/ttyACM0', 'tcp:192.168.10.2:5762', 'tcp:192.168.10.2:5772', 'tcp:192.168.10.2:5782', 'tcp:192.168.10.2:5792', 'tcp:192.168.10.2:5802', 'tcp:192.168.10.2:5812']:
        try:
            print(connection_string)
            v = dronekit.connect(connection_string)
            msg = v.message_factory.command_long_encode(
                0, 0, mavutil.mavlink.MAV_CMD_DO_FLIGHTTERMINATION, 0,
                1,  # param 1: Flight termination activated if >0.5. min = 0, max = 1
                0,  # param 2: Empty
                0,  # param 3: Empty
                0,  # param 4: Empty
                0,  # param 5: Empty 
                0,  # param 6: Empty
                0   # param 7: Empty
            )
            # print('cmd ' + str(msg))
            v.send_mavlink(msg)
            v.close()
        except:
            pass
    
    exit(0)