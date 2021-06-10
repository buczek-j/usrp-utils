#!/usr/bin/env python3

'''
Layer 5 object: Sample Application layer
'''

from time import sleep, time
import random, string, struct
from math import ceil

from LayerStack.Network_Layer import Network_Layer


class Layer5(Network_Layer):
    def __init__(self, my_config, layer4, debug=False):
        '''
        Layer 5 Application layer object
        :param my_config: Node_Config object for the current node
        :param layer4: Layer4 object for the current node
        :param debug: bool for debug outputs or not
        '''
        Network_Layer.__init__(self, "layer_5", debug=debug)

        self.my_config = my_config
        self.layer4 = layer4
        self.transmit = False
        self.tspt_rate = 1000000			# Initial tansport layer rate in bps

    def pass_down(self, stop):
        '''
        Method to pass down packets to the lower layers
        :param stop: function returning true/false to stop the thread
        '''
        
        payload = bytes((self.layer4.l4_size - self.layer4.l4_header) * random.choice(string.digits), "utf-8")
        pktno_l4 = 1
        l4_pkts_to_send = 1000000

        l4_maximum_rate = self.tspt_rate/8 	    # bps -> [Bps]
        max_pkt_per_sec = max(1,int(ceil(l4_maximum_rate/self.layer4.l4_size)))
        print("MPPS:", max_pkt_per_sec)

        while not stop():
            if self.transmit:
                if pktno_l4 == l4_pkts_to_send:
                        print("Max number of packets sent")
                        break

                for counter_packet in range(int(max_pkt_per_sec)):
                    time_stamp = time()
                    packet = struct.pack('l', pktno_l4)  + self.pad(bytes(self.my_config.pc_ip, "utf-8")) + self.pad(bytes(self.my_config.dest.pc_ip, "utf-8")) +  struct.pack('d', time_stamp) + payload # 56 bytes added + payload
                    self.down_queue.put(packet, True)
                    pktno_l4 += 1
                    sleep(1.0/max_pkt_per_sec)


    def pass_up(self, stop):
        '''
        Method to use received packets
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            msg = self.prev_up_queue.get(True)
            # print(msg)
            # print('...')

