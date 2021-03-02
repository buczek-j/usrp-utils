#!/usr/bin/env python3

'''
Emane experiment node object
'''
from argparse import ArgumentParser

from Utils.Simple_Node import Simple_Node
from Utils.Node_Config import Node_Config

class Emane_Node(Simple_Node):
    def __init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False):
        '''
        Emane Node class for network stack
        :param my_config: Node_Config class object
        :param l1_debug: bool for layer 1 debug outputs
        :param l2_debug: bool for layer 2 debug outputs
        :param l3_debug: bool for layer 3 debug outputs
        :param l4_debug: bool for layer 4 debug outputs
        '''
        Simple_Node.__init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False)   

        #TODO add drone class


wifi_ip_list = ['192.168.10.101', '192.168.10.102', '192.168.10.103', '192.168.10.104', '192.168.10.105', '192.168.10.106']
username_list = ['wines-nuc1', 'wines-nuc2', 'wines-nuc3', 'wines-nuc4', 'wines-nuc5', 'wines-nuc6']
pwrd_list = ['wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl', 'wnesl']
def main():
    '''
    '''
    id_list = ['dest1','rly1', 'src1'] # TODO update list
    role_list = ['rx', 'rly','tx']
    udp_port_list = [9000, 9000, 9000]
    usrp_ports = [['55555','55556'], ['55555','55556'], ['55555','55556']]
    usrp_ip_list = ['192.170.10.2', '192.170.10.104', '192.170.10.102']
    tx_gain = [0.8, 0.8, 0.8]
    rx_gain = [0.6, 0.6, 0.6]
    tx_freq = [2.7e9, 2.5e9, 2.7e9]
    rx_freq = [2.5e9, 2.7e9, 2.5e9]
    tx_bw = [0.5e6, 0.5e6, 0.5e6]
    rx_bw = [0.5e6, 0.5e6, 0.5e6]

    nodes = {}
    for ii in range(len(id_list)):
        nodes[id_list[ii]] = Node_Config(
            pc_ip=wifi_ip_list[ii],
            usrp_ip=usrp_ip_list[ii],
            my_id=id_list[ii],
            role=role_list[ii],
            listen_port=udp_port_list[ii],
            usrp_ports=usrp_ports[ii],
            rx_bw=rx_bw[ii],
            rx_freq=rx_freq[ii],
            rx_gain=rx_gain[ii],
            tx_bw=tx_bw[ii],
            tx_freq=tx_freq[ii],
            tx_gain=tx_gain[ii],
            serial=serial_list[ii]
        )

    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
    parser.add_argument('--l1', type=str, default='n', help='layer 1 debug (y/n)')
    parser.add_argument('--l2', type=str, default='n', help='layer 2 debug (y/n)')
    parser.add_argument('--l3', type=str, default='n', help='layer 3 debug (y/n)')
    parser.add_argument('--l4', type=str, default='n', help='layer 4 debug (y/n)')
    options = parser.parse_args()

    nodes['dest1'].configure_hops(nodes['src1'], nodes['dest1'], None, nodes['rly1'])
    nodes['rly1'].configure_hops(nodes['src1'], nodes['dest1'], nodes['dest1'], nodes['src1'])
    nodes['src1'].configure_hops(nodes['src1'], nodes['dest1'], nodes['rly1'], None)

    
    simple_node = Simple_Node(nodes[id_list[int(options.index)]], l1_debug=(options.l1=='y' or options.l1 == 'Y'), l2_debug=(options.l2=='y' or options.l2 == 'Y'), l3_debug=(options.l3=='y' or options.l3 == 'Y'), l4_debug=(options.l4=='y' or options.l4 == 'Y'))
    try:
        simple_node.run()
    except:
        simple_node.close_threads()
        exit(0)
