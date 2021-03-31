#!/usr/bin/env python3

'''
Layer 3 object: Routing layer (Network) 

[Header len], [Packet Len], [  flag ], [source IP], [ dest IP ], [optional], [payload]
[ 2 bytes  ], [  4 bytes ], [2 bytes], [ 4 bytes ], [ 4 bytes ], [0-40bytes], [0-X byets] 
'''

from LayerStack.Network_Layer import Network_Layer, addr_to_bytes
import struct
L3_Default_len=16

class Layer3(Network_Layer):
    def __init__(self, my_config, debug=False):
        '''
        Layer 3 network layer object
        :param my_config: Node_Config object for the current node
        :param debug: bool for debug outputs or not
        '''
        Network_Layer.__init__(self, "layer_3", debug=debug)
        self.my_pc = addr_to_bytes(my_config.pc_ip)
        self.my_usrp = addr_to_bytes(my_config.usrp_ip)

        self.src_pc = addr_to_bytes(my_config.src.pc_ip)
        self.dest_pc = addr_to_bytes(my_config.dest.pc_ip)

        self.nh_usrp = addr_to_bytes(my_config.next_hop.usrp_ip)
        self.ph_usrp = addr_to_bytes(my_config.prev_hop.usrp_ip)


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
    
    def determine_dest(self, addr):
        '''
        Method to determine the 
        '''
    
    def make_l3_pkt(self, source_ip, dest_ip ,flag=0, optional=b'', payload=b''):
        '''
        Method to format an l3 packet
        TODO
        '''
        header_len = struct.pack("H", (len(optional)+L3_Default_len))
        pkt_len = struct.pack("I", (len(optional)+L3_Default_len+len(payload)))

        if type(source_ip)!=bytes:
            source_ip = addr_to_bytes(source_ip)
        if type(dest_ip)!=bytes:
            dest_ip = addr_to_bytes(dest_ip)
        if type(flag)!=bytes:
            flag = struct.pack("H", flag)
        return header_len + pkt_len + flag + source_ip + dest_ip + optional + payload

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
            
            # TODO implement flags

            if l3_packet[12:16] == self.my_pc:
                self.up_queue.put(l3_packet, True)
            else: 
                mac_addr = self.determine_mac(l3_packet[12:16])
                self.prev_down_queue.put(struct.pack('H', 1) + mac_addr + self.my_usrp + struct.pack('H', 0) + l3_packet, True)


    def pass_down(self, stop):
        '''
        Method to determine routing and add appropriate mac address to packet and pass down to l2
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l4_packet = self.prev_down_queue.get(True)  # chunk : []
            # TODO implement flags
            

            if self.debug:
                print('from l4', l3_packet)

            mac_addr = self.determine_mac(l3_packet[12:16]) # determine and replace pc address with mac address then pass to l2
            self.down_queue.put( struct.pack('H', 1) + mac_addr + self.my_usrp + struct.pack('H', 0) +  self.make_l3_pkt(self.my_pc, self.dest_pc), True) # TODO make better

