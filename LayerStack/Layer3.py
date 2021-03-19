#!/usr/bin/env python3

'''
Layer 3 object: Routing layer (Network) 
'''

from LayerStack.Network_Layer import Network_Layer
import struct

class Layer3(Network_Layer):
    def __init__(self, my_config, debug=False):
        '''
        Layer 3 network layer object
        :param my_config: Node_Config object for the current node
        :param debug: bool for debug outputs or not
        '''
        Network_Layer.__init__(self, "layer_3", debug=debug)

        self.my_usrp = bytes(my_config.usrp_ip, "utf-8")

        self.src_pc = bytes(my_config.src.pc_ip, "utf-8")
        self.dest_pc = bytes(my_config.dest.pc_ip, "utf-8")

        self.nh_usrp = bytes(my_config.next_hop.usrp_ip, "utf-8")
        self.ph_usrp = bytes(my_config.prev_hop.usrp_ip, "utf-8")


        if self.debug:
            print('src', self.src_pc, "dest", self.dest_pc, 'nh', self.nh_usrp, 'ph', self.ph_usrp)

    def determine_mac(self, pc_ip):
        '''
        Method to determine the mac_address to send to based on the input ip address 
        [src pv me nh dest]
        :param pc_ip: bytes for the wifi ip address
        :return: bytes for the usrp ip address
        '''
        if pc_ip == self.dest_pc:
            return self.nh_usrp
        elif pc_ip == self.src_pc:
            return self.ph_usrp

    def pass_up(self, stop):
        '''
        Method to pass packet up to l4, nothing needed on up for l3
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l3_packet = self.prev_up_queue.get(True)
            if self.debug:
                print('from l2',l3_packet)
                print()
            self.up_queue.put(l3_packet, True)


    def pass_down(self, stop):
        '''
        Method to determine routing and add appropriate mac address to packet and pass down to l2
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l3_packet = self.prev_down_queue.get(True)  # chunk : []

            if self.debug:
                print('from l4', l3_packet)

            mac_addr = self.determine_mac(self.unpad(l3_packet[22:42])) # determine and replace pc address with mac address then pass to l2
            self.down_queue.put(l3_packet[0:2]+self.pad(self.my_usrp)+self.pad(mac_addr)+l3_packet[42:], True)

