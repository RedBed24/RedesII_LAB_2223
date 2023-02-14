
from socket import *

#             IPv4     UDP
sock = socket(AF_INET, SOCK_DGRAM)

#  nos ponemos a escuchar
#  cualquier IP, puerto
sock.bind(('', 12345))

# recibimos el mensaje y el cliente
# como mucho, recibimos 1024 Bytes
msg, client = sock.recvfrom(1024)

print(msg.decode(), client)

sock.close()

