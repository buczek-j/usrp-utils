#!/usr/bin/env python3

'''
Layer 2 object: Mac address layer 
'''

from Network_Layer import Network_Layer
from threading import Thread, Event, Timer
import socket, time, struct

class Layer2(Network_Layer):
    def __init__(self,
                my_config,
                src_config,
                dest_config,
                nh_config,
                ph_config,
                window='',
                sock_send = '',
                size_block=128,
                l2_header_len=10,
                num_blocks=2,
                num_frames=1,
                phy='NARROWBAND',
                print_debug=1,
                timeout=0.01,
                l2_th_coeff=0.75,
                l2_retransmission_threshold = 0,
                header_len = 10,
                signalling_discovery = int(10)
                ):
        '''
        Layer 2 network layer object
        :param my_config: Node_Config object for the current node
        :param src_config: Node_Config object for the source node
        :param dest_config: Node_COnfig object for the destination node
        :param nh_config: Node_Config object for the nehxt hop node
        :param ph_config: Node_Config object for the previous hop node
        :param window: integer for the l2 window
        :param sock_send: udp socket to send acks 
        :param:     TODO
        '''  
        Network_Layer.__init__(self, "layer_2", window)

        self.my_config = my_config
        self.src_config = src_config
        self.dest_config = dest_config
        self.nh_config = nh_config
        self.ph_config = ph_config

        self.udp_send_port = self.my_config.send_port
        self.udp_listen_port = self.my_config.listen_port
        
        self.packet_size = size_block*num_blocks
        self.block_size = size_block
        self.print_debug = print_debug
        
        self.timeout = timeout
        self.th_coeff = l2_th_coeff
        self.retransmit_thresh = l2_retransmission_threshold
        self.packet_count = 0
        self.acks = 0
        self.sent = 0
        self.num_frames = num_frames  #number of l2 packet that compose an upper layer packet
        self.num_blocks = num_blocks
        self.header_length = header_len
        self.chunk_size = self.packet_size - self.header_length
        self.signalling_discovery = signalling_discovery

        # ack sending socket ONLY IF THE NODE RECEIVES
        if self.my_config.role == 'tx' or self.my_config.role =='relay' or self.my_config.role =='rx': # LO 11/30
            self.send_previous_hop_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # transmission block ONLY IF THE NODE TRANSMITS
        if self.my_config.role == 'tx' or self.my_config.role =='relay' or self.my_config.role =='rx': # LO 11/30
            if phy == 'NARROWBAND':
                pass

            elif phy == 'OFDM':	
                pass

        self.sock_send = sock_send

        self.waiting_ack_mac_pktno = None
        
        if self.my_config.role == 'tx' or self.my_config.role == 'relay' or self.my_config.role == 'rx': 
            pass
		
        self.transmitted_packets 				= 1
        self.successfully_transmitted_packets 	= 1
        
        self.last = time.time()
        self.A = 0	

        # added by hai, used to calculate l2 rate
        self.t0 = 0
        self.data_write_flag = 0
        
        # build the dictionaries for pass_up	
        self.up_packet = {}
        self.pktno_mac_old = {}
        self.packet_beginning_flag = {}		

        for source in [self.my_config.usrp_ip, self.src_config.usrp_ip, self.dest_config.usrp_ip, self.nh_config.usrp_ip, self.ph_config.usrp_ip]:
            self.up_packet[source] = b''
            self.pktno_mac_old[source] = 0
            self.packet_beginning_flag[source] = 0

    def send_cc_message(self,packet,number,ip,port):
        '''
        Method to send channel coding update
        '''
        packet = struct.pack('h', -2) + packet
        try:
            self.sock_send.sendto(packet, (ip, port))
        except socket.error as exc:
            pass	

    def send_l2_feedback(self,packet,number,ip,port):
        '''
        Method to hanlde sending l2 ack messages
        :param packet: packet to send
        :param number: ?
        :param ip: string for ip address to send to 
        :param port: int for port to send to
        '''
        packet = struct.pack('h', 2) + packet
        try:
            self.sock_send.sendto(packet, (ip, port))
        except socket.error as exc:
            print('unable to send feedback')
            pass
    
    def received_ack(self,mac_ack):	
        '''
        Method to handle receiving l2 ack messages
        :param mack_ack: ack message
        '''	
        t_ack = time.time()

        (mac_ack_pktno,) = struct.unpack('h', mac_ack[0:2])
        mac_source_ip =  socket.inet_ntoa( mac_ack[2:6]	)#13	

        if mac_ack_pktno == self.waiting_ack_mac_pktno and mac_source_ip == self.my_config.usrp_ip: 
            globals()["ack_l2_received"].set() 
            # inclease n_ack received
            self.acks += 1

        elif mac_ack_pktno == -1 :
            print('L2 CONTROL ACK ')
            globals()["ack_l2_received_control"].set() 

        else:
            print("UNKNOWN/WRONG L2 ACK!!!")
        

    def new_send_pkt(self, payload, ip, port):
        '''
        Method to send a udp new packet
        :param payload: message to send
        :param ip: ip address to send to 
        :param port: int for port to send to 
        '''
        sock_send = socket.socket(socket.AF_INET, 	# Internet
                                        socket.SOCK_DGRAM) 			# UDP
        return sock_send.sendto(payload, (ip, port))

    def new_start_l1_receiving_block(self, stop):
        '''
        Method to handle the l1 receiving thread
        :param stop: function returning true/false to stop the thread
        '''
        self.data_UDP_IP_LISTEN = self.my_config.usrp_ip
        self.data_UDP_PORT_LISTEN = 10000
        self.data_sock_listen = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP

        self.data_sock_listen.bind((self.data_UDP_IP_LISTEN, self.data_UDP_PORT_LISTEN))	

        print(('DATA LISTEN SCKT started at ', self.data_UDP_IP_LISTEN,' ',self.data_UDP_PORT_LISTEN))
        while not stop() :# thread termination condition
            received_pkt, _ = self.data_sock_listen.recvfrom(1024) # buffer size is 1024 bytes

            self.up_queue.put(received_pkt,True)
        print("\n new_start_l1_receiving_block TERMINATE\n")

    def find_ack_address(self, mac_source_ip):
        '''
        Method to return the correct pc ip address and udp listening port for the input usrp ip address
        :param ip_usrp: string for the usrp ip address
        :return: string pc ip, int pc port number
        '''
        if mac_source_ip == self.src_config.usrp_ip:
            pc_ip = self.src_config.pc_ip
            port = self.src_config.listen_port
        elif mac_source_ip == self.dest_config.usrp_ip:
            pc_ip = self.dest_config.pc_ip
            port = self.dest_config.listen_port
        elif mac_source_ip == self.nh_config.usrp_ip:
            pc_ip = self.nh_config.pc_ip
            port = self.nh_config.listen_port
        elif mac_source_ip == self.ph_config.usrp_ip:
            pc_ip = self.ph_config.pc_ip
            port = self.ph_config.listen_port
        return pc_ip, port
        
    # it builds a l4 packet and passes it up in the l4 queue when  complete	
    def pass_up(self, stop):
        '''
        Method to pass data up the stack to the next layer
        :param stop: function returning True/False for if the pass up thread should stop
        '''
        pktno_mac = 0
        
        # pop packets until the last mac number: assuming none is lost and they are sequential
        
        while not stop():
            mac_packet = self.up_queue.get(True)
            (pktno_mac,) = struct.unpack('h', mac_packet[0:2])	
            mac_source_ip =  socket.inet_ntoa(mac_packet[2:6])
            mac_destination_ip =  socket.inet_ntoa( mac_packet[6:10])

            if len(mac_packet) != self.packet_size:
                continue
            
            # If L2 dest is correct
            if mac_destination_ip == self.my_config.usrp_ip : #13
                # Frame 0 of a new pkt
                if pktno_mac == 1 :
                    # this constitutes the l2 ack packet to be sent
                    feedback_mac = mac_packet[0:10]		 #13
                    self.pktno_mac_old[mac_source_ip] = pktno_mac
                    
                    # Add the payload to L4 packet
                    self.up_packet[mac_source_ip] += mac_packet[10:] #13 
                    mac_packet = b''

                    # Send L2 ack
                    if (self.my_config.role == 'rx' or self.my_config.role =='relay') :
                        pc_ip, port = self.find_ack_address(mac_source_ip)
                        self.send_l2_feedback(feedback_mac,pktno_mac,pc_ip, port)

                    if pktno_mac == self.num_frames :
                        break	

                # FRAME CONTIGUOUS TO THE PREVIOUS
                elif pktno_mac == (self.pktno_mac_old[mac_source_ip] + 1) % (self.num_frames +1): 
                    feedback_mac = mac_packet[0:10]		#13
                    
                    mac_source_ip =  socket.inet_ntoa(mac_packet[2:6])
                    mac_destination_ip =  socket.inet_ntoa( mac_packet[6:10])		
                    
                    self.pktno_mac_old[mac_source_ip] = pktno_mac
                    # add the payload to l4 packet
                    self.up_packet[mac_source_ip] += mac_packet[10:] # 13 BYTES IP
                    mac_packet = b''
                    
                    # send l2 ack
                    if (self.my_config.role == 'rx' or self.my_config.role =='relay') :
                        pc_ip, port = self.find_ack_address(mac_source_ip)
                        self.send_l2_feedback(feedback_mac,pktno_mac,pc_ip, port)

                    if pktno_mac == self.num_frames :
                        break		

                # CONTROL MESSAGE RECEIVED
                elif pktno_mac == -1: 
                    # send l2 ack
                    if (self.my_config.role == 'rx' or self.my_config.role =='relay') :
                        pc_ip, port = self.find_ack_address(mac_source_ip)
                        self.send_l2_feedback(feedback_mac,pktno_mac,pc_ip, port)
                    continue

                # Out of order frame for that source
                else: 
                    if (self.my_config.role == 'rx' or self.my_config.role =='relay'):
                        feedback_mac = mac_packet[0:10]#13
                    continue 
            else:
                 pass	

        # reset completed packet 
        pass_up_packet = self.up_packet[mac_source_ip]
        self.up_packet[mac_source_ip] = b''
        self.pktno_mac_old[mac_source_ip] = 0
        self.packet_beginning_flag[mac_source_ip] = 0
        
        return pass_up_packet,1 

    def pass_down(self, down_packet, index, stop): 
        '''
        Method to pass data down the stack to the next layer
        :param down_packet: packet of information to pass
        :param index: ?
        :param stop: function returning True/False for if the pass up thread should stop
        '''        
        if self.data_write_flag == 0:
            self.t0 = time.time()
            self.data_write_flag = 1

        act_rt = 0
        (pktno_mac,) = struct.unpack('h', down_packet[0:2])
        mac_destination_ip = socket.inet_ntoa(down_packet[6:10])
        
        if self.my_config.role == 'tx' or self.my_config.role =='relay' or self.my_config.role =='rx':   	
            self.waiting_ack_mac_pktno = pktno_mac # the ack received must be for this pktno_mac
            self.new_send_pkt(down_packet, mac_destination_ip, 10000)
            
            # increase packets sent
            self.sent += 1
            self.transmitted_packets = self.transmitted_packets + 1 # counter for transmission operated
            
            while not stop():	
                if self.transmitted_packets % 100 == 0:
                    self.transmitted_packets = 1
                    self.successfully_transmitted_packets = 1	

                globals()["ack_l2_received"].wait(self.timeout) 
                if globals()["ack_l2_received"].isSet():
                    globals()["ack_l2_received"].clear()

                    # throughput estimation 
                    if self.packet_count < 10:
                        self.packet_count = self.packet_count + 1
                    else:
                        self.t1 = time.time()
                        delta_t = self.t1 - self.last
                        if delta_t == 0:
                            a = 0
                        else:
                            #a = 1/delta_t
                            a = self.packet_count/delta_t
                    
                        self.A = self.A*self.th_coeff + (1-self.th_coeff)*a                     
                        netcfg.lnk_thpt = self.A
                        self.last = self.t1						
                        self.packet_count = 0
                    
                    self.successfully_transmitted_packets = self.successfully_transmitted_packets + 1 # counter for acks received
                    break
                
                elif act_rt < self.retransmit_thresh:
                    act_rt += 1
                    self.new_send_pkt(down_packet, mac_destination_ip, 10000)
                    
                    # increase packets sent
                    self.sent += 1
                    self.transmitted_packets = self.transmitted_packets + 1 # counter for transmission operated
                    
                else:
                    # pop the remaining l4 packets from the queue and discard them
                    for ii in range(self.num_frames - (pktno_mac)):
                        self.down_queue.get()
                        print("popped packet")
                            
                    break  