
from socket import *

#             IPv4     UDP
sock = socket(AF_INET, SOCK_DGRAM)
#            Mensaje codifi    tupla (addr, puerto)
sock.sendto("hello".encode(), ('localhost', 12345))

sock.close()

