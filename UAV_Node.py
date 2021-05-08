#!/usr/bin/env python3

'''
DQN experiment node object
'''

# Global Libraries
from threading import Thread
from argparse import ArgumentParser
from time import time, sleep
import tensorflow.compat.v1 as tf
import csv, os, datetime

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
                    num_nodes=6, 
                    min_iteration_time=5.0, 
                    pow_index=3, 
                    node_index=0, 
                    log_base_name="~/Documents/usrp-utils/Logs/log_", 
                    log=True,
                    state_dir='~/Documents/usrp-utils/FromCsv/performance_data_',
                    csv_in=False, 
                    model_path='~/Documents/usrp-utils/saved_models/asym_scenarios_50container_loc/', 
                    model_stage=270,
                    fly_drone=True,
                    use_radio=True,
                    tx_optimization=True,
                    is_sim=False,
                    global_home=None,
                    is_dji=False,
                    use_timeout=False,
                    test_timeout=5
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
        self.log = log
        # Setup Log File
        if self.log:
            self.csv_name = log_base_name + datetime.datetime.now().strftime("___%m-%d-%y___%H-%M")+".csv"
            row_list = ["Iteration Number","Node0 Loc", "Node1 Loc", "Node2 Loc", "Node3 Loc", "Node4 Loc", "Node5 Loc", "Node0 Tx Gain", "Node1 Tx Gain", "Node2 Tx Gain", "Node3 Tx Gain", "Node4 Tx Gain", "Node5 Tx Gain", "Number L4 Acks"]
            self.log_data(row_list)

        # Flags
        self.wait = wait
        self.fly_drone = fly_drone
        self.use_radio=use_radio
        self.tx_optimization = tx_optimization
        self.is_sim = is_sim
        self.is_dji = is_dji
        self.use_timeout = use_timeout
        self.test_timeout = test_timeout

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
        
        if self.use_radio:
            self.layer4 = Layer4.Layer4(self.my_config, self.control_plane.send_l4_ack, debug=l4_debug, log=self.log, l4_log_base_name=log_base_name+"l4_")
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
        if self.fly_drone and not self.is_dji:
            if self.is_sim==True:
                self.my_drone = BasicArdu(frame=Frames.NED, connection_string='tcp:192.168.10.138:'+str(5762+10*node_index), global_home=global_home) 
            else:
                self.my_drone = BasicArdu(frame=Frames.NED, connection_string='/dev/ttyACM0', global_home=global_home) 

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
        
    def log_data(self, data_row):
        '''
        Method to open csv file and log data
        :param data_row: array of data to log 
        '''
        if self.log:
            file = open(os.path.expanduser(self.csv_name), 'a', newline='')
            writer = csv.writer(file)
            writer.writerow(data_row)
            file.close()


    def start_threads(self):
        '''
        Method to start all of the threads, passing in a lambda funciton returning the state of self.stop_threads
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~", end='\n\n')

        # Initialize threads
        if self.use_radio:
            self.threads["L2_ACK_RCV"] = Thread(target=self.control_plane.listen_l2, args=(self.layer2.recv_ack, lambda : self.stop_threads, ))
            self.threads["L2_ACK_RCV"].start()

            self.threads["L4_ACK_RCV"] = Thread(target=self.control_plane.listen_l4, args=(self.layer4.recv_ack, lambda : self.stop_threads, ))
            self.threads["L4_ACK_RCV"].start()

        self.threads["STATE_RCV"] = Thread(target=self.control_plane.listen_cc, args=(self.handle_state, self.handle_get_state, lambda : self.stop_threads, ))
        self.threads["STATE_RCV"].start()

        if self.use_radio:
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
        if self.use_radio:
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
        print("Testing . . .")

        if self.use_radio:
            self.layer5.transmit=True

        start_time = time()
        # Wait for desired min iteration time to pass
        while time()-start_time<self.min_time:
            sleep(0.01)

        if self.use_radio:
            self.layer5.transmit=False

    def dji_takeoff(self):
        '''
        Method to takeoff Dji drone
        '''
        print("DJI Takeoff")
        os.system('~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/djiosdk-experiment-takeoff-and-stay ~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/UserConfig.txt --altitude '+str(self.my_alt))

    
    def dji_land(self):
        '''
        Method to land Dji drone
        '''
        print("DJI Landing")
        os.system('~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/djiosdk-experiment-land ~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/UserConfig.txt --altitude ' + str(self.my_alt))

    def run(self):
        '''
        Main Function to run the test
        '''
        
        try:
            self.start_threads()
            sleep(10)   # wait 10 sec for usrp to init

            if self.fly_drone:
                # takeoff 
                if self.is_dji:
                    self.dji_takeoff()

                else:
                    self.my_drone.handle_takeoff(abs(self.my_alt))
                    
            

            # iterate
            iteration_num = 0
            start_time = time()

            if not self.csv_in: # run NN
                while not self.stop_threads:
                    if  self.use_radio and self.layer4.log:
                        self.layer4.writer.writerow(["Iteration Number: " +str(iteration_num)])

                    # Goto State
                    self.handle_action()

                    # Broadcast State
                    self.state_loop()

                    # Begin Test
                    self.test_throughput()
                    
                    # Run Neural Network
                    if 'rly' in self.my_config.id:  # only run NN for relays
                        self.action = self.neural_net.run(self.state_buf)

                    # Log Data
                    if self.use_radio:
                        self.log_data([iteration_num]+self.state_buf+[self.layer4.n_ack])
                        self.layer4.n_ack = 0

                    # Reset State Buffer
                    self.state_buf = [None]*(2*self.num_nodes)
                    iteration_num += 1
            
            else: # actions from CSV
                print('~ ~ Reading From CSV ~ ~\n')
                for Exp_Ind, Loc_x, Loc_y, Loc_z, TxPower, sessRate, runTime, l2Ack, l2Time, l4Ack, l4Time, rtDelay, l2TxQueue, l4TxQueue, l2Sent in self.state_reader:
                    if Loc_y != 'Loc_y':
                        print('\n~~ Iteration', iteration_num, ' ~~')
                        if self.use_radio and self.layer4.log:
                            self.layer4.writer.writerow(["Iteration Number: " +str(iteration_num)])
                            # close to save data after each iteration. Reopen for faster writing
                            self.layer4.file.close()
                            self.layer4.file = open(os.path.expanduser(self.layer4.l4_csv_name), 'a', newline='')
                            self.layer4.writer = csv.writer(self.layer4.file)

                        self.loc_index = 0
                        self.pow_index = TxPower

                        # goto state
                        self.action_move([float(Loc_y), float(Loc_x)])
                        self.action_tx_gain(float(TxPower)/90)  

                        # Broadcast State
                        self.state_loop()

                        # Run throuhgput test
                        self.test_throughput()

                        # Log Data
                        if self.use_radio:
                            self.log_data([iteration_num]+self.state_buf+[self.layer4.n_ack, Loc_x, Loc_y, Loc_z])
                            if self.my_config.role == 'tx':
                                print("num acks:", self.layer4.n_ack, "time:", self.min_time) 
                            self.layer4.n_ack = 0

                        self.state_buf = [None]*(2*self.num_nodes)
                        
                        iteration_num += 1

            print("~ ~ Finished CSV Entries ~ ~")
            if self.use_timeout:    # optional continue testing for set amount of time
                while time()-start_time < (60*self.test_timeout):
                    print('\n~~ Iteration', iteration_num, ' ~~')
                    if self.use_radio and self.layer4.log:
                            self.layer4.writer.writerow(["Iteration Number: " +str(iteration_num)])
                    self.state_loop()
                    
                    self.test_throughput()

                    # Log Data
                    if self.use_radio:
                        self.log_data([iteration_num]+self.state_buf+[self.layer4.n_ack])
                        if self.my_config.role == 'tx':
                                print("num acks:", self.layer4.n_ack, "time:", self.min_time) 
                        self.layer4.n_ack = 0

                    self.state_buf = [None]*(2*self.num_nodes)
                    iteration_num += 1


            print("~ ~ Finished Successfully ~ ~")
            # Land
            if self.fly_drone:
                if self.is_dji:
                    self.dji_land()
                else:
                    self.my_drone.handle_landing()

            self.close_threads()
                
                   
        except Exception as e:
            print(e)
            # Land
            if self.fly_drone:
                if self.is_dji:
                    self.dji_land()
                else:
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
        if self.fly_drone and not self.is_dji:
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
        if self.use_radio and self.tx_optimization:
            self.layer1.set_tx_gain(gain)
        print('TX Gain:', gain)


def arguement_parser():
    '''
    Method to parse the input args
    :return: options
    '''
    parser = ArgumentParser()
    parser.add_argument('--index', type=int, default='', help='node index number')
    parser.add_argument('--num', type=int, default=6, help='number of nodes')
    parser.add_argument('--csv', type=str, default='y', help='states from csv (y/n)')
    parser.add_argument('--csv_path', type=str, default='~/Documents/usrp-utils/FromCsv/performance_data_', help='dir path to import csv')

    parser.add_argument('--f1', type=int, default=2000000000, help='freq 1')
    parser.add_argument('--f2', type=int, default=2100000000, help='freq 2')

    parser.add_argument('--tx_gain', type=float, default=0.8, help='normalized tx gain percentage')
    parser.add_argument('--rx_gain', type=float, default=0.95, help='normalized rx gian percentage')

    parser.add_argument('--fly_drone', type=str, default='y', help='Node UAV takesoff (y/n)')
    parser.add_argument('--wait', type=str, default='y', help='wait for other states before continuing (y/n)')
    parser.add_argument('--log', type=str, default='y', help='log data (y/n)')
    parser.add_argument('--file_name', type=str, default='log_', help='log data file name')

    parser.add_argument('--use_radio', type=str, default='y', help='use the usrp radios (y/n)')
    parser.add_argument('--use_timeout', type=str, default='y', help='use timeout (y/n)')
    parser.add_argument('--test_timeout', type=float, default=2.0, help='fixed test length (minutes)')
    parser.add_argument('--use_tx', type=str, default='y', help='optimize tx (y/n)')
    parser.add_argument('--is_sim', type=str, default='n', help='simulation or real drone (y/n)')
    parser.add_argument('--is_dji', type=str, default='n', help='dji drone? (y/n)')
    parser.add_argument('--global_home', type=str, default='42.47777625687639,-71.19357940183706,174.0', help='Global Home Location')
    
    parser.add_argument('--l1', type=str, default='n', help='layer 1 debug (y/n)')
    parser.add_argument('--l2', type=str, default='n', help='layer 2 debug (y/n)')
    parser.add_argument('--l3', type=str, default='n', help='layer 3 debug (y/n)')
    parser.add_argument('--l4', type=str, default='n', help='layer 4 debug (y/n)')
    return parser.parse_args()


def main():
    '''
    Main Method
    '''

    options = arguement_parser()
    print("STARTING", options.index)

    tx_gain = float(options.tx_gain)
    rx_gain = float(options.rx_gain)
    freq1 = int(options.f1)
    freq2 = int(options.f2)
    freq3 = 2.6e9

    dest1= Node_Config(pc_ip='192.168.10.101', usrp_ip='192.170.10.101', my_id='dest1', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", tx_gain=tx_gain, rx_gain=rx_gain , location_index=10) # TODO
    rly1 = Node_Config(pc_ip='192.168.10.102', usrp_ip='192.170.10.102', my_id='rly1', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", tx_gain=tx_gain, rx_gain=rx_gain ,location_index=24)
    src1 = Node_Config(pc_ip='192.168.10.103', usrp_ip='192.170.10.103', my_id='src1' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", tx_gain=tx_gain, rx_gain=rx_gain ,location_index=0)

    dest2= Node_Config(pc_ip='192.168.10.104', usrp_ip='192.170.10.104', my_id='dest2', role='rx', tx_freq=freq3, rx_freq=freq2, serial="", tx_gain=tx_gain, rx_gain=rx_gain ,location_index=120)
    rly2 = Node_Config(pc_ip='192.168.10.105', usrp_ip='192.170.10.105', my_id='rly2', role='rly', tx_freq=freq2, rx_freq=freq1, serial="", tx_gain=tx_gain, rx_gain=rx_gain ,location_index=70)
    src2 = Node_Config(pc_ip='192.168.10.106', usrp_ip='192.170.10.106', my_id='src2' , role='tx', tx_freq=freq1, rx_freq=freq3, serial="", tx_gain=tx_gain, rx_gain=rx_gain ,location_index=55)


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
    is_dji = (options.is_dji=='y' or options.is_dji=='Y')
    
    uav_node = UAV_Node(my_config, node_index=int(options.index), 
                                l1_debug=(options.l1=='y' or options.l1 == 'Y'), 
                                l2_debug=(options.l2=='y' or options.l2 == 'Y'), 
                                l3_debug=(options.l3=='y' or options.l3 == 'Y'), 
                                l4_debug=(options.l4=='y' or options.l4 == 'Y'), 
                                csv_in=(options.csv=='y' or options.csv=='Y'), 
                                fly_drone=fly_drone, 
                                wait=(options.wait=='y' or options.wait=='Y'),
                                use_radio=(options.use_radio=='y' or options.use_radio=='Y'),
                                tx_optimization=(options.use_tx=='y' or options.use_tx=='Y'),
                                is_sim=(options.is_sim=='y' or options.is_sim=='y'),
                                is_dji=is_dji,
                                global_home=[float(ii) for ii in options.global_home.split(',')],
                                use_timeout=(options.use_timeout=='y' or options.use_timeout=='y'),
                                test_timeout=float(options.test_timeout),
                                log=(options.log=='y' or options.log=='y'),
                                log_base_name="~/Documents/usrp-utils/Logs/"+options.file_name,
                                num_nodes=int(options.num)
                                )
    try:
        uav_node.run()
    except Exception as e:
        print(e)
        if fly_drone:
            if is_dji:
                print("landing Dji")
                os.system('~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/djiosdk-experiment-land ~/Documents/usrp-utils/dji_onboard_sdk_primitives/build/bin/UserConfig.txt --altitude ' + str(self.my_alt))
            else:
                uav_node.my_drone.handle_landing()
        uav_node.close_threads()
        exit(0)


if __name__ == '__main__':
    main()