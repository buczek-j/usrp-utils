"""
Embedded Python Block demo
"""

#  epy_block_0.py
#  created 10/17/2019

import numpy as np
from gnuradio import gr

import pmt

textboxValue = ""

class my_sync_block(gr.sync_block):
    """
    reads input from a message port
    outputs text
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name = "Embedded Python demo",
            in_sig = None,
            out_sig = [np.byte])
        self.message_port_register_in(pmt.intern('msg_in'))
        self.message_port_register_out(pmt.intern('clear_input'))
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)

    def handle_msg(self, msg):
        global textboxValue

        textboxValue = pmt.symbol_to_string (msg)
        # print (textboxValue)
    
    def work(self, input_items, output_items):
        global textboxValue

        # get length of string
        _len = len(textboxValue)
        if (_len > 0):
            # terminate with LF
            textboxValue += "\n"
            _len += 1
            # store elements in output array
            for x in range(_len):
                output_items[0][x] = ord(textboxValue[x])
            textboxValue = ""
            self.message_port_pub(pmt.intern('clear_input'), pmt.intern(''))
            return (_len)
        else:
            return (0)