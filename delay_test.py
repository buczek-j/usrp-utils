#!/usr/bin/env python3



# Global Libraries
from threading import Thread
from argparse import ArgumentParser
from time import time, sleep

import csv, os

# User Libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Layer5
from Utils.Node_Config import Node_Config
from Utils.Transforms import global_to_NED



class UAV_Node():
    def __init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False, l5_debug=False, dqn_config=None, alt=5, num_nodes=3, min_iteration_time=10.0, pow_index=3, node_index=0, log_base_name="~/Documents/usrp-utils/Logs/log_", csv_in=False, model_path='~/Documents/usrp-utils/saved_models/asym_scenarios_50container_loc/', model_stage=270):
        '''
        Emane Node class for network stack
        :param my_config: Node_Config class object
        :param l1_debug: bool for layer 1 debug outputs
        :param l2_debug: bool for layer 2 debug outputs
        :param l3_debug: bool for layer 3 debug outputs
        :param l4_debug: bool for layer 4 debug outputs
        :param l5_debug: bool for layer 5 debug outputs
        :param dqn_config: DQN_Config class object 
        :param alt: float for the altitude (meters) that the UAV should fly at
        :param num_nodes: int for the number of Nodes to get states from
        :param min_iteration_time: float for the time to test each iteration (s)
        :param pow_index: int for the startng tx power state index
        :param node_index: int for the node index number
        :param log_base_name: string for the directory and base name to save log files
        :param csv_in: bool for if actions should be determined from the csv file or the neural network
        :param model_path: string for the directory for the neural network model
        '''
        
        # Setup Log File
        self.csv_name = log_base_name + str(round(time())) + '.csv'
        row_list = ["Iteration Number","Node0 Loc", "Node1 Loc", "Node2 Loc", "Node3 Loc", "Node4 Loc", "Node5 Loc", "Node0 Tx Gain", "Node1 Tx Gain", "Node2 Tx Gain", "Node3 Tx Gain", "Node4 Tx Gain", "Node5 Tx Gain", "Number L4 Acks"]
        self.file = open(os.path.expanduser(self.csv_name), 'a', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(row_list)

        self.my_config = my_config
        self.stop_threads = False
        self.threads = {}

        # Initalize Network Stack
        self.control_plane = Control_Plane.Control_Plane(my_config.pc_ip)
        
        self.layer4 = Layer4.Layer4(self.my_config, self.control_plane.send_l4_ack, debug=l4_debug, window=2)
        self.layer3 = Layer3.Layer3(self.my_config, debug=l3_debug)
        self.layer2 = Layer2.Layer2(self.my_config.usrp_ip, send_ack=self.control_plane.send_l2_ack, debug=l2_debug)
        self.layer1 = Layer1.Layer1(self.my_config, debug=l1_debug)
        self.layer5 = Layer5.Layer5(self.my_config, self.layer4, debug=l5_debug)

        # Link layers together
        self.layer1.init_layers(upper=self.layer2, lower=None)
        self.layer2.init_layers(upper=self.layer3, lower=self.layer1)
        self.layer3.init_layers(upper=self.layer4, lower=self.layer2)
        self.layer4.init_layers(upper=self.layer5, lower=self.layer3)  # link l4 to this class object
        self.layer5.init_layers(upper=None, lower=self.layer4)

        # Neural Net params
        self.node_index = node_index    # 0 to num_nodes
        self.loc_index = self.my_config.location_index  # 11x11 maxtix index (x,y) 0:(0,0), 1:(0,1), 11:(1,0), 12:(1,1)...
        self.pow_index = pow_index      # [2,3,4]
        self.action = None

        self.min_time = min_iteration_time
        self.state_buf = [None]*(2*num_nodes)
        self.num_nodes = num_nodes
        self.get_state_msg = False

        print("~ ~ Initialization Complete ~ ~", end='\n\n')
        
    def start_threads(self):
        '''
        Method to start all of the threads, passing in a lambda funciton returning the state of self.stop_threads
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~", end='\n\n')

        # Initialize threads
        self.threads["L2_ACK_RCV"] = Thread(target=self.control_plane.listen_l2, args=(self.layer2.recv_ack, lambda : self.stop_threads, ))
        self.threads["L2_ACK_RCV"].start()

        self.threads["L4_ACK_RCV"] = Thread(target=self.control_plane.listen_l4, args=(self.layer4.recv_ack, lambda : self.stop_threads, ))
        self.threads["L4_ACK_RCV"].start()

        self.threads["STATE_RCV"] = Thread(target=self.control_plane.listen_cc, args=(self.handle_state, self.handle_get_state, lambda : self.stop_threads, ))
        self.threads["STATE_RCV"].start()

        for layer in [self.layer1, self.layer2, self.layer3, self.layer4]:
            
            self.threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_up"].start()
            for jj in layer.window:
                self.threads[layer.layer_name + "_pass_down_"+str(jj)] = Thread(target=layer.pass_down, args=(lambda : self.stop_threads,))
                self.threads[layer.layer_name + "_pass_down_"+str(jj)].start() 
        
        if self.my_config.role == 'tx':
            self.threads[self.layer5.layer_name + "_pass_down"] = Thread(target=self.layer5.pass_down, args=(lambda : self.stop_threads,))
            self.threads[self.layer5.layer_name + "_pass_down"].start()

        elif self.my_config.role == 'rx':
            self.threads[self.layer5.layer_name + "_pass_up"] = Thread(target=self.layer5.pass_up, args=(lambda : self.stop_threads,))
            self.threads[self.layer5.layer_name + "_pass_up"].start()

        print("~ ~ Threads all running ~ ~", end='\n\n')

    def close_threads(self):
        '''
        Method to close all of the threads and subprocesses
        '''
        self.stop_threads = True
        self.file.close()           # close node logging file
        self.layer4.file.close()    # close l4 logging file

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
        # print(node_index, loc_index, pow_index)

    def handle_get_state(self):
        '''
        Method to handle receiving "I need a state message" message
        '''
        self.get_state_msg = True


    def run(self):
        '''
        Main Function to run the test
        '''
        try:
            self.start_threads()
            sleep(10)   # wait 10 sec for usrp to init

            # iterate
            iteration_num = 0

            print('~ ~ Beginning ~ ~\n')

            #[l4_timeout, l2_timeout,  l5_rate]
            setups = [
                [1.0, 0.1, 20000],
                [0.03, 0.02, 20000],
                # [0.5, 0.5, 2000],
                # [0.5, 0.4, 2000],
                # [0.5, 0.3, 2000],
                # [0.5, 0.2, 2000],
                # [0.5, 0.1, 2000],
                # [0.5, 0.09, 2000],
                # [0.5, 0.08, 2000],
                # [0.5, 0.07, 2000],
                # [0.5, 0.06, 2000],
                # [0.5, 0.05, 2000],
                # [0.5, 0.04, 2000],
                # [0.5, 0.03, 2000],
                # [0.5, 0.02, 2000],

                # [0.5, 0.5, 4000],
                # [0.5, 0.4, 4000],
                # [0.5, 0.3, 4000],
                # [0.5, 0.2, 4000],
                # [0.5, 0.1, 4000],
                # [0.5, 0.09, 4000],
                # [0.5, 0.08, 4000],
                # [0.5, 0.07, 4000],
                # [0.5, 0.06, 4000],
                # [0.5, 0.05, 4000],
                # [0.5, 0.04, 4000],
                # [0.5, 0.03, 4000],
                # [0.5, 0.02, 4000],

                # [0.5, 0.5, 6000],
                # [0.5, 0.4, 6000],
                # [0.5, 0.3, 6000],
                # [0.5, 0.2, 6000],
                # [0.5, 0.1, 6000],
                # [0.5, 0.09, 6000],
                # [0.5, 0.08, 6000],
                # [0.5, 0.07, 6000],
                # [0.5, 0.06, 6000],
                # [0.5, 0.05, 6000],
                # [0.5, 0.04, 6000],
                # [0.5, 0.03, 6000],
                # [0.5, 0.02, 6000],

                # [0.5, 0.5, 8000],
                # [0.5, 0.4, 8000],
                # [0.5, 0.3, 8000],
                # [0.5, 0.2, 8000],
                # [0.5, 0.1, 8000],
                # [0.5, 0.09, 8000],
                # [0.5, 0.08, 8000],
                # [0.5, 0.07, 8000],
                # [0.5, 0.06, 8000],
                # [0.5, 0.05, 8000],
                # [0.5, 0.04, 8000],
                # [0.5, 0.03, 8000],
                # [0.5, 0.02, 8000],

                # [0.5, 0.5, 10000],
                # [0.5, 0.4, 10000],
                # [0.5, 0.3, 10000],
                # [0.5, 0.2, 10000],
                # [0.5, 0.1, 10000],
                # [0.5, 0.09, 10000],
                # [0.5, 0.08, 10000],
                # [0.5, 0.07, 10000],
                # [0.5, 0.06, 10000],
                # [0.5, 0.05, 10000],
                # [0.5, 0.04, 10000],
                # [0.5, 0.03, 10000],
                # [0.5, 0.02, 10000],
                # #

                # [0.7, 0.5, 2000],
                # [0.7, 0.4, 2000],
                # [0.7, 0.3, 2000],
                # [0.7, 0.2, 2000],
                # [0.7, 0.1, 2000],
                # [0.7, 0.09, 2000],
                # [0.7, 0.08, 2000],
                # [0.7, 0.07, 2000],
                # [0.7, 0.06, 2000],
                # [0.7, 0.05, 2000],
                # [0.7, 0.04, 2000],
                # [0.7, 0.03, 2000],
                # [0.7, 0.02, 2000],

                # [0.7, 0.5, 4000],
                # [0.7, 0.4, 4000],
                # [0.7, 0.3, 4000],
                # [0.7, 0.2, 4000],
                # [0.7, 0.1, 4000],
                # [0.7, 0.09, 4000],
                # [0.7, 0.08, 4000],
                # [0.7, 0.07, 4000],
                # [0.7, 0.06, 4000],
                # [0.7, 0.05, 4000],
                # [0.7, 0.04, 4000],
                # [0.7, 0.03, 4000],
                # [0.7, 0.02, 4000],

                # [0.7, 0.5, 6000],
                # [0.7, 0.4, 6000],
                # [0.7, 0.3, 6000],
                # [0.7, 0.2, 6000],
                # [0.7, 0.1, 6000],
                # [0.7, 0.09, 6000],
                # [0.7, 0.08, 6000],
                # [0.7, 0.07, 6000],
                # [0.7, 0.06, 6000],
                # [0.7, 0.05, 6000],
                # [0.7, 0.04, 6000],
                # [0.7, 0.03, 6000],
                # [0.7, 0.02, 6000],

                # [0.7, 0.5, 8000],
                # [0.7, 0.4, 8000],
                # [0.7, 0.3, 8000],
                # [0.7, 0.2, 8000],
                # [0.7, 0.1, 8000],
                # [0.7, 0.09, 8000],
                # [0.7, 0.08, 8000],
                # [0.7, 0.07, 8000],
                # [0.7, 0.06, 8000],
                # [0.7, 0.05, 8000],
                # [0.7, 0.04, 8000],
                # [0.7, 0.03, 8000],
                # [0.7, 0.02, 8000],

                # [0.7, 0.5, 10000],
                # [0.7, 0.4, 10000],
                # [0.7, 0.3, 10000],
                # [0.7, 0.2, 10000],
                # [0.7, 0.1, 10000],
                # [0.7, 0.09, 10000],
                # [0.7, 0.08, 10000],
                # [0.7, 0.07, 10000],
                # [0.7, 0.06, 10000],
                # [0.7, 0.05, 10000],
                # [0.7, 0.04, 10000],
                # [0.7, 0.03, 10000],
                # [0.7, 0.02, 10000],
                # #
                # [1.0, 0.5, 2000],
                # [1.0, 0.4, 2000],
                # [1.0, 0.3, 2000],
                # [1.0, 0.2, 2000],
                # [1.0, 0.1, 2000],
                # [1.0, 0.09, 2000],
                # [1.0, 0.08, 2000],
                # [1.0, 0.07, 2000],
                # [1.0, 0.06, 2000],
                # [1.0, 0.05, 2000],
                # [1.0, 0.04, 2000],
                # [1.0, 0.03, 2000],
                # [1.0, 0.02, 2000],

                # [1.0, 0.5, 4000],
                # [1.0, 0.4, 4000],
                # [1.0, 0.3, 4000],
                # [1.0, 0.2, 4000],
                # [1.0, 0.1, 4000],
                # [1.0, 0.09, 4000],
                # [1.0, 0.08, 4000],
                # [1.0, 0.07, 4000],
                # [1.0, 0.06, 4000],
                # [1.0, 0.05, 4000],
                # [1.0, 0.04, 4000],
                # [1.0, 0.03, 4000],
                # [1.0, 0.02, 4000],

                # [1.0, 0.5, 6000],
                # [1.0, 0.4, 6000],
                # [1.0, 0.3, 6000],
                # [1.0, 0.2, 6000],
                # [1.0, 0.1, 6000],
                # [1.0, 0.09, 6000],
                # [1.0, 0.08, 6000],
                # [1.0, 0.07, 6000],
                # [1.0, 0.06, 6000],
                # [1.0, 0.05, 6000],
                # [1.0, 0.04, 6000],
                # [1.0, 0.03, 6000],
                # [1.0, 0.02, 6000],

                # [1.0, 0.5, 8000],
                # [1.0, 0.4, 8000],
                # [1.0, 0.3, 8000],
                # [1.0, 0.2, 8000],
                # [1.0, 0.1, 8000],
                # [1.0, 0.09, 8000],
                # [1.0, 0.08, 8000],
                # [1.0, 0.07, 8000],
                # [1.0, 0.06, 8000],
                # [1.0, 0.05, 8000],
                # [1.0, 0.04, 8000],
                # [1.0, 0.03, 8000],
                # [1.0, 0.02, 8000],

                # [1.0, 0.5, 10000],
                # [1.0, 0.4, 10000],
                # [1.0, 0.3, 10000],
                # [1.0, 0.2, 10000],
                # [1.0, 0.1, 10000],
                # [1.0, 0.09, 10000],
                # [1.0, 0.08, 10000],
                # [1.0, 0.07, 10000],
                # [1.0, 0.06, 10000],
                # [1.0, 0.05, 10000],
                # [1.0, 0.04, 10000],
                # [1.0, 0.03, 10000],
                # [1.0, 0.02, 10000],
                # #

                # [1.5, 0.5, 2000],
                # [1.5, 0.4, 2000],
                # [1.5, 0.3, 2000],
                # [1.5, 0.2, 2000],
                # [1.5, 0.1, 2000],
                # [1.5, 0.09, 2000],
                # [1.5, 0.08, 2000],
                # [1.5, 0.07, 2000],
                # [1.5, 0.06, 2000],
                # [1.5, 0.05, 2000],
                # [1.5, 0.04, 2000],
                # [1.5, 0.03, 2000],
                # [1.5, 0.02, 2000],

                # [1.5, 0.5, 4000],
                # [1.5, 0.4, 4000],
                # [1.5, 0.3, 4000],
                # [1.5, 0.2, 4000],
                # [1.5, 0.1, 4000],
                # [1.5, 0.09, 4000],
                # [1.5, 0.08, 4000],
                # [1.5, 0.07, 4000],
                # [1.5, 0.06, 4000],
                # [1.5, 0.05, 4000],
                # [1.5, 0.04, 4000],
                # [1.5, 0.03, 4000],
                # [1.5, 0.02, 4000],

                # [1.5, 0.5, 6000],
                # [1.5, 0.4, 6000],
                # [1.5, 0.3, 6000],
                # [1.5, 0.2, 6000],
                # [1.5, 0.1, 6000],
                # [1.5, 0.09, 6000],
                # [1.5, 0.08, 6000],
                # [1.5, 0.07, 6000],
                # [1.5, 0.06, 6000],
                # [1.5, 0.05, 6000],
                # [1.5, 0.04, 6000],
                # [1.5, 0.03, 6000],
                # [1.5, 0.02, 6000],

                # [1.5, 0.5, 8000],
                # [1.5, 0.4, 8000],
                # [1.5, 0.3, 8000],
                # [1.5, 0.2, 8000],
                # [1.5, 0.1, 8000],
                # [1.5, 0.09, 8000],
                # [1.5, 0.08, 8000],
                # [1.5, 0.07, 8000],
                # [1.5, 0.06, 8000],
                # [1.5, 0.05, 8000],
                # [1.5, 0.04, 8000],
                # [1.5, 0.03, 8000],
                # [1.5, 0.02, 8000],

                # [1.5, 0.5, 10000],
                # [1.5, 0.4, 10000],
                # [1.5, 0.3, 10000],
                # [1.5, 0.2, 10000],
                # [1.5, 0.1, 10000],
                # [1.5, 0.09, 10000],
                # [1.5, 0.08, 10000],
                # [1.5, 0.07, 10000],
                # [1.5, 0.06, 10000],
                # [1.5, 0.05, 10000],
                # [1.5, 0.04, 10000],
                # [1.5, 0.03, 10000],
                # [1.5, 0.02, 10000],
                # #
            ]


            for setup_test in setups:
                sleep(1)
                l4_timeout = setup_test[0]
                l2_timeout = setup_test[1]
                l5_thrpt = setup_test[2]
                # l2_num_retran = int((l4_timeout/l2_timeout)-1)
                l2_num_retran = 4
                print('\n~~ Iteration', iteration_num, ' ~~')
                setup = "Iteration Number: " +str(iteration_num) + ", l5_max_thrpt:"+ str(l5_thrpt)+ ", l4_timeout:" + str(l4_timeout) + ", l2_timeout:" + str(l2_timeout) + ", l2_num: " + str(l2_num_retran)
                if self.layer4.log:

                    self.layer4.writer.writerow([setup])

                # goto state
                self.layer5.tspt_rate = l5_thrpt
                self.layer4.timeout = l4_timeout
                self.layer2.timeout = l2_timeout
                self.layer2.n_retrans = l2_num_retran
                

                # Broadcast State
                state_loop = True
                state_timeout = time()
                print('Waiting for state buffer. . .')
                while state_loop:
                    if None in self.state_buf:
                        self.control_plane.get_state_msgs()  
                        state_timeout = time()
                    
                    if self.get_state_msg == True:
                        self.get_state_msg = False
                        self.control_plane.broadcast_state(str(self.node_index) + ',' + str(self.loc_index) + ',' + str(self.pow_index))
                        state_timeout = time()
                    
                    if time() - state_timeout > 1:
                        state_loop = False

                    sleep(0.1)

                self.layer5.transmit=True
                start_time = time()
                # Wait for desired min iteration time to pass
                while time()-start_time<self.min_time:
                    sleep(0.01)
                self.layer5.transmit=False

                

                # Log Data
                self.writer.writerow([iteration_num]+self.state_buf+[self.layer4.n_ack])
                print(" - log data")
                print(setup)
                print("num acks:", self.layer4.n_ack)

                # Reset State Buffer
                self.layer4.n_ack = 0
                
                iteration_num += 1
                print(" - reset")
                
            print("~ ~ Finished Successfully ~ ~")
            
            self.close_threads()
                
                   
        except Exception as e:
            print(e)
            self.close_threads()
            
            #sleep(5)
            #self.my_drone.handle_kill()

    



def main():
    '''
    Main Method
    '''
    freq1 = 2.2e9
    freq2 = 2.1e9
    freq3 = 2.6e9

    dest1= Node_Config(pc_ip='192.168.10.101', usrp_ip='192.170.10.101', my_id='dest1', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=10)
    rly1 = Node_Config(pc_ip='192.168.10.102', usrp_ip='192.170.10.102', my_id='rly1', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", location_index=24)
    src1 = Node_Config(pc_ip='192.168.10.103', usrp_ip='192.170.10.103', my_id='src1' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", location_index=0)

    dest2= Node_Config(pc_ip='192.168.10.104', usrp_ip='192.170.10.104', my_id='dest2', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=120)
    rly2 = Node_Config(pc_ip='192.168.10.105', usrp_ip='192.170.10.105', my_id='rly2', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", location_index=70)
    src2 = Node_Config(pc_ip='192.168.10.106', usrp_ip='192.170.10.106', my_id='src2' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", location_index=55)

    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
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
    
    uav_node = UAV_Node(my_config, node_index=int(options.index), l1_debug=(options.l1=='y' or options.l1 == 'Y'), l2_debug=(options.l2=='y' or options.l2 == 'Y'), l3_debug=(options.l3=='y' or options.l3 == 'Y'), l4_debug=(options.l4=='y' or options.l4 == 'Y'), csv_in=True)
    try:
        uav_node.run()
    except Exception as e:
        print(e)

        exit(0)

if __name__ == '__main__':
    main()