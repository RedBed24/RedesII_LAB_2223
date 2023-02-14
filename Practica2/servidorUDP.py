
from socket import *

#             IPv4     UDP
sock = socket(AF_INET, SOCK_DGRAM)

#  nos ponemos a escuchar
#  cualquier IP, puerto
sock.bind(('', 12345))

while (True):
    # recibimos el mensaje y el cliente
    # como mucho, recibimos 1024 Bytes
    response, client = sock.recvfrom(1024)
    print(client, '>', response.decode())

    if response.decode() == "bye":
        break

    msgSend = input()

    sock.sendto(msgSend.encode(), client)

    if msgSend == "bye":
        break

sock.close()

