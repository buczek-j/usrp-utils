#!/usr/bin/env python3

'''
DQN experiment node object

TODO:
- Debug
- runtime of 5min once last action, stay until runtime finishes, then land

- power levels
    - -20dBm to 20dBm
    - 2 dbm steps (20 total)

- Only specify one or two drones

- convert to state for csv read in

- humanreadable log time

'''


# Global Libraries
from threading import Thread
from argparse import ArgumentParser
from time import time, sleep
import tensorflow.compat.v1 as tf
import csv, os

# User Libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Layer5
from Utils.Node_Config import Node_Config
from Utils.Transforms import global_to_NED
from BasicArducopter.BasicArdu import BasicArdu, Frames
from Utils.DQN import DQN, DQN_Config


class UAV_Node():
    def __init__(self, my_config, 
                    l1_debug=False, 
                    l2_debug=False, 
                    l3_debug=False, 
                    l4_debug=False, 
                    l5_debug=False, 
                    wait=True,
                    dqn_config=None, 
                    alt=5, 
                    num_nodes=3, 
                    min_iteration_time=5.0, 
                    pow_index=3, 
                    node_index=0, 
                    log_base_name="~/Documents/usrp-utils/Logs/log_", 
                    state_dir='~/Documents/usrp-utils/FromCsv/performance_data_',
                    csv_in=False, 
                    model_path='~/Documents/usrp-utils/saved_models/asym_scenarios_50container_loc/', 
                    model_stage=270,
                    fly_drone=True,
                    ):
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
        TODO
        '''
        
        # Setup Log File
        self.csv_name = log_base_name + str(round(time())) + '.csv'
        row_list = ["Iteration Number","Node0 Loc", "Node1 Loc", "Node2 Loc", "Node3 Loc", "Node4 Loc", "Node5 Loc", "Node0 Tx Gain", "Node1 Tx Gain", "Node2 Tx Gain", "Node3 Tx Gain", "Node4 Tx Gain", "Node5 Tx Gain", "Number L4 Acks"]
        self.file = open(os.path.expanduser(self.csv_name), 'a', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(row_list)

        self.wait = wait
        self.fly_drone = fly_drone

        # csv_input
        if csv_in:
            self.csv_in = True
            self.state_csv = open(os.path.expanduser(state_dir+my_config.id+'.csv'), 'r', newline='')
            self.state_reader = csv.reader(self.state_csv)

        self.my_config = my_config
        self.stop_threads = False
        self.threads = {}

        # Initalize Network Stack
        self.control_plane = Control_Plane.Control_Plane(my_config.pc_ip)
        
        self.layer4 = Layer4.Layer4(self.my_config, self.control_plane.send_l4_ack, debug=l4_debug)
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

        # Drone parameters
        if self.fly_drone:
            # self.my_drone = BasicArdu(frame=Frames.NED, connection_string='/dev/ttyACM0', global_home=[42.47777625687639,-71.19357940183706,174.0]) 
            self.my_drone = BasicArdu(frame=Frames.NED, connection_string='tcp:192.168.10.2:'+str(5762+10*node_index), global_home=[42.47777625687639,-71.19357940183706,174.0]) 
            self.my_location = None
            self.my_alt = alt

        # Neural Net params
        self.node_index = node_index    # 0 to num_nodes-1
        self.loc_index = self.my_config.location_index  # 11x11 maxtix index (x,y) 0:(0,0), 1:(0,1), 11:(1,0), 12:(1,1)...
        self.pow_index = pow_index      # [2,3,4]
        self.action = None

        if csv_in==False and 'rly' in self.my_config.id:  # only run NN for relays
            self.neural_net = DQN(dqn_config)
            self.init = tf.global_variables_initializer()
            self.session = tf.InteractiveSession()
            self.session.run(self.init)
            self.saver = tf.train.Saver(max_to_keep=10)
            self.neural_net.set_session(self.session)
            self.saver.restore(self.neural_net.session, os.path.expanduser(str(model_path + "tf_model_{}-{}") ).format("rly11", model_stage))

        # state buffer vars
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
            for jj in range(layer.window):
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

    def state_loop(self):
        '''
        Method to prompt and wait for node states (synchronize)
        '''
        if self.wait:
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

    def test_throughput(self):
        '''
        method to test the network throughput
        '''
        self.layer5.transmit=True
        start_time = time()
        # Wait for desired min iteration time to pass
        while time()-start_time<self.min_time:
            sleep(0.01)
        self.layer5.transmit=False

    def run(self):
        '''
        Main Function to run the test
        '''
        try:
            self.start_threads()
            sleep(10)   # wait 10 sec for usrp to init

            if self.fly_drone:
                # takeoff 
                self.my_drone.handle_takeoff(abs(self.my_alt))
                self.my_drone.wait_for_target()   

            # iterate
            iteration_num = 0

            if not self.csv_in: # run NN
                while not self.stop_threads:
                    if self.layer4.log:
                        self.layer4.writer.writerow(["Iteration Number: " +str(iteration_num)])
                    # Goto State
                    self.handle_action()

                    # Broadcast State
                    while None in self.state_buf:
                        self.control_plane.broadcast_state(str(self.node_index) + ',' + str(self.loc_index) + ',' + str(self.pow_index))
                        sleep(0.5)
                        self.control_plane.broadcast_state(str(self.node_index) + ',' + str(self.loc_index) + ',' + str(self.pow_index))
                        print('Waiting for state buffer. . .')

                    # Begin Test
                    self.layer5.transmit=True
                    start_time = time()
                    # Wait for desired min iteration time to pass
                    while time()-start_time<self.min_time:
                        sleep(0.01)
                    self.layer5.transmit=False
                    
                    # Run Neural Network
                    if 'rly' in self.my_config.id:  # only run NN for relays
                        self.action = self.neural_net.run(self.state_buf)

                    # Log Data
                    self.writer.writerow([iteration_num]+self.state_buf+[self.layer4.n_ack])

                    # Reset State Buffer
                    self.state_buf = [None]*(2*self.num_nodes)
                    iteration_num += 1
            
            else: # actions from CSV
                print('~ ~ Reading From CSV ~ ~\n')
                for Exp_Ind, Loc_x, Loc_y, Loc_z, TxPower, sessRate, runTime, l2Ack, l2Time, l4Ack, l4Time, rtDelay, l2TxQueue, l4TxQueue, l2Sent in self.state_reader:
                    print('\n~~ Iteration', iteration_num, ' ~~')
                    if self.layer4.log:
                        self.layer4.writer.writerow(["Iteration Number: " +str(iteration_num)])

                    # goto state
                    self.action_move([float(Loc_y), float(Loc_x)])
                    self.action_tx_gain(float(TxPower)/90)     # TODO

                    # Broadcast State
                    self.state_loop()

                    # Run throuhgput test
                    self.test_throughput()

                    # Log Data
                    self.writer.writerow([iteration_num]+self.state_buf+[self.layer4.n_ack, self.min_time])
                    print(" - log data")
                    print("num acks:", self.layer4.n_ack, "time:", self.min_time)

                    # Reset 
                    self.layer4.n_ack = 0
                    self.state_buf = [None]*(2*self.num_nodes)
                    
                    iteration_num += 1
                    print(" - reset")
                
            print("~ ~ Finished Successfully ~ ~")
            if self.fly_drone:
                self.my_drone.handle_landing()
            self.close_threads()
                
                   
        except Exception as e:
            print(e)
            if self.fly_drone:
                self.my_drone.handle_landing()
            self.close_threads()
            
            #sleep(5)
            #self.my_drone.handle_kill()

    def handle_action(self):
        '''
        Method to execute the input action based on the current action index
        '''
        # Parse action into state index
        if self.action:

            loc_action = self.action[0]    # [-9, -1, 0, 1, 9]
            if loc_action == 0:# west
                self.loc_index = self.loc_index - 11

            elif loc_action == 1:# north
                self.loc_index = self.loc_index - 1

            elif loc_action == 2: # stay
                self.loc_index = self.loc_index + 0
            
            elif loc_action == 3: # south
                self.loc_index = self.loc_index + 1
            
            elif loc_action == 4: # east
                self.loc_index = self.loc_index + 11
            
            else:
                print('ERROR: UNEXPECTED LOC ACTION', self.action)

            pow_action = self.action[1]     # [-1, 0, 1] 
            if pow_action == 0:    # decrease
                if self.pow_index >2:   # if can decrease
                    self.pow_index = self.pow_index -1 
                else:
                    print("ERROR: INVALID POWER ACTION")
            elif pow_action == 1:
                self.pow_index = self.pow_index # no change
            
            elif pow_action == 2: # increase
                if self.pow_index < 4: # if can increase
                    self.pow_index = self.pow_index + 1
                else:
                    print("ERROR: INVALID POWER ACTION")
            else:
                print('ERROR: UNEXPECTED TX ACTION', self.action)

            self.action = None

        # Change Tx power
        power_lookup = [0.5, 0.6, 0.7]      # TODO Calculate power level
        """
        power_lookup = [-20, -15, -10] dBm
        power state 2, 3, 4
        """

        new_gain = None
        if self.pow_index == 2:
            new_gain = power_lookup[0]
        elif self.pow_index == 3:
            new_gain = power_lookup[1]
        elif self.pow_index == 4:
            new_gain = power_lookup[2]

        self.action_tx_gain(new_gain)   # set power

        # Change Location
        self.action_move(global_to_NED(self.loc_index))  

    def action_move(self, coords):
        '''
        Method to perform a movement action on the drone
        :param coords: array of floats for the ned NED location [meters north, meters east, meters down]
        '''
        if self.fly_drone:
            self.my_drone.handle_waypoint(Frames.NED, coords[0], coords[1], -1.0*abs(self.my_alt), 0)
            self.my_drone.wait_for_target()
        print('Move:', coords[0], coords[1])

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
        print('TX Gain:', gain)


def main():
    '''
    Main Method
    '''
    freq1 = 2.4e9
    freq2 = 2.5e9
    freq3 = 2.6e9

    dest1= Node_Config(pc_ip='192.168.10.101', usrp_ip='192.170.10.101', my_id='dest1', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=10)
    rly1 = Node_Config(pc_ip='192.168.10.102', usrp_ip='192.170.10.102', my_id='rly1', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", location_index=24)
    src1 = Node_Config(pc_ip='192.168.10.103', usrp_ip='192.170.10.103', my_id='src1' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", location_index=0)

    dest2= Node_Config(pc_ip='192.168.10.104', usrp_ip='192.170.10.104', my_id='dest2', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", location_index=120)
    rly2 = Node_Config(pc_ip='192.168.10.105', usrp_ip='192.170.10.105', my_id='rly2', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", location_index=70)
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
    fly_drone = (options.fly_drone=='y' or options.fly_drone=='Y')
    
    uav_node = UAV_Node(my_config, node_index=int(options.index), 
                                l1_debug=(options.l1=='y' or options.l1 == 'Y'), 
                                l2_debug=(options.l2=='y' or options.l2 == 'Y'), 
                                l3_debug=(options.l3=='y' or options.l3 == 'Y'), 
                                l4_debug=(options.l4=='y' or options.l4 == 'Y'), 
                                csv_in=(options.csv=='y' or options,csv=='Y'), 
                                fly_drone=fly_drone, 
                                wait=(options.wait=='y' or options.wait=='Y'))
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