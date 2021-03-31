#!/usr/bin/env python3

'''
Node_Config object
'''

class Node_Config():
	def __init__(self, pc_ip='', usrp_ip='', my_id='src0', role='tx', listen_port=55557, usrp_ports=['55555', '55556'], rx_bw=500e3, rx_freq=2e9, rx_gain=0.5, tx_bw=500e3, tx_freq=2.1e9, tx_gain=0.5, serial=""):
		'''
		:param pc_ip: string of ip address of the pc for the node
		:param usrp_ip: string of ip address for the usrp of the node
		:param my_id: string if the name of the node ex: 'src1'
		:param role: string of the role of the node ex: 'tx'
		:param listen_port: int for the port to listen for udp acks and state messages
		:param usrp_ports: array of strings for the usrp connection ports [tx, rx]
		:param rx_bw: int for the receiver bandwidth in Hz
		:param rx_rf_freq: int for the receiver center frequency in Hz
		:param rx_gain: float for the rx normalized gain (0.0-1.0)
		:param tx_bw: int for the transmitter bandwidth in Hz
		:param tx_rf_freq: int for the transmitter center frequency in Hz
		:param tx_gain: float for the tx normalized gain (0.0-1.0)
		:param  serial: string for the USRP device serial number, if left as "" the first usrp found will be used
		'''
		self. pc_ip = pc_ip
		self.usrp_ip = usrp_ip
		self.id = my_id
		self.role = role
		self.listen_port = listen_port 
		self.usrp_in_port = usrp_ports[0]
		self.usrp_out_port = usrp_ports[1]
		self.rx_bw = int(rx_bw)
		self.rx_freq = int(rx_freq)
		self.rx_gain=rx_gain
		self.tx_bw = int(tx_bw)
		self.tx_freq = int(tx_freq)
		self.tx_gain = tx_gain
		self.serial = serial

	def configure_hops(self, src, dest, next_hop, prev_hop):
		'''
		Method to configure the hops of the network
		:param src: Node_Config Object of the source
		:param dest: Node_Config Object of the destination
		:param next_hop: Node_Config Object of the next hop
		:param prev_hop: Node_Config Object of the previous hop
		'''
		self.src = src
		self.dest = dest

		if next_hop == None:	# if node, set to all '-1'
			self.next_hop = None
		else:
			self.next_hop = next_hop

		if prev_hop == None:
			self.prev_hop = None
		else:
			self.prev_hop = prev_hop

	def get_tranceiver_args(self):
		'''
		Method to return string of usrp tranceiver args
		:return: string with usrp tranceiver args for TRX_ODFM_USRP.py 
		'''
		return '--serial "'+self.serial +'" --rx_bw ' + str(self.rx_bw) + ' --rx_freq ' + str(self.rx_freq) + ' --rx_gain ' + str(self.rx_gain) + ' --tx_bw ' + str(self.tx_bw)  + ' --tx_freq ' + str(self.tx_freq) + ' --tx_gain ' + str(self.tx_gain) + ' --input_port "'+self.usrp_in_port + '" --output_port "' + self.usrp_out_port + '"'
