
from socket import *

#             IPv4     UDP
sock = socket(AF_INET, SOCK_DGRAM)

server = ('localhost', 12345)

while(True):
    msgSend = input()

    #            Mensaje codifi    tupla (addr, puerto)
    sock.sendto(msgSend.encode(), server)

    if msgSend == "bye":
        break

    # server2 == server
    response, server2 = sock.recvfrom(1024)
    print(server2, '>', response.decode())

    if response.decode() == "bye":
        break

sock.close()

