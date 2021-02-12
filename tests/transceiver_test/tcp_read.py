#!/usr/bin/python3

import zmq
import numpy as np
import time
import matplotlib.pyplot as plt

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:55558") # connect, not bind, the PUB will bind, only 1 can bind
socket.setsockopt(zmq.SUBSCRIBE, b'') # subscribe to topic of all (needed or else it won't work)

while True:
    if socket.poll(10) != 0: # check if there is a message on the socket
        msg = socket.recv() # grab the message
        print(len(msg)) # size of msg
        data = np.frombuffer(msg, dtype=np.byte, count=-1) 
        print(data)

    else:
        time.sleep(0.1) # wait 100ms and try again