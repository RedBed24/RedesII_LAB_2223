#!/usr/bin/python3

"""Yicana"""
__author__ = "Samuel Espejo"


import socket
import os


# Definir algunas "constantes"

DEFAULT_PACKET_SIZE : int = 1024

def debug(caller : str, debug_type : str, info : str) -> None:
	"""
	Función ayudante para mostrar información durante la ejecución

	Parameters:
		caller: Función que ha llamadado a esta, para localizar la ejecución en el código
		debug_type: Cualquiera de ["INFO", "INFO+", "DEBUG", "WARNING", "FATAL"], indica el tipo de información a mostrar
		info: Información que será mostrada
	"""
	# Muestra más de la información típica
	VERBOSE : bool = True
	# Muestra mucha información
	DEBUG : bool = False
	# Mustra la información con secuencias de color ANSI
	USE_PRINT_COLORS : bool = True
	
	# Sólo muestra errores fatales, sobre escribe las anteriores
	QUIET : bool = False

	msg : str = f"[{caller}] {debug_type}: {info}"

	if debug_type == "INFO" and not QUIET:
		print(msg)
	elif debug_type == "INFO+" and VERBOSE and not QUIET:
		print(msg)
	elif debug_type == "DEBUG" and DEBUG and not QUIET:
		print(msg)
	elif debug_type == "WARNING" and not QUIET:
		if USE_PRINT_COLORS:
			print(f"\033[93m{msg}\033[0m")
		else:
			print(msg)
	elif debug_type == "FATAL":
		if USE_PRINT_COLORS:
			print(f"\033[91m{msg}\033[0m")
		else:
			print(msg)



def ObtainIdentifier(msg : bytes) -> bytes:
	"""
	Función que devuelve el identificador encontrado en el mensaje

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

		debug("Hito0", "INFO", f"\n{msg.decode()}")
		debug("Hito0", "INFO+", f"{username = }")

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

		debug("Hito1", "INFO+", f"{mensaje = }")

		servidorUDP.sendto(mensaje, connection_tuple)

		msg, sender = servidorUDP.recvfrom(DEFAULT_PACKET_SIZE)

		debug("Hito1", "INFO+", f"\n{msg.decode()}")
		debug("Hito1", "INFO+", f"{sender = }")

		if msg == b"upper-code?":

			debug("Hito1", "INFO+", f"{identifier.upper() = }")

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

	debug("ObtainWordCount", "DEBUG", f"{word_separators = }")

	while suma < maximum:
		word_sequence = TCPsocket.recv(DEFAULT_PACKET_SIZE)
		byte : int = 0

		debug("ObtainWordCount", "DEBUG", f"Received a new message:\n{word_sequence.decode()}")

		while byte < len(word_sequence) and suma < maximum:
			if word_sequence[byte] not in word_separators:
				chars_in_word += 1
			else:
				suma += chars_in_word
				count += f"{chars_in_word} ".encode()

				debug("ObtainWordCount", "DEBUG", f"word at {byte = } ended with {chars_in_word = }. {maximum - suma} chars remain.")

				chars_in_word = 0
			byte += 1
	
	return count

def ObtainLastMessage(socket : socket.socket) -> bytes:
	previous = msg = socket.recv(DEFAULT_PACKET_SIZE)
	while len(msg) > 0:

		debug("ObtainLastMessage", "DEBUG", f"Received a new message:\n{msg = }")

		previous = msg
		msg = socket.recv(DEFAULT_PACKET_SIZE)

	return previous

def Hito2(connection_tuple : tuple[str, int], identifier : bytes, maximum : int, word_separators) -> bytes:

	mensaje : bytes = identifier

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito2:
		servidorTCPHito2.connect(connection_tuple)

		mensaje += ObtainWordCount(servidorTCPHito2, maximum, word_separators) + b"--"

		debug("Hito2", "INFO+", f"{mensaje = }")

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
		debug("main", "INFO", f"Starting {__file__} as {os.environ['USER']}.")

		msg = Hito0(("yinkana", 2000), os.environ["USER"])

		debug("main", "INFO", f"Hito1:\n{msg.decode()}")

		msg = Hito1(("yinkana", 4000), ObtainIdentifier(msg), 25565)

		debug("main", "INFO", f"Hito2:\n{msg.decode()}")

		msg = Hito2(("yinkana", 3010), ObtainIdentifier(msg), 1000, [" ", "\t", "\n"])

		debug("main", "INFO", f"Hito3:\n{msg.decode()}")

		msg = Hito3(("yinkana", 5501), ObtainIdentifier(msg), 1200)

		debug("main", "INFO", f"Hito4:\n{msg.decode()}")
		...
	except Exception as e:
		debug("main", "FATAL", f"Exception: {e}")

