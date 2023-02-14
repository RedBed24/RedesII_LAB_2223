
from socket import *

#             IPv4     UDP
sock = socket(AF_INET, SOCK_DGRAM)

server = ('localhost', 12345)

#            Mensaje codifi    tupla (addr, puerto)
sock.sendto("hello".encode(), server)

msg, server2 = sock.recvfrom(1024)

# server2 == server

print(msg.decode())

sock.close()

