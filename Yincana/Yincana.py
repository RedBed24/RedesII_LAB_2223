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

puerto = 25565

mensajeAEnviar = f"{puerto} {identifier}".encode()
identificadorUpper = identifier.upper().encode()

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidorUDP:
	servidorUDP.bind(("", puerto))

	servidorUDP.sendto(mensajeAEnviar, ("yinkana", 4000))

	msg, sender = servidorUDP.recvfrom(DEFAULT_PACKET_SIZE)
	print(f"{msg.decode()}")

	if msg == b"upper-code?":

		servidorUDP.sendto(identificadorUpper, sender)

		msg = servidorUDP.recv(DEFAULT_PACKET_SIZE)
		#print(f"{msg.decode()}")

# Hito 2

def obtenerCuentaPalabras(TCPsocket, maximum, wordSeparators):
	"""Devuelve bytes que contienen la cuenta de los caracteres de las palabras (separadas por alguno de los caracteres especificados en) que se obtienen del socket, que debe de estar previamente conectado"""

	suma = 0
	bytesCuentas = b""

	carateresEnEstaPalabra = 0

	# obtenemos el número ascii asociado a los diferentes separadores especificados
	wordSeparators = [ord(i) for i in wordSeparators]

	while suma < maximum:
		wordSequence = TCPsocket.recv(DEFAULT_PACKET_SIZE)
		i = 0
		while i < len(wordSequence) and suma < maximum:
			if wordSequence[i] not in wordSeparators:
				carateresEnEstaPalabra += 1
			else:
				suma += carateresEnEstaPalabra
				bytesCuentas += f"{carateresEnEstaPalabra} ".encode()
				carateresEnEstaPalabra = 0
			i += 1
	
	return bytesCuentas


identifier = msg.decode().split("\n")[0].split(":")[1]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito2:
	servidorTCPHito2.connect(("node1", 3010))

	bytesCuentas = obtenerCuentaPalabras(servidorTCPHito2, 1000, [" "])

	servidorTCPHito2.send(f"{identifier} {bytesCuentas.decode()}--".encode())

	# obtenemos el último mensaje enviado con datos, el cual se espera que sea el enunciado
	msg = servidorTCPHito2.recv(DEFAULT_PACKET_SIZE)
	while len(msg) > 0:
		previous = msg
		msg = servidorTCPHito2.recv(DEFAULT_PACKET_SIZE)

	print(f"{previous.decode()}")
	
# Hito 3

identifier = previous.decode().split("\n")[0].split(":")[1]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito3:
	servidorTCPHito3.connect(("node1", 5501))

	sumaMaxima = 1200
	suma = 0
	palabra = None
	while suma < sumaMaxima and palabra == None:
		msg = servidorTCPHito3.recv(DEFAULT_PACKET_SIZE)

		divisiones = msg.decode().split(" ")

		for token in divisiones:
			try:
				suma +=	int(token)
			except ValueError as ve:
				suma += 1
				if suma > sumaMaxima:
					palabra = token
					break

	servidorTCPHito3.send(f"{palabra} {identifier}".encode())

	msg = servidorTCPHito3.recv(DEFAULT_PACKET_SIZE)
	while len(msg) > 0:
		previous = msg
		msg = servidorTCPHito3.recv(DEFAULT_PACKET_SIZE)

	print(f"{previous.decode()}")

# Hito 4

