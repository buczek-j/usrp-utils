#!/usr/bin/env python3


# external libraries
from threading import Thread
from time import sleep, time
from math import ceil
from subprocess import Popen, PIPE
from signal import SIGTERM
from os import killpg

import random, string, struct

# user made libraries
from LayerStack import Control_Plane, Layer1, Layer2, Layer3, Layer4, Network_Layer
from Node_Config import Node_Config

class Simple_Node(Network_Layer.Network_Layer):
    def __init__(self, my_config):
        '''
        Test node class for network layer stack
        :param my_config: Node_Config class object
        :param serial: string for the usrp serial number
        '''
        Network_Layer.Network_Layer.__init__(self, "application_layer")
        self.my_config = my_config
        self.stop_threads = False
        self.transmit = False

        self.threads = {}
        self.subproccesses = []

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
        self.init_layers(upper=None, lower=self.layer4)

        

        print("~ ~ Initialization Complete ~ ~")

    def tx_test(self):
        tspt_rate = 20000			# Initial tansport layer rate in bps
        size = 5*128*2
        header = 42
        payload = bytes((size - header) * random.choice(string.digits), "utf-8")
        pktno_l4 = 0
        l4_pkts_to_send = 10000
        n_sent = 0

        l4_maximum_rate = tspt_rate/8 	    # bps -> [Bps]
        max_pkt_per_sec = max(1,int(ceil(l4_maximum_rate/size)))

        while not self.stop_threads:
            if self.transmit:
                sleep(1)

                if pktno_l4 == l4_pkts_to_send:
                        print("Max number of packets sent")
                        break

                for counter_packet in range(int(max_pkt_per_sec)):
                    time_stamp = time()
                    packet = struct.pack('l', pktno_l4)  + bytes(self.my_config.pc_ip, "utf-8") + bytes(self.my_config.dest.pc_ip, "utf-8") +  struct.pack('d', time_stamp) + payload # 42 bytes added
                    
                    self.down_queue.put(packet, True)
                
                    n_sent += 1
                    pktno_l4 += 1
                    

    def rx_test(self):
        while not self.stop_threads:
            msg = self.prev_up_queue.get(True)
            print(msg)


    def start_threads(self):
        '''
        Method to start all of the threads 
        '''
        self.stop_threads = False
        print("~ ~ Starting Threads ~ ~")
        # Initialize threads
        self.threads["control_layer"] = Thread(target=self.control_plane.listening_socket, args=(self.layer2.recv_ack, self.layer4.recv_ack, lambda : self.stop_threads, ))
        self.threads["control_layer"].start()

        for layer in [self.layer1, self.layer2, self.layer3, self.layer4]:
            self.threads[layer.layer_name + "_pass_up"] = Thread(target=layer.pass_up, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_down"] = Thread(target=layer.pass_down, args=(lambda : self.stop_threads,))
            self.threads[layer.layer_name + "_pass_up"].start()
            self.threads[layer.layer_name + "_pass_down"].start() 

        # self.threads["usrp_block"] = Thread(target=Layer1.ofdm_tranceiver_thread, args=(lambda : self.stop_threads, self.my_config.serial, self.my_config.usrp_in_port, self.my_config.usrp_out_port, self.my_config.rx_bw, self.my_config.rx_freq, self.my_config.rx_gain, self.my_config.tx_bw, self.my_config.tx_freq, self.my_config.tx_gain,))
        # self.threads["usrp_block"].start()

        self.subproccesses.append(Popen('python3 LayerStack/L1_protocols/TRX_ODFM_USRP.py '+str(self.my_config.get_tranceiver_args()), stdout=PIPE, shell=True))

        if self.my_config.role == 'tx':
            self.threads['tx_thread'] = Thread(target=self.tx_test, args=())
            self.threads['tx_thread'].start()

        elif self.my_config.role == 'rx':
            self.threads['rx_thread'] = Thread(target=self.rx_test, args=())
            self.threads['rx_thread'].start()

        print("~ ~ Threads all running ~ ~")


    def close_threads(self):
        '''
        Method to close all of the threads and subprocesses
        '''
        self.stop_threads = True
        print("~ ~ Closing Threads ~ ~")
        for thread in self.threads:
            try:
                sleep(4)
                thread.join(2)
            except:
                pass

        for proc in self.subproccesses:
            try:
                killpg(proc.pgid, SIGTERM)
            except:
                pass
            
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

        except Exception as e:		
            print(e)
            self.stop_threads=True
            self.close_threads()
            return 0

def main():
    '''
    Main method
    '''
    id_list = ['dest1', 'src1']
    role_list = ['rx', 'tx']
    udp_port_list = [9000, 9000]
    usrp_ports = [['55555','55556'], ['55555','55556']]
    wifi_ip_list = ['10.110.149.19', '10.110.144.55']#['192.168.10.', '192.168.10.']
    usrp_ip_list = ['192.170.10.19', '192.170.10.20']
    tx_gain = [0.8, 0.8]
    rx_gain = [0.8, 0.8]
    tx_freq = [2e9, 2.4e9]
    rx_freq = [2.4e9, 2e9]
    tx_bw = [0.5e6, 0.5e6]
    rx_bw = [0.5e6, 0.5e6]
    serial_list = ["31C9261", "31C9237"]

    nodes = []
    for ii in range(len(id_list)):
        nodes.append(Node_Config(
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
        ))
    nodes[0].configure_hops(nodes[0], nodes[1], nodes[1], None)
    nodes[1].configure_hops(nodes[0], nodes[1], None, nodes[1])
    
    simple_node = Simple_Node(nodes[1])
    try:
        simple_node.run()
    except:
        simple_node.close_threads()
        exit(0)
    
if __name__ == "__main__":
    main()