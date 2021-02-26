#!/usr/bin/env python3

'''
Control Plane object: Runs alongside layer stack to receive l2 and l4 acks and cc commands
'''

from socket import socket, AF_INET, SOCK_DGRAM
from enum import Enum
import struct

class CP_Codes(Enum):
    L2_ACK=struct.pack('ss', b'-', b'2')        # layer 2 ack message
    L4_ACK=struct.pack('ss', b'-', b'4')        # layer 4 ack message
    CC_ACK=-3       # layer 2 code rate signalling ack
    CC_MESS=-2      # layer 2 code rate signalling message 
    GPS=-5          # gps signal received
    DISC=-10        # neighborhood discovery message
    ROUTE=-7        # signal the next hop of the session
    GEN = -3        # generic signalling message
    

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
    def __init__(self, ip, port_recv=55557, wifi_ip_pre=b'192.168.10.'):
        '''
        Object to send and recieve control plane messages (outside of layer stack)
        :param ip: string for the wifi ip address
        :param port_recv: int for the udp message listener port
        '''
        self.send_sock = socket(AF_INET, SOCK_DGRAM)
        self.recv_sock = socket(AF_INET, SOCK_DGRAM)
        print(ip, port_recv)
        self.recv_sock.bind((ip, port_recv))
        self.ip = ip
        self.port = port_recv
        self.wifi_ip_pre = wifi_ip_pre


    def listening_socket(self, l2_recv_ack, l4_recv_ack, stop):
        '''
        Method to listen to the control plane udp socket, parse data, and perform cooresponding actions
        :param l2_recv_ack: l2 method for a recived packet ack
        :param l4_recv_ack: l4 method for a recived packet ack
        :param stop: method returning true/false to stop the thread
        '''
        while not stop():
            packet, addr = self.recv_sock.recvfrom(1024)
            control_code = packet[0:2] 
            print(packet, control_code == CP_Codes.L2_ACK.value, control_code == CP_Codes.L4_ACK.value)
            packet = packet[2:]
            if control_code == CP_Codes.L2_ACK.value:
                (ack,) = struct.unpack('h', packet[0:2])
                l2_recv_ack(ack)

            elif control_code == CP_Codes.L4_ACK.value:
                (ack,)=struct.unpack('l', packet[0:8])
                l4_recv_ack(ack)
            

    def send_l2_ack(self, pktno, mac_ip):
        '''
        method to send l2 ack via wifi. Assumes that wifi and mac have the same postfix
        :param pktno: bytes for the packet number
        :param mac_ip: bytes for the destination mac ip
        '''
        pc_ip = self.wifi_ip_pre + get_post_ip(mac_ip)
        ack_msg = CP_Codes.L2_ACK.value + pktno
        self.send_sock.sendto(ack_msg, (pc_ip.decode('utf-8'), self.port))
        print('L2 ACK', pc_ip.decode('utf-8'), self.port, ack_msg)


    def send_l4_ack(self, pktno, pc_ip):
        '''
        method to send l4 ack via wifi
        :param pktno: bytes for the packet number
        :param pc_ip: bytes for the destination wifi ip
        '''
        ack_msg = CP_Codes.L4_ACK.value + pktno
        self.send_sock.sendto(ack_msg, (pc_ip.decode('utf-8'), self.port))
        print('L4 ACK', pc_ip.decode('utf-8'), self.port, ack_msg)


