#!/usr/bin/env python3

'''
Layer 2 object: Mac address layer (Datalink)

[L2 Pkt Num], [MAC Dest], [MAC Src], [ACK Num], [Payload]
[  2 bytes ], [6 bytes ], [6 bytes], [2 bytes], [0-X bytes]
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
    ACK = 0
    CNTRL = -3
    NEIGHBOR_DISCOVERY = -10

L2_Header_Len=16
L2_Num_Blocks=2
L2_Block_Size=128

class Layer2(Network_Layer):
    def __init__(self, mac_ip, num_frames=1, timeout=0.1, n_retrans=9, debug=False):
        '''
        Layer 2 network layer object
        :param mac_ip: string for the usrp mac address fo the current node
        :param send_ack: method to send udp acks via wifi
        :param udp_acks: bool to use udp acks via wifi
        :param num_frames: int for the number of l2 frames in one l4 packet
        :param timeout: float for the time in seconds to wait for a l2 packet ack
        :param n_retrans: int for the numbre of retranmission before packet tranmssion failure
        :param debug: bool for debug outputs or not
        '''  
        Network_Layer.__init__(self, "layer_2", debug=debug)

        
        self.mac_ip = b''
        for entry in mac_ip.split('.'):
            self.mac_ip = self.mac_ip + struct.pack('B', int(entry))

        self.timeout= timeout
        self.n_retrans = n_retrans 

        self.mac_pkt_dict = {}
        self.up_pkt = {}
        self.sent_pkt_dict = {}

        self.chunk_size = L2_Block_Size * L2_Num_Blocks - L2_Header_Len    
        

    def send_ack(self, pktno, dest):
        '''
        Method to send an acknoledgement with the specified packet number to the specified destination
        :param pktno: bytes for packet number that ack is for
        :param dest: bytes for the destination mac address
        '''
        pkt = struct.pack("H", L2_ENUMS.MSG.value) + dest + self.mac_ip + pktno
        for ii in range(self.chunk_size - (len(pkt[L2_Header_Len:])%self.chunk_size)):  # pad to next chunk size
                pkt = pkt+struct.pack('x')
        self.down_queue.put(pkt, True)
        print("ACK LEN",len(pkt))
        
    def recv_ack(self, pktno, addr):
        '''
        Method to signal that a packet has been ack'd (needed for usrp and wifi ack messages)
        :param pktno: int for the packet number that has been acked
        '''
        print(pktno == self.sent_pkt_dict[addr], pktno)
        if pktno == self.sent_pkt_dict[addr]:
            globals()["l2_ack"].set()
            print('L2 ACK', pktno)


    def parse_header(self, pkt):
        '''
        '''
        print("pktno: ",struct.unpack("H", pkt[0:2])[0], 
            "Dest: ",int(pkt[2]),int(pkt[3]),int(pkt[4]),int(pkt[5]),int(pkt[6]),int(pkt[7]),
            "SRC: " ,int(pkt[8]),int(pkt[9]),int(pkt[10]),int(pkt[11]),int(pkt[12]),int(pkt[13]),"ACK: ", struct.unpack("H", pkt[14:16])[0] )


    def pass_up(self, stop):
        '''
        Method to read pkt number, check if the destination is correct, and ensure packets are received correctly
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            mac_packet = self.prev_up_queue.get(True)

            # if self.debug:
            #     print('from l1', mac_packet)

            pktno_mac = struct.unpack('H', mac_packet[0:2])[0]
            mac_destination_ip=mac_packet[2:8]
            mac_source_ip=mac_packet[8:14]
            ack = struct.unpack('H', mac_packet[14:L2_Header_Len])[0]
            if self.debug:
                print("L2_up", "pknto", pktno_mac, "dest:", mac_destination_ip, "src:", mac_source_ip, "Ack:", ack)
                print("to me?", mac_destination_ip == self.mac_ip)
                print('My Ack?', ack, self.sent_pkt_dict[addr])

            if not (mac_source_ip in self.mac_pkt_dict.keys()):
                self.mac_pkt_dict[mac_source_ip] = L2_ENUMS.MSG.value
                self.sent_pkt_dict[mac_source_ip] = L2_ENUMS.ACK.value
                self.up_pkt[mac_source_ip] = b''

            # check if destination correct (meant for this node to read)
            if mac_destination_ip == self.mac_ip:
                
                if pktno_mac == L2_ENUMS.MSG.value or pktno_mac == (self.mac_pkt_dict[mac_source_ip]+1):
                    if ack != L2_ENUMS.ACK.value:   # check if ack message
                        self.recv_ack(ack, mac_source_ip)
                        continue
                    
                    else:
                        self.mac_pkt_dict[mac_source_ip] = pktno_mac        # update last received pkt number 
                        self.send_ack(mac_packet[0:2], mac_source_ip)  # send ack

                        if pktno_mac == L2_ENUMS.MSG.value: # if first pkt of meessage, start fresh
                            self.up_pkt[mac_source_ip] = mac_packet[L2_Header_Len:]
                        else:
                            self.up_pkt[mac_source_ip] += mac_packet[L2_Header_Len:]
                        mac_packet = b''

                        if len(self.up_pkt[mac_source_ip]) >= struct.unpack('I', self.up_pkt[mac_source_ip][2:6])[0]:    # if get expected size
                            self.up_queue.put(self.up_pkt[mac_source_ip][:(struct.unpack('I', self.up_pkt[mac_source_ip][2:6])[0])], True)
                            self.up_pkt[mac_source_ip] = b''
                            self.mac_pkt_dict[mac_source_ip] = L2_ENUMS.MSG.value
                            continue

                        else:
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

            pkno = 1
            for ii in range(self.chunk_size - (len(down_packet[L2_Header_Len:])%self.chunk_size)):  # pad to next chunk size
                down_packet = down_packet+struct.pack('x')
            print("PKT LEN", len(down_packet))

            # if self.debug:
            #     print("from l3", down_packet)

            while len(down_packet[(L2_Header_Len+(self.chunk_size*(pkno-1))):]) / (self.chunk_size)>0:   #while chunks left
                chunk = down_packet[(L2_Header_Len+(self.chunk_size*(pkno-1))):(L2_Header_Len+(self.chunk_size*(pkno)))]
                self.down_queue.put(down_packet[0:L2_Header_Len] + chunk, True)
                
                self.sent_pkt_dict[down_packet[2:8]]= pkno
                pkno += 1

                act_rt = 0  # retransmission counter
                while not stop():
                    globals()["l2_ack"].wait(self.timeout)
                    if globals()["l2_ack"].isSet():     # ack received
                        globals()["l2_ack"].clear()
                        break

                    elif act_rt < self.n_retrans:       # check num of retransmissions
                        act_rt += 1
                        self.down_queue.put(down_packet[0:L2_Header_Len] + chunk, True)

                    else:
                        if self.debug:
                            print("FATAL ERROR: L2 retransmit limit reached for pktno ", struct.unpack("H", down_packet[0:2])[0])
                        down_packet=b''

                        break
                        
