#!/usr/bin/env python3

'''
Layer 1 object: Physical layer 
'''

from LayerStack.L1_protocols.TRX_ODFM_USRP import TRX_ODFM_USRP
from LayerStack.Network_Layer import Network_Layer
import signal, time, sys, pmt, zmq, os
from numpy import byte, frombuffer

   
class Layer1(Network_Layer):
    def __init__(self, mynode, input_port='55555', output_port='55556', debug=False):
        '''
        Object to send and receive bytes via uarp radios through tcp connections to GNU radio object
        :param mynode: Node_Config object for the current node USRP configuration information
        :param input_port: string for the input tcp port of the GNU radio object
        :param output_port: string for the output port of the GNU radio object 
        '''
        Network_Layer.__init__(self, "layer_1", debug=debug)

        send_context = zmq.Context()
        self.send_socket = send_context.socket(zmq.PUB)
        self.send_socket.bind("tcp://127.0.0.1:"+str(input_port))

        recv_context = zmq.Context()
        self.recv_socket = recv_context.socket(zmq.SUB)
        self.recv_socket.connect("tcp://127.0.0.1:"+str(output_port))
        self.recv_socket.setsockopt(zmq.SUBSCRIBE, b'')

        # measurement
        self.n_sent = 0
        self.n_recv = 0

        # USRP Object
        # self.tb = TRX_ODFM_USRP(input_port_num=str(input_port), serial_num=str(mynode.serial), output_port_num=str(output_port), rx_bw=int(mynode.rx_bw), rx_freq=int(mynode.rx_freq), rx_gain=mynode.rx_gain, tx_bw=int(mynode.tx_bw), tx_freq=int(mynode.tx_freq), tx_gain=mynode.tx_gain)
        # def sig_handler(sig=None, frame=None):
        #     self.tb.stop()
        #     self.tb.wait()

        #     sys.exit(0)
        # signal.signal(signal.SIGINT, sig_handler)
        # signal.signal(signal.SIGTERM, sig_handler)

        # self.tb.start()
    

    def set_rx_gain(self, gain):
        '''
        Method to adjust the USRP rx gain
        :param gain: float for the new normalized  gain (0.0-1.0)
        '''
        if gain <= 1.0:
            self.tb.uhd_usrp_source_0.set_normalized_gain(gain, 0)
        else:
            print('Invalid Gain', gain)


    def set_tx_gain(self, gain):
        '''
        Method to adjust the USRP tx gain
        :param gain: float for the new normalized  gain (0.0-1.0)
        '''
        if gain <= 1.0:
            self.tb.uhd_usrp_sink_0.set_normalized_gain(gain, 0)
        else:
            print('Invalid Gain', gain)
    
    
    def pass_up(self, stop):
        '''
        Method to pass bytes up to Layer 2
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            if self.recv_socket.poll(10) != 0:      # check if msg in socket
                msg = self.recv_socket.recv()
                received_pkt = frombuffer(msg, dtype=byte, count=-1)
                self.up_queue.put(received_pkt.tobytes(), True)
                self.n_recv = self.n_recv + len(received_pkt.tobytes())
                received_pkt=None


    def pass_down(self, stop):
        '''
        Method to pass bytes to GNU radio object
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            msg = self.prev_down_queue.get(True)    #  get message from previous layer down queue
            self.send_socket.send(msg)
            self.n_sent = self.n_sent + len(msg)

