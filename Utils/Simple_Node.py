#!/usr/bin/env python3


# external libraries
from threading import Thread
from time import sleep
import random, string

# user made libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Network_Layer


class Simple_Node(Network_Layer):
    def __init__(self, my_config, serial="31C9237"):
        '''
        Test node class for network layer stack
        :param my_config: Node_Config class object
        :param serial: string for the usrp serial number
        '''
        Network_Layer.__init__(self, "application_layer")
        self.my_config = my_config
        self.stop_threads = False
        self.transmit = False

        self.threads = {}

        # Initalize Network Stack
        self.control_plane = Control_Plane.Control_Plane(my_config.pc_ip)
        self.layer4 = Layer4.Layer4(self.my_config, self.control_plane.send_l4_ack)
        self.layer3 = Layer3.Layer3(self.my_config)
        self.layer2 = Layer2.Layer2(self.my_config.usrp_ip, send_ack=self.control_plane.send_l2_ack)
        self.layer1 = Layer1.Layer1()
        
        # Link layers together
        self.layer1.init_layers(upper=self.layer2, lower=None)
        self.layer2.init_layers(upper=self.layer3, lower=self.layer1)
        self.layer3.init_layers(upper=self.layer4, lower=self.layer2)
        self.layer4.init_layers(upper=self, lower=self.layer3)  # link l4 to this class object

        # Initialize threads
        self.threads["control_layer"] = Thread(target=self.control_plane.listening_socket, args=(self.layer2.recv_ack, self.layer4.recv_ack, lambda : self.stop_threads, ))

        for layer in [self.layer1, self.layer2, self.layer3, self.layer4]:
            self.threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_down"] = Thread(target=layer.pass_down, args=(lambda : self.stop_threads,))

        self.threads["usrp_block"] = Thread(target=Layer1.ofdm_tranceiver_thread, args=(lambda : self.stop_threads, serial, ))

        if self.my_config.role == 'tx':
            self.threads['tx_thread'] = Thread(target=self.tx_test, args=())

        elif self.my_config.role == 'rx':
            self.threads['rx_thread'] = Thread(target=self.tx_test, args=())
        print("~ ~ Initialization Complete ~ ~")

    def tx_test(self):
        size = 5*128*2
        header = 42
        payload = bytes((size - header) * random.choice(string.digits), "utf-8")

        while not self.stop_threads:
            if self.transmit:
    
    def rx_test(self):
        while not self.stop_threads:
            


    def start_threads(self):
        '''
        Method to start all of the threads 
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~")
        for thread in self.threads:
            thread.start()
        print("~ ~ Threads all running ~ ~")

    def close_threads(self):
        '''
        Method to close all of the threads
        '''
        self.stop_threads = True
        print("~ ~ Closing Threads ~ ~")
        for thread in self.threads:
            sleep(4)
            thread.join(2)
            
    def run(self):
        '''
        Main node method
        '''
        try:
            # setup
            self.start_threads()
            sleep(10)                   # startup time

            # run
            print("~ ~ Starting Transmission ~ ~")
            self.transmit = True
            sleep(30)                   # run time

            # close
            self.transmit = False
            self.stop_threads = True
            self.close_threads()
            return 0

        except KeyboardInterrupt:		
            self.stop_threads=True
            self.close_threads()
            return 0

