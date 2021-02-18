

# msg1 = b'192.168.0.103'
# msg2 = b'192.168.0.10'
# msg3 = b'192.168.0.9'

# for msg in [msg1, msg2, msg3]:
#     index=0
#     for ii in range(4):
#         if msg[len(msg)-(ii+1)] == 46:
#             index = len(msg)-(ii)
#             break

#     print(msg[index:])
#     print(type(msg))

import random, string
size = 5*128*2
header = 42
payload = bytes((size - header) * random.choice(string.digits), "utf-8")
print(payload)
print(type(payload))
print(len(payload)+header)