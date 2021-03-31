#!/usr/bin/env python3

'''
Layer 4 object: Transport layer

[l4 pkt number], [source port], [dest port], [l4 length], [timestamp], [l4 ack number], [payload]
'''

from LayerStack.Network_Layer import Network_Layer, addr_to_bytes
from LayerStack.Layer2 import L2_Header_Len, L2_Num_Frames, L2_Num_Blocks, L2_Block_Size
from LayerStack.Layer3 import L3_Default_len

from threading import  Event, Lock
from time import time
import struct, csv, os

l4_ack = Event()
l4_down_access = Lock()     

L4_Header_Len=24

class Layer4(Network_Layer):
    def __init__(self, my_config, timeout=1, n_retrans=3, debug=False):
        '''
        Layer 4 Transport layer object
        :param my_config: Node_Config object for the current node
        :param num_frames: int for the number of l2 frames in one l4 packet
        :param num_blocks: int for the number of blocks in an l2 message
        :param l2_header: int for the byte length of the l2 header
        :param l2_block_size: int for the byte length for one l2 block
        :param timeout: int for the l4 ack timeout
        :param n_retrans: int for the number of times to retransmit a l4 message
        :param debug: bool for debug outputs or not
        TODO
        '''
        Network_Layer.__init__(self, "layer_4", debug=debug)
        self.my_pc = addr_to_bytes(my_config.pc_ip)

        self.timeout=timeout
        self.n_retrans = n_retrans
        self.unacked_packet = 0        

        # Measurements
        self.n_recv = 0
        self.n_sent = 0
        self.n_ack = 0  # number of acks recvd

    def make_l4_pkt(self, pkt_num, dest_port, msg, ack_num=0, timestamp=time()):
        '''
        Method to format an l4 packet and header
        TODO
        '''
        if type(pkt_num) != bytes:
            pkt_num = struct.pack("I", pkt_num)
        if type(dest_port) != bytes:
            dest_port = struct.pack("H", dest_port)
        if type(timestamp) != bytes:
            timestamp = struct.pack("d", timestamp)
        if type(msg) != bytes:
            msg = msg.encode("utf-8")
        if type(ack_num) != bytes:
            ack_num = struct.pack("I", ack_num)
        length = self.l4_header + len(msg)

        return pkt_num + self.l4_port + dest_port + struct.pack("I", length) + timestamp + ack_num + msg
 
    def send_ack(self, pktno, dest_port, time_stamp):
        '''
        Method to send an acknoledgement with the specified packet number to the specified destination
        :param pktno: bytes for packet number that ack is for
        :param dest: bytes for the destination pc address
        :param time_stamp: bytes for the message time stamp
        '''
        # use wifi to send acks
        self.down_queue.put(self.make_l4_pkt(pkt_num=1, dest_port=dest_port, msg=time_stamp, ack_num=pktno), True) 

    def recv_ack(self, pktno, time_sent):
        '''
        Method to signal that a packet has been ack'd 
        :param pktno: int for the packet number that has been acked
        :param time_sent: float for the packet time sent
        '''
        if pktno == self.unacked_packet:
            globals()["l4_ack"].set()
            self.n_ack += 1

    def send_msg(self, msg, dest_port=0):
        '''
        Method to send message to specified port (Application interface with L4)
        TODO
        '''
        self.dest_port = dest_port
        self.prev_down_queue.put(msg, True)
    
    def recv_msg(self):
        '''
        Method to receive message (Application interface with L4)
        TODO
        '''
        return self.up_queue.get(True)


    def pass_up(self, stop):
        '''
        Method to check if the l4 address is this node then either pass to the app layer, or relay message
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l4_packet = self.prev_up_queue.get(True)
                
            self.n_recv = self.n_recv + len(l4_packet)

            if self.debug:
                print('l4', l4_packet)
            
            ack_num = struct.unpack("I", l4_packet[20:24])[0]
            if ack_num !=0:
                self.recv_ack(ack_num, struct.unpack("d", l4_packet[12:20])[0])
            else:
                self.up_queue.put(l4_packet[self.l4_header:], True)
                self.send_ack(l4_packet[0:4], l4_packet[4:6], l4_packet[12:20])  # send l4 ack
                l4_packet = b''


    def pass_down(self, stop):
        '''
        Method to receive l4 packets, break them into l2 sized packets, and pass them to l3
        :param stop: function returning true/false to stop the thread
        '''
        l4_pktno=0
        while not stop():
            act_rt=0 # retransmission counter
            msg = self.prev_down_queue.get(True)
            self.n_sent = self.n_sent + len(msg)      # record number of bytes
            
            for ii in range(len(msg)%self.chunk_size):  # pad message so it is n*chunk_size
                msg = msg + ' '

            try:
                self.unacked_packet = l4_pktno
            except:
                pass
                       
            l4_down_access.acquire()
            # pass l2 packets down to l3
            self.down_queue.put(self.make_l4_pkt(pkt_num=l4_pktno, dest_port=self.dest_port, msg=msg), True)   
            l4_pktno +=1
            l4_down_access.release()
            
            while not stop():
                globals()["l4_ack"].wait(self.timeout)
                if globals()["l4_ack"].isSet(): # ack received
                    globals()["l4_ack"].clear()
                    # TODO measurements
                    break

                elif act_rt < self.n_retrans:       # check num of retransmissions
                    act_rt += 1 
                    l4_down_access.acquire() 
                    self.down_queue.put(self.make_l4_pkt(pkt_num=l4_pktno, dest_port=self.dest_port, msg=msg), True)
                    l4_down_access.release()

                else:
                    if self.debug:
                        print("FATAL ERROR: L4 retransmit limit reached for pktno ", self.unacked_packet)
                    try:
                        globals()["l4_ack"].set()
                    except:
                        pass
                    break

