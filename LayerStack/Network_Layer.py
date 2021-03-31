#!/usr/bin/env python3

'''
Network layer parent class. Defines the basic structure of the stack
'''
IP_LEN = 20

import  struct
from queue import Queue

def addr_to_bytes(addr):
	'''
	method to transform a human-readable address to byte form
	:param addr: string for the address to parse
	:return byte array of the address
	'''
	temp = b''
	for entry in addr.split('.'):
		temp = temp + struct.pack("B", int(entry))
	return temp
	
class Network_Layer():
	def __init__(self, layer_name, window=None, debug=False):
		'''
		Class to define the the basic structure of a network layer
		:param layer_name: sting for the layer name
		:param window: int for the number of l2 windows to open 
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
			self.prev_down_queue = Queue(1024*1000)
		
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

