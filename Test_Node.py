#!/usr/bin/env python3

'''
DQN experiment node object
'''
# Global Libraries
from threading import Thread
from argparse import ArgumentParser
from time import time, sleep
import csv, os

# User Libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Layer5
from Utils.Node_Config import Node_Config
from Utils.DQN import DQN, DQN_Config


class Test_Node():
    def __init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False, l5_debug=False, dqn_config=None):
        '''
        Emane Node class for network stack
        :param my_config: Node_Config class object
        :param l1_debug: bool for layer 1 debug outputs
        :param l2_debug: bool for layer 2 debug outputs
        :param l3_debug: bool for layer 3 debug outputs
        :param l4_debug: bool for layer 4 debug outputs
        :param l5_debug: bool for layer 5 debug outputs
        '''
        self.my_config = my_config
        self.stop_threads = False
        self.threads = {}

        # Initalize Network Stack

        self.layer4 = Layer4.Layer4(self.my_config, debug=l4_debug)
        self.layer3 = Layer3.Layer3(self.my_config, debug=l3_debug)
        self.layer2 = Layer2.Layer2(self.my_config.usrp_ip, debug=l2_debug)
        self.layer1 = Layer1.Layer1(self.my_config, debug=l1_debug)


        # Link layers together
        self.layer1.init_layers(upper=self.layer2, lower=None)
        self.layer2.init_layers(upper=self.layer3, lower=self.layer1)
        self.layer3.init_layers(upper=self.layer4, lower=self.layer2)
        self.layer4.init_layers(upper=None, lower=self.layer3)  # link l4 to this class object

        print("~ ~ Initialization Complete ~ ~", end='\n\n')
        

    def tx_func(self, stop):
        '''
        TODO
        '''
        while not stop():
            msg = input("Message to send: ")
            self.layer4.send_msg(msg)

    def rx_func(self, stop):
        '''
        TODO
        '''
        while not stop():
            msg = self.layer4.recv_msg()
            print(msg)

    def start_threads(self):
        '''
        Method to start all of the threads, passing in a lambda funciton returning the state of self.stop_threads
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~", end='\n\n')

        # Initialize threads
        
        for layer in [self.layer1, self.layer2, self.layer3, self.layer4]:
            self.threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_up"].start()
            self.threads[layer.layer_name + "_pass_down"] = Thread(target=layer.pass_down, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_down"].start() 
        
        if self.my_config.role == 'tx':
            self.threads["TX"] = Thread(target=self.tx_func, args=(lambda : self.stop_threads,))
            self.threads["TX"].start()

        elif self.my_config.role == 'rx':
            self.threads["RX"] = Thread(target=self.rx_func, args=(lambda : self.stop_threads,))
            self.threads["RX"].start()

        print("~ ~ Threads all running ~ ~", end='\n\n')

    def close_threads(self):
        '''
        Method to close all of the threads and subprocesses
        '''
        self.stop_threads = True
        
        print("\n ~ ~ Closing Threads ~ ~", end='\n\n')
        for thread in self.threads:
            try:
                self.threads[thread].join(0.1)
            except Exception as e:
                print(e)
                pass
        print("\n ~ ~ Threads Closed ~ ~", end='\n\n')
        os._exit(0)

    def handle_state(self, node_index, loc_index, pow_index):
        '''
        Method to handle receiving state info from another node
        :param  node_index: int for the node index number
        :param loc_index: int for the location index number
        :param pow_index: int for the tx power index number
        '''
        # [loc0, loc1, loc2, ..., locn, pow0, pow1, pow2, ..., pown ]
        self.state_buf[int(node_index)] = int(loc_index)
        self.state_buf[int(node_index) + self.num_nodes] = int(pow_index)

    def run(self):
        '''
        Main Function to run the test
        '''
        try:
            self.start_threads()
            sleep(10)   # wait 10 sec for usrp to init


            print('STARTED')
            sleep(60)
                
            print("~ ~ Finished Successfully ~ ~")
            self.close_threads()
                
                   
        except Exception as e:
            print(e)
            self.close_threads()
            


def main():
    '''
    Main Method
    '''
    freq1 = 2.3e9
    freq2 = 2.5e9

    dest1= Node_Config(pc_ip='192.168.10.101', usrp_ip='0.0.192.170.10.101', my_id='dest1', role='rx', tx_freq=freq2, rx_freq=freq1)
    src1 = Node_Config(pc_ip='192.168.10.103', usrp_ip='0.0.192.170.10.103', my_id='src1' , role='tx', tx_freq=freq1, rx_freq=freq2)

    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
    parser.add_argument('--l1', type=str, default='n', help='layer 1 debug (y/n)')
    parser.add_argument('--l2', type=str, default='n', help='layer 2 debug (y/n)')
    parser.add_argument('--l3', type=str, default='n', help='layer 3 debug (y/n)')
    parser.add_argument('--l4', type=str, default='n', help='layer 4 debug (y/n)')
    options = parser.parse_args()

    # Configure hops for route 1
    dest1.configure_hops(src=src1, dest=dest1, next_hop=None,  prev_hop=src1)
    src1.configure_hops( src=src1, dest=dest1, next_hop=dest1,  prev_hop=None)

    
    if int(options.index) == 0:
        my_config = dest1
    elif int(options.index) == 1:
        my_config = rly1
    elif int(options.index) == 2:
        my_config = src1
    elif int(options.index) == 3:
        my_config = dest2
    elif int(options.index) == 4:
        my_config = rly2
    elif int(options.index) == 5:
        my_config = src2
    else:
        print('INVALID INDEX')
        exit(0)
    
    my_node = Test_Node(my_config, l1_debug=(options.l1=='y' or options.l1 == 'Y'), l2_debug=(options.l2=='y' or options.l2 == 'Y'), l3_debug=(options.l3=='y' or options.l3 == 'Y'), l4_debug=(options.l4=='y' or options.l4 == 'Y'))
    try:
        my_node.run()
    except Exception as e:
        print(e)
        my_node.close_threads()
        exit(0)

if __name__ == '__main__':
    main()