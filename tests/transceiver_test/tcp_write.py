#!/usr/bin/python3

import pmt
import zmq
import random, time
import numpy as np

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:55555") # connect, not bind, the PUB will bind, only 1 can bind


msg = np.zeros(100, dtype=np.byte)
socket.send(msg.tobytes())

# message = "00000000000000000"
# socket.send (pmt.serialize_str(pmt.to_pmt(message)))
# socket.send(bytes(message, "utf-8"))

print(len(msg.tobytes()))
time.sleep(0.2)
socket.send(msg.tobytes())

for i in range(10):
    msg = np.ones(100, dtype=np.byte)*i
    socket.send(msg.tobytes())
    print(i)

