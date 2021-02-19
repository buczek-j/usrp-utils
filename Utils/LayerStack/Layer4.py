#!/usr/bin/env python3

'''
Layer 4 object: Transport layer
'''

from LayerStack.Network_Layer import Network_Layer
from threading import  Event, Lock
import struct

l4_ack = Event()
l4_down_access = Lock()     

class Layer4(Network_Layer):
    def __init__(self, my_config,
                send_ack,
                num_frames=5,
                num_blocks=2,
                l2_header=28,
                l2_block_size=128,
                timeout=1,
                n_retrans=3,
                debug=False
                ):
        '''
        Layer 4 Transport layer object
        :param : TODO
        '''
        Network_Layer.__init__(self, "layer_4", debug=debug)
        self.my_pc = bytes(my_config.pc_ip, "utf-8")
  
        self.send_ack_wifi = send_ack

        self.num_frames = num_frames
        self.chunk_size = l2_block_size*num_blocks - l2_header
        self.timeout=timeout
        self.n_retrans = n_retrans
        self.unacked_packet = 1

    def send_ack(self, pktno, dest):
        '''
        Method to send an acknoledgement with the specified packet number to the specified destination
        :param pktno: bytes for packet number that ack is for
        :param dest: bytes for the destination pc address
        '''
        # use wifi to send acks
        self.send_ack_wifi(pktno, dest, self.my_pc)

    def recv_ack(self, pktno):
        '''
        Method to signal that a packet has been ack'd 
        :param pktno: int for the packet number that has been acked
        '''
        if pktno == self.unacked_packet:
            globals()["l4_ack"].set()

    def pass_up(self, stop):
        '''
        Method to check if the l4 address is this node then either pass to the app layer, or relay message
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l4_packet = self.prev_up_queue.get(True)
            if self.debug:
                print('from l3',l4_packet)
                
            packet_source = l4_packet[8:21] 
            packet_destination = l4_packet[21:34]
            (timestamp,) = struct.unpack('d', l4_packet[34:42])
            (pktno_l4,) = struct.unpack('l', l4_packet[:8])	

            if packet_destination == self.my_pc:    # if this is the destination, then pass payload to the application layer
                self.up_queue.put(l4_packet[42:])
                self.send_ack(pktno_l4, packet_source)  # send l4 ack

            else:   # relay/forward message
                self.prev_up_queue.put(l4_packet, True)


    def pass_down(self, stop):
        '''
        Method to receive l4 packets, break them into l2 sized packets, and pass them to l3
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            act_rt=0 # retransmission counter
            l4_packet = self.prev_down_queue.get(True)
            packet_source = l4_packet[8:21]
            packet_destination = l4_packet[21:34]
            try:
                self.unacked_packet = struct.unpack('h', l4_packet[0:8])
            except:
                pass

            pkt_no_mac = 1  # mac (l2) packet number counter
            l4_down_access.acquire()
            # pass l2 packets down to l3
            while pkt_no_mac <= self.num_frames:
                chunk = l4_packet[(pkt_no_mac-1)*self.chunk_size : min((pkt_no_mac)*self.chunk_size,len(l4_packet)) ]
                l2_packet = struct.pack('h', pkt_no_mac & 0xffff) + packet_source + packet_destination + chunk  # packet source not needed, it gets replaced in l3, similarly, in l3 the dest is replaced by the mac address
                self.down_queue.put(l2_packet, True)    # TODO check that a full l2 packet is made and pad otherwise

                pkt_no_mac +=1
                l2_packet=''
            l4_down_access.release()
            
            

            # if l4 packet originated from this node, then wait for ack
            if packet_source == self.my_pc:
                while not stop():
                    globals()["l4_ack"].wait(self.timeout)
                    if globals()["l4_ack"].isSet(): # ack received
                        globals()["l4_ack"].clear()
                        # TODO measurements
                        break

                    elif act_rt < self.n_retrans:       # check num of retransmissions
                        act_rt += 1 

                        pkt_no_mac = 1  # mac (l2) packet number counter
                        l4_down_access.acquire()
                        # repeated transmission block 
                        while pkt_no_mac <= self.num_frames:
                            chunk = l4_packet[(pkt_no_mac-1)*self.chunk_size : min((pkt_no_mac)*self.chunk_size,len(l4_packet)) ]
                            l2_packet = struct.pack('h', pkt_no_mac & 0xffff) + packet_source + packet_destination + chunk  
                            self.down_queue.put(l2_packet, True)    

                            pkt_no_mac +=1
                            l2_packet=''
                        l4_down_access.release()

                    else:
                        print("FATAL ERROR: L4 retransmit limit reached for pktno ", self.unacked_packet)
                        try:
                            globals()["l4_ack"].set()
                        except:
                            pass
                        break

            




