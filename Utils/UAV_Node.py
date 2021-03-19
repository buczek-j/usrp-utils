#!/usr/bin/env python3

'''
Emane experiment node object
'''
# Global Libraries
from threading import Thread
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
from time import time, sleep

# User Libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Layer5
from Utils.Node_Config import Node_Config
from BasicArducopter import BasicArdu, Frames
from DQN import DQN, DQN_Config


class UAV_Node():
    def __init__(self, my_config, l1_debug=False, l2_debug=False, l3_debug=False, l4_debug=False, l5_debug=False, dqn_config=None, alt=5, num_nodes=6, min_iteration_time=5, loc_index=None, pow_index=None, node_index=0):
        '''
        Emane Node class for network stack
        :param my_config: Node_Config class object
        :param l1_debug: bool for layer 1 debug outputs
        :param l2_debug: bool for layer 2 debug outputs
        :param l3_debug: bool for layer 3 debug outputs
        :param l4_debug: bool for layer 4 debug outputs
        :param l5_debug: bool for layer 5 debug outputs
        #TODO
        '''
        
        self.my_config = my_config
        self.stop_threads = False
        self.threads = {}

        # Initalize Network Stack
        self.control_plane = Control_Plane.Control_Plane(my_config.pc_ip, self.my_config.listen_port)
        self.layer5 = Layer5.Layer5(self.my_config, debug=l5_debug)
        self.layer4 = Layer4.Layer4(self.my_config, self.control_plane.send_l4_ack, debug=l4_debug)
        self.layer3 = Layer3.Layer3(self.my_config, debug=l3_debug)
        self.layer2 = Layer2.Layer2(self.my_config.usrp_ip, send_ack=self.control_plane.send_l2_ack, debug=l2_debug)
        self.layer1 = Layer1.Layer1(self.my_config, debug=l1_debug)

        # Link layers together
        self.layer1.init_layers(upper=self.layer2, lower=None)
        self.layer2.init_layers(upper=self.layer3, lower=self.layer1)
        self.layer3.init_layers(upper=self.layer4, lower=self.layer2)
        self.layer4.init_layers(upper=self.layer5, lower=self.layer3)  # link l4 to this class object
        self.layer5.init_layers(upper=None, lower=self.layer4)

        # Drone parameters
        self.my_drone = BasicArdu(rame=Frames.NED, connection_string='/dev/ttyACM0', global_home=[42.47777625687639,-71.19357940183706,174.0])
        self.my_location = None
        self.my_alt = alt

        # Neural Ned params
        self.node_index = node_index    # 0 to num_nodes
        self.loc_index = loc_index   # [0 - 54] ~ 6 x 9 (x,y) coordinate locaiton (2 meter incriments)
        self.pow_index = pow_index      # [-1, 0, 1]        # TODO Confirm
        self.action = None

        self.neural_net = DQN(dqn_config)
        self.min_time = min_iteration_time
        self.state_buf = [None]*(2*num_nodes)
        self.num_nodes = num_nodes

        print("~ ~ Initialization Complete ~ ~", end='\n\n')

    def start_threads(self):
        '''
        Method to start all of the threads 
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~", end='\n\n')

        # Initialize threads
        self.threads["control_layer"] = Thread(target=self.control_plane.listening_socket, args=(self.layer2.recv_ack, self.layer4.recv_ack, self.handle_state, lambda : self.stop_threads, ))
        self.threads["control_layer"].start()

        for layer in [self.layer1, self.layer2, self.layer3, self.layer4]:
            self.threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_up"].start()
            self.threads[layer.layer_name + "_pass_down"] = Thread(target=layer.pass_down, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_down"].start() 
        
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
        print("\n ~ ~ Closing Threads ~ ~", end='\n\n')
        for thread in self.threads:
            try:
                self.threads[thread].join(0.1)
            except Exception as e:
                print(e)
                pass
            
        exit(0)

    def handle_state(self, node_index, loc_index, pow_index):
        '''
        Method to handle receiving state info from another node
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

            # takeoff 
            self.my_drone.handle_takeoff(abs(self.my_alt))
            self.my_drone.wait_for_target()

            # iterate
            while not self.stop_threads:
                
                # Goto State
                self.handle_action()

                # Broadcast State
                self.control_plane.broadcast_state(self.node_index + ',' + self.loc_index + ',' + self.pow_index)
                self.state_buf[self.node_index] = self.loc_index
                self.state_buf[self.num_nodes + self.node_index] = self.pow_index

                # Wait for all to broadcast state
                while None in self.state_buf:
                    sleep(0.01)

                start_time = time()
                # Wait for desired min iteration time to pass
                while time()-start_time<self.min_time:
                    sleep(0.01)
                
                # Run Neural Network
                self.action = self.neural_net.run(self.state_buf)       # TODO Update the NN run method 

                # Log Data
                # TODO

                # Reset State Buffer
                self.state_buf = [None]*(2*self.num_nodes)
                   
        except:
            self.stop_threads=True
            self.close_threads()
            self.my_drone.handle_landing()

            #sleep(5)
            #self.my_drone.handle_kill()


    def handle_action(self):
        '''
        Method to execute the input action based on the current action index
        '''
        # Parse action into state index
        if self.action:
            # self.loc_index = self.loc_index + self.action[0] # TODO

            loc_action = self.action[0]    
            if loc_action == -9:# down
                self.loc_index = self.loc_index - 6

            elif loc_action == -1:# left
                self.loc_index = self.loc_index - 1

            elif loc_action == 0: # stay
                self.loc_index = self.loc_index + 0
            
            elif loc_action == 1: # left
                self.loc_index = self.loc_index + 1
            
            if loc_action == 9: # down
                self.loc_index = self.loc_index + 6
            
            else:
                print('UNEXPECTED ACTION', self.action)

            self.pow_index = self.action[1]     # [-1, 0, 1] ~ [low, med, high]

            self.action = None

        # Change Tx power
        power_lookup = [0.5, 0.6, 0.7]      # TODO Calculate power level

        new_gain = None
        if self.pow_index == -1:
            new_gain = power_lookup[0]
        elif self.pow_index == 0:
            new_gain = power_lookup[1]
        elif self.pow_index == -1:
            new_gain = power_lookup[2]

        self.action_tx_gain(new_gain)   # set power

        # Change Location
        x = 2.0 * (self.loc_index % 6)
        y = 2.0 * (int(self.loc_index / 6) + 1)

        # x = 2.0 * (self.loc_index / 9)
        # y = 2.0 * (int(self.loc_index % 9) + 1)   # TODO

        self.action_move([y, x])

    def action_move(self, coords):
        '''
        Method to perform a movement action on the drone
        :param coords: array of floats for the ned NED location
        '''
        self.my_drone.handle_waypoint(Frames.NED, coords[0], coords[1], -1.0*abs(self.my_alt), 0)
        self.my_drone.wait_for_target()

    def action_rx_gain(self, gain):
        '''
        Method to perfomr a rx gain adjust action
        :param gain: float for the new gain (0.0-1.0)
        '''
        self.layer1.set_rx_gain(gain)

    def action_tx_gain(self, gain):
        '''
        Method to perform a tx gain adjust action
        :param gain: float for the new gain (0.0-1.0)
        '''
        self.layer1.set_tx_gain(gain)


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
