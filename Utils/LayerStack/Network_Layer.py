#!/usr/bin/env python3

'''
Network layer parent class. Defines the basic structure of the stack
'''
IP_LEN = 20

import  struct
from queue import Queue
class Network_Layer():
	def __init__(self, layer_name, window=None, debug=False):
		'''
		Class to define the the basic structure of a network layer
		:param layer_name: sting for the layer name
		:param window: int for the number of l2 windows to open TODO
		:param debug: bool for debug console outputs 
		'''
		self.layer_name = layer_name
		self.up_queue = Queue(1024*1000)
		self.down_queue = Queue(1024*1000)
		self.window = window
		self.debug = debug

	def init_layers(self, upper=None, lower=None):
		'''
		Method to initialize the queues between layers
		:param upper: Network_Layer object for the next upper layer
		:param lower: Network_Layer object for the next lower layer
		'''
		if upper:
			self.prev_down_queue = upper.down_queue
		else:
			self.prev_down_queue = None
		
		if lower:
			self.prev_up_queue = lower.up_queue
		else:
			self.prev_up_queue = Queue(1024*1000)	# needed for l4 layer relay

		
	def pass_up(self, stop):
		'''
		pass up to be overritten by child classes
		'''
		return None, None

	def pass_down(self, stop):
		'''
		pass down to be overritten by child class
		'''

	def pad(self, ip, length=20):
		'''
		Method to pad an IP in bytes to a length 
		:param ip: bytes for the ip address to pad
		:param length: int for the desired length
		:return: bytes for the padded ip
		'''
		padded_ip = ip
		for ii in range(length-len(ip)):
			padded_ip = padded_ip + struct.pack('x')	# add struct pad byte
		return padded_ip

	def unpad(self, padded_ip):
		'''
		Method to uppad an IP in bytes from a length of 20 to its actual values
		:param padded_ip: bytes of ip address with pad bytes
		:return: bytes of ip address without pad bytes
		'''
		num = padded_ip.count(struct.pack('x'))	# count the number of pad bytes
		return padded_ip[:-num]