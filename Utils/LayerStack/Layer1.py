#!/usr/bin/env python3

'''
Layer 1 object: Physical layer 
'''

from L1_protocols.TRX_ODFM_USRP import TRX_ODFM_USRP
from Network_Layer import Network_Layer
import signal, time, sys, pmt, zmq
from numpy import byte, frombuffer

def ofdm_tranceiver_thread(stop, input_port_num="55555", output_port_num="55556", rx_bw=0.5e6, rx_freq=2e9, rx_gain=0.8, serial_num="31C9237", tx_bw=0.5e6, tx_freq=1e9, tx_gain=0.8):
    '''
    Method to start a odfm tranceiver thread
    :param stop: function returning true/false to stop the tranceiver thread
    :param input_port_num: string for the input tcp port
    :param output_port_num: string for the output tcp port
    :param rx_bw: int for the receiver bandwidth in Hz
    :param rx_freq: int for the receiver center frequency in Hz
    :param rx_gain: float for the realative receiver gain (0.0 to 1.0)
    :param serial_num: string for the radio serial number
    :param tx_bw: int for the transmitter bandwidth in Hz
    :param tx_freq: int for  the transmitter center frequency
    :param tx_gain float for the relative transmitter gain (0.0 to 1.0)
    '''
    tb = TRX_ODFM_USRP(input_port_num=str(input_port_num), serial_num=str(serial_num), output_port_num=str(output_port_num), rx_bw=rx_bw, rx_freq=rx_freq, rx_gain=rx_gain, tx_bw=tx_bw, tx_freq=tx_freq, tx_gain=tx_gain)
    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)
    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()
    while not stop():
        time.sleep(0.5)
    tb.stop()
    tb.wait()
     

class Layer1(Network_Layer):
    def __init__(self, input_port='55555', output_port='55556'):
        '''
        Method to send and receive bytes via uarp radios through tcp connection to GNU radio object
        :param input_port: string for the input tcp port of the GNU radio object
        :param output_port: string for the output port of the GNU radio object 
        '''
        Network_Layer.__init__(self, "layer_1")

        send_context = zmq.Context()
        self.send_socket = send_context.socket(zmq.PUB)
        self.send_socket.bind("tcp://127.0.0.1:"+str(input_port))

        recv_context = zmq.Context()
        self.recv_socket = recv_context.socket(zmq.SUB)
        self.recv_socket.connect("tcp://127.0.0.1:"+str(output_port))
        self.recv_socket.setsockopt(zmq.SUBSCRIBE, b'')
    
    def pass_up(self, stop):
        '''
        Method to pass bytes up to Layer 2
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            if self.recv_socket.poll(10) != 0:      # check if msg in socket
                msg = self.recv_socket.recv()
                received_pkt = frombuffer(msg, dtype=byte, count=-1)
                self.up_queue.put(received_pkt, True)

    def pass_down(self, stop):
        '''
        Method to pass bytes to GNU radio object
        :param stop: function returning true/false to stop the thread
        '''
        while not stop():
            msg = self.prev_down_queue.get(True)    #  get message from previous layer down queue
            self.send_socket.send(msg)

