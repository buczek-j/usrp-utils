#!/usr/bin/env python3

'''
Network layer parent class. Defines the basic structure of the stack
'''

from threading import Thread, Event
import queue
class Network_Layer(object):
	def __init__(self, layer_name, window=None):
		'''
		Class to define the the basic structure of a network layer
		'''
		self.layer_name = layer_name
		self.up_queue = queue.Queue(1024*1000)
		self.down_queue = queue.Queue(1024*1000)
		self.window = window

	def init_upper_queue(self, upper_layer):
		self.upper_queue = upper_layer.up_queue

	def init_lower_queue(self, lower_layer):
		self.lower_queue = lower_layer.down_queue						

	def up_fuction(self, stop):
		'''
		Method that continuously runs. receives up_packet from pass_up and decides based on the 
		return of pass_up whether to put the packet in upper_queue(upper layer) or down_queue (current layer)
		:param stop: function returning True/False to terminate the thread
		'''
		while not stop() :
			#function that assemble the packet to be sent up/to down_queue. this function will pull packets from the queue
			up_packet,passing_decision = self.pass_up(stop)  #previous_hop_socket check
			if passing_decision == 1:
				self.upper_queue.put(up_packet, True)
			elif  passing_decision == 0:
				self.down_queue.put(up_packet,True)	
			else:
				pass #this is for mac layers not having a upper queue 	
		print("\n" + self.__class__.__name__ +  " up_fuction TERMINATE\n")

	def down_function_pool(self, stop):
		'''
		Method that continuously runs and gets the down_packet from down_queue and passes it to pass_down 
		:param stop: function returning True/False to terminate the thread
		'''
		self.thread_pool = []
		self.dict_thread_signal = {}
		self.dict_pktno_thread = {}		
		for i in range(self.window):			
			self.thread_pool.append(Thread(target = self.running_down_function, args = (i, lambda : stop, ))) #call a thread running 
			self.dict_thread_signal[self.thread_pool[i].ident] = Event()  #put a signal			
			self.thread_pool[-1].start()	

	def running_down_function(self,index, stop):	
		while not stop():
			self.down_function(index, stop)
		print("\n" + self.__class__.__name__ + " running_down_function TERMINATE\n")
			
	def down_function(self, index, stop):
		#fucntions that fragments the packet and put each of them down. the function is in charge of putting all the fragments in the queue
		down_packet = self.down_queue.get(True)
		self.pass_down(down_packet,index, stop) 
		
	def pass_up(self, stop):
		'''
		pass up to be overritten by child classes
		'''
		return None, None

	def pass_down(self, down_pkt, index, stop):
		'''
		pass down to be overritten by child class
		'''