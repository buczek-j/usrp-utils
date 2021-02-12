"""
Embedded Python Block demo
"""

#  output_block.py
#  created 10/17/2019

import numpy as np
from gnuradio import gr

class my_sync_block(gr.sync_block):
    """
    reads input from a message port
    outputs text
    """
    def __init__(self):
        gr.sync_block.__init__(self, name = "Output_Message_Block", in_sig = [np.byte], out_sig = None)
        #self.callback = callback
    
    def work(self, input_items, output_items):
        print("JOHN MESSAGE")
        print(input_items[0])
        return (0)
