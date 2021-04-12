#!/usr/bin/env python3

import pmt
import zmq
import random, time
import numpy as np

if __name__ == '__main__':
    '''
    '''
    # writer
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:55555") # connect, not bind, the PUB will bind, only 1 can bind
    msg = np.ones(128, dtype=np.byte)

    #reader
    rcv_socket = context.socket(zmq.SUB)
    rcv_socket.connect("tcp://127.0.0.1:55556") # connect, not bind, the PUB will bind, only 1 can bind
    rcv_socket.setsockopt(zmq.SUBSCRIBE, b'') # subscribe to topic of all (needed or else it won't work)

    while True:
        socket.send(msg)
        if rcv_socket.poll(10) != 0: # check if there is a message on the socket
            msg = rcv_socket.recv() # grab the message
            print(len(msg)) # size of msg
            data = np.frombuffer(msg, dtype=np.byte, count=-1) 
            print(data)

        else:
            time.sleep(0.1) # wait 100ms and try again

        

        
        
