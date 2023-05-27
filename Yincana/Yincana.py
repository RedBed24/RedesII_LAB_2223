#!/usr/bin/python3

"""Yicana"""
__author__ = "Samuel Espejo"


import socket
import os


# Definir algunas "constantes"

DEFAULT_PACKET_SIZE : int = 1024

VERBOSE : bool = True
DEBUG : bool = False


def ObtainIdentifier(msg : bytes) -> bytes:
	"""
	Función ayudante que devuelve el identificador encontrado en el mensaje

	Parameters:
		msg: Bytes que deben ser del estilo: b".*:.*\\n.*" La primera instancia del patrón contiene el identificador

	Returns: El identificador (en bytes), se encuentra entre b":" y b"\\n" del patrón encontrado
	"""
	return msg.split(b"\n")[0].split(b":")[1] 

def Hito0(connection_tuple : tuple[str, int], username : str) -> bytes:
	"""
	Envía el nombre de usuario a la tupla de conexión y devuelve el mensaje recibido. Se usa un socket RAW

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que le enviaremos el nombre de usuario
		username: El nombre de usuario que enviaremos
		

	Returns: El mensaje de respuesta de connection_tuple. Contiene el identificador y las instrucciones para el siguiente Hito
	"""
	
	with socket.socket() as socketRawHito0:
		socketRawHito0.connect(connection_tuple)

		msg = socketRawHito0.recv(DEFAULT_PACKET_SIZE)

		if VERBOSE: print(f"[Hito0] INFO:\n{msg.decode()}"); print(f"[Hito0] INFO: {username = }")

		socketRawHito0.send(username.encode())

		msg = socketRawHito0.recv(DEFAULT_PACKET_SIZE)

	return msg

def Hito1(connection_tuple : tuple[str, int], identifier : bytes, port : int) -> bytes:
	"""
	Se fija al puerto especificado
	Envía un mensaje UDP a la tupla de conexión con el identificador y el puerto especificados
	Intenta leer un mensaje, y si este requiere el identificador en mayúsculas
		Envía el identificador en mayúsculas a quién envió el mensaje
	Devuelve el último mensaje recibido a través del socket. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	mensaje : bytes = f"{port} ".encode() + identifier

	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidorUDP:
		servidorUDP.bind(("", port))

		if VERBOSE: print(f"[Hito1] INFO: {mensaje = }")

		servidorUDP.sendto(mensaje, connection_tuple)

		msg, sender = servidorUDP.recvfrom(DEFAULT_PACKET_SIZE)

		if VERBOSE: print(f"[Hito1] INFO:\n{msg.decode()}"); print(f"[Hito1] INFO: {sender = }")

		if msg == b"upper-code?":

			if VERBOSE: print(f"[Hito1] INFO: {identifier.upper() = }")

			servidorUDP.sendto(identifier.upper(), sender)

			msg = servidorUDP.recv(DEFAULT_PACKET_SIZE)

	return msg

def ObtainWordCount(TCPsocket : socket.socket, maximum : int, word_separators) -> bytes:
	"""
	Devuelve bytes que contienen la cuenta de los caracteres de las palabras (separadas por alguno de los caracteres especificados en) que se obtienen del socket, que debe de estar previamente conectado
	"""

	suma : int = 0
	count : bytes = b" "

	chars_in_word : int = 0

	# obtenemos el número ascii asociado a los diferentes separadores especificados
	word_separators = [ord(i) for i in word_separators]

	if DEBUG: print(f"[ObtainWordCount] DEBUG: {word_separators = }")

	while suma < maximum:
		word_sequence = TCPsocket.recv(DEFAULT_PACKET_SIZE)
		byte : int = 0

		if DEBUG: print(f"[ObtainWordCount] DEBUG: Received a new message:\n{word_sequence.decode()}")

		while byte < len(word_sequence) and suma < maximum:
			if word_sequence[byte] not in word_separators:
				chars_in_word += 1
			else:
				suma += chars_in_word
				count += f"{chars_in_word} ".encode()

				if DEBUG: print(f"[ObtainWordCount] DEBUG: word at {byte = } ended with {chars_in_word = }. {maximum - suma} chars remain.")

				chars_in_word = 0
			byte += 1
	
	return count

def ObtainLastMessage(socket : socket.socket) -> bytes:
	previous = msg = socket.recv(DEFAULT_PACKET_SIZE)
	while len(msg) > 0:

		if DEBUG: print(f"[ObtainLastMessage] DEBUG: Received a new message:\n{msg = }")

		previous = msg
		msg = socket.recv(DEFAULT_PACKET_SIZE)

	return previous

def Hito2(connection_tuple : tuple[str, int], identifier : bytes, maximum : int, word_separators) -> bytes:

	mensaje : bytes = identifier

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito2:
		servidorTCPHito2.connect(connection_tuple)

		mensaje += ObtainWordCount(servidorTCPHito2, maximum, word_separators) + b"--"

		if VERBOSE: print(f"[Hito2] INFO: {mensaje = }")

		servidorTCPHito2.send(mensaje)

		msg = ObtainLastMessage(servidorTCPHito2)

	return msg

def Hito3(connection_tuple : tuple[str, int], identifier : bytes, maximum : int) -> bytes:

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito3:
		servidorTCPHito3.connect(connection_tuple)

		sumaMaxima = maximum
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

		msg = ObtainLastMessage(servidorTCPHito3)

	return msg


# función main: llama a todos los hitos en orden con los parámetros necesarios
if __name__ == "__main__":
	try:
		print(f"[main] INFO: Starting {__file__} as {os.environ['USER']}.")

		msg = Hito0(("yinkana", 2000), os.environ["USER"])

		print(f"[main] INFO: Hito0:\n{msg.decode()}")

		msg = Hito1(("yinkana", 4000), ObtainIdentifier(msg), 25565)

		print(f"[main] INFO: Hito1:\n{msg.decode()}")

		msg = Hito2(("yinkana", 3010), ObtainIdentifier(msg), 1000, [" ", "\t", "\n"])

		print(f"[main] INFO: Hito2:\n{msg.decode()}")

		msg = Hito3(("yinkana", 5501), ObtainIdentifier(msg), 1200)

		print(f"[main] INFO: Hito3:\n{msg.decode()}")
		...
	except Exception as e:
		print(f"[main] FATAL: {e}")

