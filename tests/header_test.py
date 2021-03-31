from struct import pack, unpack
from time import time

# Transport Layer
trans_msg = "test123"
trans_pkt_no = 0
trans_src_port = 5
trans_dest_port = 6
trans_len = len(trans_msg) + 24
timestamp = time()
trans_ack_no = 0


trans_header=b''
trans_header = trans_header + pack("I", trans_pkt_no)
trans_header = trans_header + pack("H", trans_src_port)
trans_header = trans_header + pack("H", trans_dest_port)
trans_header = trans_header + pack("I", trans_len)
trans_header = trans_header + pack("d", timestamp)
trans_header = trans_header + pack("I", trans_ack_no)

print("TRANS", len(trans_header), trans_header)
print(unpack('I', trans_header[0:4])[0],end=', ')
print(unpack('H', trans_header[4:6])[0],end=', ')
print(unpack('H', trans_header[6:8])[0],end=', ')
print(unpack('I', trans_header[8:12])[0],end=', ')
print(unpack('d', trans_header[12:20])[0],end=', ')
print(unpack('I', trans_header[20:24])[0],end=', ')
print('\n')

# Routing Layer
routing_optional = b''
routing_header_len = 16 + len(routing_optional)
routing_pkt_len = routing_header_len + trans_len
routing_flag = 0
routing_source = '192.160.10.103'
routing_dest = '192.168.10.101'


routing_header = b''
routing_header = routing_header + pack("H", routing_header_len)
routing_header = routing_header + pack("I", routing_pkt_len)
routing_header = routing_header + pack("H", routing_flag)

for entry in routing_dest.split('.'):
    routing_header = routing_header + pack("B", int(entry))

for entry in routing_source.split('.'):
    routing_header = routing_header + pack("B", int(entry))

routing_header = routing_header + routing_optional

print("Routing", len(routing_header), routing_header)
print(unpack('H', routing_header[0:2])[0],end=', ')
print(unpack('I', routing_header[2:6])[0],end=', ')
print(unpack('H', routing_header[6:8])[0],end=', ')
for ii in range(4):
    print(int(routing_header[8+ii]), end='.')
print('', end=', ')

for ii in range(4):
    print(int(routing_header[12+ii]), end='.')
print('', end=', ')

print(routing_header[16:routing_header_len])
print('\n')



# Datalinnk Layer
datalink_packet_num=1
datalink_dest = "0.0.192.170.10.101"
datalink_src = "0.0.192.170.10.103"
datalink_ack_no=0


data_header = b''
data_header = data_header + pack('H', datalink_packet_num)

for entry in datalink_dest.split('.'):
    data_header = data_header + pack('B', int(entry))

for entry in datalink_src.split('.'):
    data_header = data_header + pack('B', int(entry))

data_header = data_header + pack('H', datalink_ack_no)
print("Datalink", len(data_header), data_header)


print(unpack('H', data_header[0:2])[0],end=', ')
for ii in range(6):
    print(int(data_header[2+ii]), end='.')
print('', end=', ')

for ii in range(6):
    print(int(data_header[8+ii]), end='.')
print('', end=', ')

print(unpack('H', data_header[14:16])[0])
print('\n')


total = data_header + routing_header + trans_header + trans_msg.encode('utf-8')
print(len(total), len(data_header)+routing_pkt_len)