#!/usr/bin/env python3

'''
Control Plane object: Runs alongside layer stack to receive l2 and l4 acks and state commands
'''

from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
from enum import Enum
import struct

class CP_Codes(Enum):
    L2_ACK=struct.pack('ss', b'-', b'2')        # layer 2 ack message
    L4_ACK=struct.pack('ss', b'-', b'4')        # layer 4 ack message
 
    STATE=struct.pack('ss', b'-', b'3')         # application layer state message
    

def get_post_ip(ip):
    '''
    Method to get the final part of the ip
    :param ip: bytes of ip address
    :return: final bytes
    '''
    index=0
    for ii in range(4):
        if ip[len(ip)-(ii+1)] == 46:
            index = len(ip)-(ii)
            break
    return ip[index:]


class Control_Plane():
    def __init__(self, ip, port_recv=55557, wifi_ip_pre=b'192.168.10.', num_nodes=6):
        '''
        Object to send and recieve control plane messages (outside of layer stack)
        :param ip: string for the wifi ip address
        :param port_recv: int for the udp message listener port
        :param num_nodes: int for the number of nodes to wait for states from
        '''
        # Setup Sockets
        self.send_sock = socket(AF_INET, SOCK_DGRAM)

        self.recv_sock = socket(AF_INET, SOCK_DGRAM)
        self.recv_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.recv_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.broadcast_socket = socket(AF_INET, SOCK_DGRAM)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.broadcast_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        self.recv_sock.bind(('', port_recv))
        self.ip = ip
        self.port = port_recv
        self.wifi_ip_pre = wifi_ip_pre

    def broadcast_state(self, message):
        '''
        Method to broadcast message to all nodes
        :param message: string or convertable to string to broadcast
        '''
        self.broadcast_socket.sendto((CP_Codes.STATE.value + str(message).encode('utf-8')), ('255.255.255.255', self.port))

    def listening_socket(self, l2_recv_ack, l4_recv_ack, state_recv, stop):
        '''
        Method to listen to the control plane udp socket, parse data, and perform cooresponding actions
        :param l2_recv_ack: l2 method for a recived packet ack
        :param l4_recv_ack: l4 method for a recived packet ack
        :param state_recv: method to handle state messages
        :param stop: method returning true/false to stop the thread
        '''
        while not stop():
            packet, addr = self.recv_sock.recvfrom(1024)
            control_code = packet[0:2] 
            # print(packet, control_code == CP_Codes.STATE.value)
            packet = packet[2:]
            if control_code == CP_Codes.L2_ACK.value:
                (ack,) = struct.unpack('h', packet[0:2])
                l2_recv_ack(ack)

            elif control_code == CP_Codes.L4_ACK.value:
                (ack,)=struct.unpack('l', packet[0:8])
                (time_sent,) = struct.unpack('d', packet[8:16])
                l4_recv_ack(ack, time_sent)

            elif control_code == CP_Codes.STATE.value:
                # [node index #],[location index #],[power index #]
                msg = packet.decode('utf-8').split(',')
                # print('RCVD STATE:', int(msg[0]), int(msg[1]), int(msg[2]))
                state_recv(int(msg[0]), int(msg[1]), int(msg[2]))
                

    def send_l2_ack(self, pktno, mac_ip):
        '''
        method to send l2 ack via wifi. Assumes that wifi and mac have the same postfix
        :param pktno: bytes for the packet number
        :param mac_ip: bytes for the destination mac ip
        '''
        pc_ip = self.wifi_ip_pre + get_post_ip(mac_ip)
        ack_msg = CP_Codes.L2_ACK.value + pktno
        self.send_sock.sendto(ack_msg, (pc_ip.decode('utf-8'), self.port))
        # print('L2 ACK', pc_ip.decode('utf-8'), self.port, ack_msg)

    def send_l4_ack(self, pktno, pc_ip, time_sent):
        '''
        method to send l4 ack via wifi
        :param pktno: bytes for the packet number
        :param pc_ip: bytes for the destination wifi ip
        :param time_sent: bytes for the tagged time sent on the l4 packet originating from this node
        '''
        ack_msg = CP_Codes.L4_ACK.value + pktno + time_sent
        self.send_sock.sendto(ack_msg, (pc_ip.decode('utf-8'), self.port))


