#!/usr/bin/env python3

'''
Layer 2 object: Mac address layer (Datalink)
'''

from LayerStack.Network_Layer import Network_Layer
from enum import Enum 
from threading import  Event
from time import time
import struct

l2_ack = Event()
l2_control = Event()

class L2_ENUMS(Enum):
    MSG = 1
    ACK = -2
    CNTRL = -3
    NEIGHBOR_DISCOVERY = -10


class Layer2(Network_Layer):
    def __init__(self, mac_ip, send_ack=None, udp_acks=True, num_frames=1, timeout=0.025, n_retrans=5, debug=False):
        '''
        Layer 2 network layer object
        :param mac_ip: string for the usrp mac address fo the current node
        :param send_ack: method to send udp acks via wifi
        :param udp_acks: bool to use udp acks via wifi
        :param num_frames: int for the number of l2 frames in one l4 packet
        :param timeout: float for the time in seconds to wait for a l2 packet ack
        :param n_retrans: int for the numbre of retranmission before packet tranmssion failure
        :param ack_recv_port: int for the layer 2 udp ack port number
        :param ack_send_port: int for the layer 2 ack send port number 
        
        '''  
        Network_Layer.__init__(self, "layer_2", debug=debug)

        self.mac_ip = bytes(mac_ip, "utf-8")
        self.num_frames = num_frames
        self.timeout= timeout
        self.n_retrans = n_retrans 

        self.send_ack_wifi = send_ack
        self.udp_acks = udp_acks

        self.mac_pkt_dict = {}
        self.up_pkt = {}
        self.unacked_packet = 0

        self.throughput = 0
        self.time_sent = 0
        self.l2_size = 0
        self.rtt = 0

    def send_ack(self, pktno, dest):
        '''
        Method to send an acknoledgement with the specified packet number to the specified destination
        [ack_flag source_ip dest_ip ack_pkt_num]
        :param pktno: bytes for packet number that ack is for
        :param dest: bytes for the destination mac address
        '''
        if not self.udp_acks:   # use usrp for l2 acks
            pkt = struct.pack('h', L2_ENUMS.ACK.value) + self.pad(self.mac_ip) + self.pad(dest) + pktno
            self.down_queue.put(pkt, True)
        else:                   # use wifi to send acks
            self.send_ack_wifi(pktno, dest)
        
    def recv_ack(self, pktno):
        '''
        Method to signal that a packet has been ack'd (needed for usrp and wifi ack messages)
        :param pktno: int for the packet number that has been acked
        '''
        if pktno == self.unacked_packet:
            globals()["l2_ack"].set()
            self.rtt = time() - self.time_sent
            self.throughput = 0.5*self.throughput + 0.5*(self.l2_size * 8 / self.rtt)   # L4 throughput in bits per sec moving average
            
            if self.debug:
                print('L2 RTT:', self.rtt, '(s)', 'L2 Throughput: ', self.throughput, "(bits/sec)")

    def pass_up(self, stop):
        '''
        Method to read pkt number, check if the destination is correct, and ensure packets are received correctly
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            mac_packet = self.prev_up_queue.get(True)

            (pktno_mac,) = struct.unpack('h', mac_packet[0:2])	
            mac_destination_ip =   self.unpad(mac_packet[22:42]) 
            mac_source_ip =   self.unpad(mac_packet[2:22])

            if self.debug:
                print(pktno_mac, mac_source_ip, mac_destination_ip, mac_destination_ip == self.mac_ip)

            if not (mac_source_ip in self.mac_pkt_dict.keys()):
                self.mac_pkt_dict[mac_source_ip] = L2_ENUMS.MSG.value
                self.up_pkt[mac_source_ip] = b''

            # check if destination correct (meant for this node to read)
            if mac_destination_ip == self.mac_ip:
                if pktno_mac == L2_ENUMS.MSG.value:
                    self.mac_pkt_dict[mac_source_ip] = pktno_mac        # update last received pkt number 
                    self.send_ack(mac_packet[0:2], mac_source_ip)  # send ack
                    self.up_pkt[mac_source_ip] = mac_packet[42:]
                    mac_packet = b''

                    if pktno_mac == self.num_frames:    # if last packet in l4 frame
                        self.up_queue.put(self.up_pkt[mac_source_ip], True)
                        self.up_pkt[mac_source_ip] = b''
                        self.mac_pkt_dict[mac_source_ip] = L2_ENUMS.MSG.value
                        continue

                    else:
                        continue


                elif pktno_mac == (self.mac_pkt_dict[mac_source_ip]+1):  # next sequential message 
                    self.mac_pkt_dict[mac_source_ip] = pktno_mac        # update last received pkt number 
                    self.send_ack(mac_packet[0:2], mac_source_ip)  # send ack
                    self.up_pkt[mac_source_ip] += mac_packet[42:]
                    mac_packet = b''

                    if pktno_mac == self.num_frames:    # if last packet in l4 frame
                        self.up_queue.put(self.up_pkt[mac_source_ip], True)
                        self.up_pkt[mac_source_ip] = b''
                        self.mac_pkt_dict[mac_source_ip] = L2_ENUMS.MSG.value
                        continue

                    else:
                        continue

                elif pktno_mac == L2_ENUMS.ACK.value:
                    (mac_ack_pktno,) = struct.unpack('h', mac_packet[42:44])
                    self.recv_ack(mac_ack_pktno)
                    continue

                else:   # if unexpected packet number
                    # self.send_ack(struct.pack('h', self.mac_pkt_dict[mac_source_ip]), mac_source_ip)  # send last known pkt num
                    continue
            else:
                pass
        
            
                
    def pass_down(self, stop):
        '''
        Method to pass bytes in to L1 
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            down_packet = self.prev_down_queue.get(True)
            
            self.l2_size = len(down_packet)
            self.time_sent = time()

            if self.debug:
                print("from l3", down_packet)

            act_rt = 0  # retransmission counter

            (pktno_mac,) = struct.unpack('h', down_packet[0:2]) 

            self.down_queue.put(down_packet, True)
            self.unacked_packet = pktno_mac

            while not stop():
                globals()["l2_ack"].wait(self.timeout)
                if globals()["l2_ack"].isSet():     # ack received
                    globals()["l2_ack"].clear()
                    # TODO measurements
                    break

                elif act_rt < self.n_retrans:       # check num of retransmissions
                    act_rt += 1
                    self.down_queue.put(down_packet, True)
                    self.unacked_packet = pktno_mac

                else:
                    if self.debug:
                        print("FATAL ERROR: L2 retransmit limit reached for pktno ", self.unacked_packet)
                    for ii in range(self.num_frames-self.unacked_packet):
                        self.prev_down_queue.get(True)
                        if self.debug:
                            print("popped packet")

                    break
                        
