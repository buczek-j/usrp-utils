#!/usr/bin/env python3

from Utils.Node_Config import Node_Config
from UAV_Node import UAV_Node
from argparse import ArgumentParser

def main():
    '''
    Main Method
    '''
    freq1 = 2.4e9
    freq2 = 2.5e9
    freq3 = 2.6e9

    dest1= Node_Config(pc_ip='192.168.10.101', usrp_ip='192.170.10.101', my_id='dest1', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=10)
    rly1 = Node_Config(pc_ip='192.168.10.102', usrp_ip='192.170.10.102', my_id='rly1', role='tx', tx_freq=freq2, rx_freq=freq1, serial="", location_index=24)
    src1 = Node_Config(pc_ip='192.168.10.103', usrp_ip='192.170.10.103', my_id='src1' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", location_index=0)

    dest2= Node_Config(pc_ip='192.168.10.104', usrp_ip='192.170.10.104', my_id='dest2', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=120)
    rly2 = Node_Config(pc_ip='192.168.10.105', usrp_ip='192.170.10.105', my_id='rly2', role='tx', tx_freq=freq2, rx_freq=freq1, serial="", location_index=70)
    src2 = Node_Config(pc_ip='192.168.10.106', usrp_ip='192.170.10.106', my_id='src2' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", location_index=55)

    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
    parser.add_argument('--csv', type=str, default='y', help='states from csv (y/n)')
    parser.add_argument('--fly_drone', type=str, default='y', help='Node UAV takesoff (y/n)')
    parser.add_argument('--wait', type=str, default='y', help='wait for other states before continuing (y/n)')
    parser.add_argument('--l1', type=str, default='n', help='layer 1 debug (y/n)')
    parser.add_argument('--l2', type=str, default='n', help='layer 2 debug (y/n)')
    parser.add_argument('--l3', type=str, default='n', help='layer 3 debug (y/n)')
    parser.add_argument('--l4', type=str, default='n', help='layer 4 debug (y/n)')
    options = parser.parse_args()

    # Configure hops for route 1
    dest1.configure_hops(src=src1, dest=dest1, next_hop=None,  prev_hop=rly1)
    rly1.configure_hops( src=src1, dest=dest1, next_hop=dest1, prev_hop=src1)
    src1.configure_hops( src=src1, dest=dest1, next_hop=rly1,  prev_hop=None)

    # Configure hops for route 2
    dest2.configure_hops(src=src2, dest=dest2, next_hop=None,  prev_hop=rly2)
    rly2.configure_hops( src=src2, dest=dest2, next_hop=dest2, prev_hop=src2)
    src2.configure_hops( src=src2, dest=dest2, next_hop=rly2,  prev_hop=None)

    alt = 5
    if int(options.index) == 0:
        my_config = rly1
        alt = 5
    elif int(options.index) == 1:
        my_config = rly2
        alt = 10
    else:
        print('INVALID INDEX')
        exit(0)
    fly_drone = (options.fly_drone=='y' or options.fly_drone=='Y')
    
    uav_node = UAV_Node(my_config, node_index=int(options.index), 
                                l1_debug=(options.l1=='y' or options.l1 == 'Y'), 
                                l2_debug=(options.l2=='y' or options.l2 == 'Y'), 
                                l3_debug=(options.l3=='y' or options.l3 == 'Y'), 
                                l4_debug=(options.l4=='y' or options.l4 == 'Y'), 
                                csv_in=(options.csv=='y' or options.csv=='Y'), 
                                fly_drone=fly_drone, 
                                wait=(options.wait=='y' or options.wait=='Y'),
                                num_nodes=2,
                                alt=alt)
    try:
        uav_node.run()
    except Exception as e:
        print(e)
        if fly_drone:
            uav_node.my_drone.handle_landing()
        uav_node.close_threads()
        exit(0)


if __name__ == '__main__':
    main()