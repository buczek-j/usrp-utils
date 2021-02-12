#!/usr/bin/env python3

'''
Layer 1 object: Physical layer 
'''

from L1_protocols.TRX_ODFM_USRP import TRX_ODFM_USRP
from Network_Layer import Network_Layer


class Layer1(Network_Layer):
    def __init__(self, window):
        '''

        '''
        Network_Layer.__init__(self, "layer_1", window)