#!/usr/bin/env python3

'''
Layer 4 object: Transport layer
'''

from LayerStack.Network_Layer import Network_Layer
from threading import  Event, Lock, Thread
from time import time
import struct, csv, os, datetime

l4_down_access = Lock()     

# latency
# l2_retrans = 4
# l2_timeout = 0.05
# l4_retrans = 0
# l4_timeout = 1.0 # 2*(1+l2_retrans)*num_hops*l2_timeout

# new
# l2_retrans = 4
# l2_timeout = 0.05
# l4_retrans = 0
# l4_timeout = 0.1 # 2*l2_timeout

# Throughput
# l2_retrans = 0
# l2_timeout = 0.01
# l4_retrans = 0
# l4_timeout = 0.02 # num_hops*l2_timeout
# l4_window=2
# l2_window=1

class Layer4(Network_Layer):
    def __init__(self, my_config, send_ack, window=1, num_frames=1, l2_header=42, l2_size=200, timeout=1.0, n_retrans=0, debug=False, l4_header=56, l4_log_base_name="~/Documents/usrp-utils/Logs/l4_acks_",  log=True):
        '''
        Layer 4 Transport layer object
        :param my_config: Node_Config object for the current node
        :param send_ack: function to call to send an acknowledgement
        :param num_frames: int for the number of l2 frames in one l4 packet
        :param l2_header: int for the byte length of the l2 header
        :param l2_size: int for the byte length for one l2 frame
        :param timeout: int for the l4 ack timeout
        :param n_retrans: int for the number of times to retransmit a l4 message
        :param debug: bool for debug outputs or not
        :param l4_header: int for the l4 packet header length
        :param l4_log_base_name: string for the file location and name to save l4 log files
        :param log: bool to log or not
        TODO
        '''
        Network_Layer.__init__(self, "layer_4", debug=debug, window=window)
        self.my_pc = bytes(my_config.pc_ip, "utf-8")

        # Setup Log File
        self.log = log
        if self.log:
            self.l4_csv_name = l4_log_base_name + datetime.datetime.now().strftime("___%m-%d-%y___%H-%M")+".csv"
            if my_config.role == 'rly' or my_config.role == 'rx':
                row_list = ["Pkt no", "Source ", "Destination", "Timestamp", "Time Received"]
            else:
                row_list = ["Ack Number", "Time Sent", "Time RCVD", "RTT", "Throughput"]
            self.file = open(os.path.expanduser(self.l4_csv_name), 'a', newline='')
            self.writer = csv.writer(self.file)
            self.writer.writerow(row_list)
  
        self.send_ack_wifi = send_ack

        self.unacked_packets = []
        self.window_ack_list = []
        for ii in range(window):
            self.unacked_packets.append(None)
            self.window_ack_list.append(False)
                
        self.num_frames = num_frames
        self.chunk_size = l2_size - l2_header
        self.timeout=timeout
        self.n_retrans = n_retrans
        
        self.ack_list = []
        
        self.l4_size = l2_size*num_frames
        self.l4_header = l4_header

        # Measurements
        self.n_recv = 0
        self.n_sent = 0
        self.n_ack = 0  # number of acks recvd

    def send_ack(self, pktno, dest, time_stamp):
        '''
        Method to send an acknoledgement with the specified packet number to the specified destination
        :param pktno: bytes for packet number that ack is for
        :param dest: bytes for the destination pc address
        :param time_stamp: bytes for the message time stamp
        '''
        # use wifi to send acks
        self.send_ack_wifi(pktno, dest, time_stamp)

    def recv_ack(self, pktno, time_sent):
        '''
        Method to signal that a packet has been ack'd 
        :param pktno: int for the packet number that has been acked
        :param time_sent: float for the packet time sent
        TODO 
        '''
        if not pktno in self.ack_list:
            self.ack_list.append(pktno)
            self.n_ack += 1
            ack_time = time()
            rtt = ack_time - time_sent 

            if self.debug:
                print("L4 ACK:", pktno, rtt)
            
            if self.log == True:
                
                self.writer.writerow([pktno, time_sent, ack_time, rtt, 8.0*self.l4_size/rtt])

        if pktno in self.unacked_packets:
            self.window_ack_list[self.unacked_packets.index(pktno)]=True
            self.unacked_packets[self.unacked_packets.index(pktno)]=None
    
    def log_pkt(self, l4_packet):
        '''
        Method to log l4 packets in a seperate thread
        :param pkt: l4 packet to log
        '''
        try:
            if self.log == True and not self.file.closed:
                    packet_source = self.unpad(l4_packet[8:28])
                    packet_destination = self.unpad(l4_packet[28:48])
                    pktno = struct.unpack('L', l4_packet[0:8])[0]
                    time_sent = struct.unpack('d', l4_packet[48:56])[0]
                    self.writer.writerow([pktno, packet_source, packet_destination, time_sent, time()])
        except:
            pass

    def pass_up(self, stop):
        '''
        Method to check if the l4 address is this node then either pass to the app layer, or relay message
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            l4_packet = self.prev_up_queue.get(True)
                
            packet_source = self.unpad(l4_packet[8:28])
            packet_destination = self.unpad(l4_packet[28:48])
            
            if self.debug:
                print('L4 RCV', struct.unpack('L', l4_packet[0:8]))

            if packet_destination == self.my_pc:    # if this is the destination, then pass payload to the application layer
                self.up_queue.put(l4_packet[56:], True)
                a = Thread(target=self.send_ack_wifi, args=(l4_packet[:8], packet_source, l4_packet[48:56],))
                a.start()
                l4_packet = b''

            else:   # relay/forward message
                self.prev_down_queue.put(l4_packet, True)
                l4_packet = b''

            # log the pkt
            b = Thread(target=self.log_pkt, args=(l4_packet,))
            b.start()

    def pass_down(self, stop, window_index=0):
        '''
        Method to receive l4 packets, break them into l2 sized packets, and pass them to l3
        :param stop: function returning true/false to stop the thread
        TODO
        '''
        
        while not stop():
            act_rt=0 # retransmission counter
            l4_packet = self.prev_down_queue.get(True)
            packet_source = self.unpad(l4_packet[8:28])
            
            if self.debug:
                print('L4 Sent', struct.unpack('L', l4_packet[0:8])[0])

            self.unacked_packets[window_index] = struct.unpack('L', l4_packet[0:8])[0]

            pkt_no_mac = 1  # mac (l2) packet number counter
            l4_down_access.acquire()
            # pass l2 packets down to l3
            while pkt_no_mac <= self.num_frames:
                chunk = l4_packet[(pkt_no_mac-1)*self.chunk_size : min((pkt_no_mac)*self.chunk_size,len(l4_packet)) ]
                l2_packet = struct.pack('H', pkt_no_mac & 0xffff ) + l4_packet[8:28] + l4_packet[28:48] + chunk  # packet source not needed, it gets replaced in l3, similarly, in l3 the dest is replaced by the mac address
                self.down_queue.put(l2_packet, True)    

                pkt_no_mac +=1
                l2_packet=b''
            l4_down_access.release()
            
            # if l4 packet originated from this node, then wait for ack
            if packet_source == self.my_pc:
                while not stop():
                    if self.window_ack_list[window_index]==True: # ack received
                        # TODO measurements
                        break

                    else:
                        if act_rt < self.n_retrans:       # check num of retransmissions
                            act_rt += 1 
                            
                            pkt_no_mac = 1  # mac (l2) packet number counter
                            l4_down_access.acquire()
                            # repeated transmission block 
                            while pkt_no_mac <= self.num_frames:
                                chunk = l4_packet[(pkt_no_mac-1)*self.chunk_size : min((pkt_no_mac)*self.chunk_size,len(l4_packet)) ]
                                l2_packet = struct.pack('h', pkt_no_mac & 0xffff) + l4_packet[8:28] + l4_packet[28:48] + chunk  # packet source not needed, it gets replaced in l3, similarly, in l3 the dest is replaced by the mac address
                                self.down_queue.put(l2_packet, True)    # TODO check that a full l2 packet is made and pad otherwise

                                pkt_no_mac +=1
                                l2_packet=b''
                            l4_down_access.release()

                        else:
                            if self.debug:
                                print("FATAL ERROR: L4 retransmit limit reached for pktno ", self.unacked_packets[window_index])
                            try:
                                globals()["l4_ack"].set()
                            except:
                                pass
                            break

