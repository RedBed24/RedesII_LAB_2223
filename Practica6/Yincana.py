#!/usr/bin/python3

import socket
import os

DEFAULT_PACKET_SIZE = 1024

with socket.socket() as socketRawHito0:
	# nos conectamos con la yinkana
	socketRawHito0.connect(("yinkana", 2000))

	# recibimos lo que nos envíe
	msg = socketRawHito0.recv(DEFAULT_PACKET_SIZE)

	# vemos qué nos ha enviado
	#print(f"{msg.decode()}")

	# Aquí entre medias habrá que hacer el código

	# le enviamos lo que nos pide, nuestro nombre de usuario
	socketRawHito0.send(os.environ["USER"].encode())

	# obtenemos las instrucciones de la siguiente
	msg = socketRawHito0.recv(DEFAULT_PACKET_SIZE)

	#print(f"{msg.decode()}")

# Hito 1

# Esto pasa a str
respuesta = msg.decode()
# Obtenemos el campo de identificador, primera línea, después de los dos puntos
identifier = respuesta.split("\n")[0].split(":")[1]

identificadorBytes = msg[11:31]

puerto = 25565

# FIXME: cualquiera de estos devuelve bytes, como es de esperar
mensajeAEnviar = bytes(f"{puerto} {identifier}", "ascii")
#mensajeAEnviar = bytes(f"{puerto} {identifier}", "UTF-8")
#mensajeAEnviar = f"{puerto} {identifier}".encode()
#mensajeAEnviar = f"{puerto} {identifier}".encode("UTF-8")
#mensajeAEnviar = b"25565 " + identificadorBytes

print(mensajeAEnviar)

identificadorUpper = identifier.upper().encode()
print(identificadorUpper)

HITO1 = ("yinkana", 4000)
#HITO1 = ("node1", 4000)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidorUDP:
	servidorUDP.bind(("", puerto))

	#servidorUDP.connect(HITO1)
	#servidorUDP.send(mensajeAEnviar)

	servidorUDP.sendto(mensajeAEnviar, HITO1)

	msg = servidorUDP.recv(DEFAULT_PACKET_SIZE)
	print(f"{msg.decode()}")

	if msg == b"upper-code?":

		# FIXME: El hito1 no es capaz de recibir el mensaje?
		#servidorUDP.sendto(identificadorBytes, HITO1)
		servidorUDP.sendto(identificadorUpper, HITO1)
		#servidorUDP.sendto(b"NoNeSeNsE12345678924", HITO1)

		msg = servidorUDP.recv(DEFAULT_PACKET_SIZE)
		print(f"{msg.decode()}")

