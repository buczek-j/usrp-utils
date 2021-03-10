#!/usr/bin/env python3

'''
Emane experiment node object
'''
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM
from subprocess import Popen, PIPE, DEVNULL
from psutil import Process
from time import sleep

from Utils.Simple_Node import Simple_Node
from Utils.Node_Config import Node_Config
from BasicArducopter import BasicArdu, Frames

def kill(proc_pid):
    '''
    Method to kill off a subprocess object 
    :param proc_pid: pid of process to kill
    '''
    process = Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

class UAV_Node(Simple_Node):
    def __init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False, control_port=9000, controller_address='192.168.10.2', controller_feedback_port=9001):
        '''
        Emane Node class for network stack
        :param my_config: Node_Config class object
        :param l1_debug: bool for layer 1 debug outputs
        :param l2_debug: bool for layer 2 debug outputs
        :param l3_debug: bool for layer 3 debug outputs
        :param l4_debug: bool for layer 4 debug outputs
        #TODO
        '''
        self.test_index = None
        self.test_loc = None

        self.control_socket = socket(AF_INET, SOCK_DGRAM)
        self.controller_address = (controller_address, controller_feedback_port)
        self.control_socket.bind((self.my_config.pc_ip, control_port))
        self.control_cmd = None

        self.feedback_socket = socket(AF_INET, SOCK_DGRAM)

        self.my_drone = BasicArdu(rame=Frames.NED, connection_string='/dev/ttyACM0', global_home=[42.47777625687639,-71.19357940183706,174.0])

        Simple_Node.__init__(self, my_config=my_config, l1_debug=l1_debug, l2_debug=l2_debug, l3_debug=l3_debug, l4_debug=l4_debug)  
    
    def parse_cmd(self, cmd):
        '''
        Method to parse the input test configuration 
        :param cmd: string for the test configuration
        '''

    def command_thread(self, stop):
        '''

        '''
        while not stop():
            data, addr = self.control_socket.recvfrom(1024)
            if data:
                self.control_cmd = data

    def reset_l1(self):
        '''
        Method to close the L1 usrp gnuradio block so that it can be reset with the new
        '''
        kill(self.subproccesses["USRP"].pid)
        sleep(1)
        self.subproccesses['USRP'] = Popen('python3 LayerStack/L1_protocols/TRX_ODFM_USRP.py '+str(self.my_config.get_tranceiver_args()), stdout=PIPE, stderr=PIPE, shell=True)
        sleep(10)

        


wifi_ip_list = ['192.168.10.101', '192.168.10.102', '192.168.10.103', '192.168.10.104', '192.168.10.105', '192.168.10.106']
username_list = ['wines-nuc1', 'wines-nuc2', 'wines-nuc3', 'wines-nuc4', 'wines-nuc5', 'wines-nuc6']
pwrd_list = ['wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl']
def main():
    '''
    '''
    id_list = ['dest1','rly1', 'src1', 'dest2', 'rly2', 'src2'] 
    role_list = ['rx', 'rly','tx', 'rx', 'rly', 'tx']
    usrp_ip_list = ['192.170.10.101', '192.170.10.102', '192.170.10.103', '192.170.10.104', '192.170.10.105', '192.170.10.106']
    tx_freq = [2.7e9, 2.5e9, 2.7e9]     # TODO
    rx_freq = [2.5e9, 2.7e9, 2.5e9]

    nodes = {}
    for ii in range(len(id_list)):
        nodes[id_list[ii]] = Node_Config(
            pc_ip=wifi_ip_list[ii],
            usrp_ip=usrp_ip_list[ii],
            my_id=id_list[ii],
            role=role_list[ii],
            rx_freq=rx_freq[ii],
            tx_freq=tx_freq[ii]
        )

    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
    parser.add_argument('--l1', type=str, default='n', help='layer 1 debug (y/n)')
    parser.add_argument('--l2', type=str, default='n', help='layer 2 debug (y/n)')
    parser.add_argument('--l3', type=str, default='n', help='layer 3 debug (y/n)')
    parser.add_argument('--l4', type=str, default='n', help='layer 4 debug (y/n)')
    options = parser.parse_args()

    # Configure hops for route 1
    nodes['dest1'].configure_hops(nodes['src1'], nodes['dest1'], None, nodes['rly1'])
    nodes['rly1'].configure_hops(nodes['src1'], nodes['dest1'], nodes['dest1'], nodes['src1'])
    nodes['src1'].configure_hops(nodes['src1'], nodes['dest1'], nodes['rly1'], None)

    # Configure hops for route 2
    nodes['dest2'].configure_hops(nodes['src2'], nodes['dest2'], None, nodes['rly2'])
    nodes['rly2'].configure_hops(nodes['src2'], nodes['dest2'], nodes['dest2'], nodes['src2'])
    nodes['src2'].configure_hops(nodes['src2'], nodes['dest2'], nodes['rly2'], None)

    
    uav_node = UAV_Node(nodes[id_list[int(options.index)]], l1_debug=(options.l1=='y' or options.l1 == 'Y'), l2_debug=(options.l2=='y' or options.l2 == 'Y'), l3_debug=(options.l3=='y' or options.l3 == 'Y'), l4_debug=(options.l4=='y' or options.l4 == 'Y'))
    try:
        uav_node.run()
    except:
        uav_node.close_threads()
        exit(0)
