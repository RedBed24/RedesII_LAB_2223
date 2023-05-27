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

	Returns:
		El identificador (en bytes), se encuentra entre b":" y b"\\n" del patrón encontrado
	"""
	return msg.split(b"\n")[0].split(b":")[1] 

def Hito0(connection_tuple : tuple[str, int], username : str) -> bytes:
	"""
	Envía el nombre de usuario a la tupla de conexión y devuelve el mensaje recibido. Se usa un socket RAW

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que le enviaremos el nombre de usuario
		username: El nombre de usuario que enviaremos
		

	Returns:
		El mensaje de respuesta de connection_tuple. Contiene el identificador y las instrucciones para el siguiente Hito
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
	Devuelve el último mensaje recibido a través del socket

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto con la que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito
		port: Puerto que usaremos para la conexión

	Returns:
		El mensaje recibido justamente después de contestar. Contiene el identificador y las instrucciones para el siguiente Hito
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

def ObtainWordsLen(TCPsocket : socket.socket, maximum : int) -> bytes:
	"""
	Crea un mensaje en bytes que cuenta cuántos bytes hay entre espacio y espacio poniendo estos valores en orden en el mensaje.
	Cuando la suma sea mayor o igual que el máximo, parará.

	Parameters: 
		TCPsocket: Socket ya abierto que provee las palabras y números
		maximum: Suma que queremos superar

	Returns:
		Mensaje creado con la longitud de cada palabra en orden
	"""

	suma : int = 0
	count : bytes = b" "

	msg : bytes
	divisiones : [bytes]
	token : bytes = b""

	while suma < maximum:
		msg = TCPsocket.recv(DEFAULT_PACKET_SIZE)

		debug("ObtainWordsLen", "DEBUG", f"Received a new message:\n{msg.decode()}")

		# juntamos el último token recibido con el mensaje ya que podríamos haber cortado por una palabra o número
		divisiones = (token + msg).split(b" ")

		for token in divisiones[:-1]:
			suma += len(token)
			count += f"{len(token)} ".encode()

			if suma >= maximum:
				break

		# obtenemos el último token para juntarlo con el siguiente mensaje
		token = divisiones[-1]
	
	return count

def ObtainAllMessages(socket : socket.socket) -> [bytes]:
	"""
	Recibe todos los mensajes hasta que se encuentra uno vacío y devuelve todos los leídos.

	Parameters:
		socket: Socket previamente abierto que enviará los mensajes.

	Returns:
		Array conteniendo todos los mensajes.
	"""

	msg_list : [bytes] = []
	msg = socket.recv(DEFAULT_PACKET_SIZE)

	while msg:
		debug("ObtainAllMessages", "DEBUG", f"Received a new message:\n{msg = }")

		msg_list.append(msg)

		msg = socket.recv(DEFAULT_PACKET_SIZE)

	return msg_list

def Hito2(connection_tuple : tuple[str, int], identifier : bytes, maximum : int) -> bytes:
	"""
	Abre la conexión con la tupla dada
	Obtiene la longitud de las palabas que la conexión ofrece hasta el máximo especificado
	Envía un mensaje con el identificador y todas las longitudes leídas
	Obtiene el último mensaje de la conexión y lo devuelve

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito
		maximum: Suma máxima de longitudes de palabras

	Returns:
		El último mensaje recibido por el socket. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito2:
		servidorTCPHito2.connect(connection_tuple)

		mensaje : bytes = identifier + ObtainWordsLen(servidorTCPHito2, maximum) + b"--"

		debug("Hito2", "INFO+", f"{mensaje = }")

		servidorTCPHito2.send(mensaje)

		msg = ObtainAllMessages(servidorTCPHito2)[-1]

	return msg

def ObtainWordAfterSum(TCPsocket : socket.socket, maximum : int) -> bytes:
	"""
	Función que obtiene la siguiente palabra (aquello que no se puede convertir a número) que viene tras superar la suma de la cuenta de palabras y los valores dados

	Parameters:
		TCPsocket: Socket ya abierto que provee las palabras y números
		maximum: Suma que queremos superar

	Returns:
		La palabra que se ha encontrado
	"""

	suma : int = 0
	palabra : bytes = None

	msg : bytes
	divisiones : [bytes]
	token : bytes = b""

	while palabra == None:
		msg = TCPsocket.recv(DEFAULT_PACKET_SIZE)

		debug("ObtainWordAfterSum", "DEBUG", f"Received a new message:\n{msg.decode()}")

		# juntamos el último token recibido con el mensaje ya que podríamos haber cortado por una palabra o número
		divisiones = (token + msg).split(b" ")

		for token in divisiones[:-1]:
			# intentamos obtener el valor
			try:
				# en cuyo caso, sumamos su valor
				suma +=	int(token.decode())
			except ValueError as ve:
				# si es una palabra, sumamos 1
				suma += 1
				# comprobamos si ya hemos superado la suma
				if suma > maximum:
					# entonces esta es la palabra
					palabra = token
					break

		# obtenemos el último token para juntarlo con el siguiente mensaje
		token = divisiones[-1]
	
	return palabra

def Hito3(connection_tuple : tuple[str, int], identifier : bytes, maximum : int) -> bytes:
	"""
	Abre la conexión con la tupla dada
	Obtiene la primera palabra leída tras alcanzar el máximo
	Envía un mensaje con el identificador y la palabra
	Obtiene el último mensaje de la conexión y lo devuelve

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito
		maximum: Suma máxima del valor de los números y las palabras a leer

	Returns:
		El último mensaje recibido por el socket. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorTCPHito3:
		servidorTCPHito3.connect(connection_tuple)

		mensaje : bytes = ObtainWordAfterSum(servidorTCPHito3, maximum) + b" " + identifier

		debug("Hito3", "INFO+", f"{mensaje = }")

		servidorTCPHito3.send(mensaje)

		msg = ObtainAllMessages(servidorTCPHito3)[-1]

	return msg


# función main: llama a todos los hitos en orden con los parámetros necesarios
if __name__ == "__main__":
	try:
		debug("main", "INFO", f"Starting {__file__} as {os.environ['USER']}.")

		msg = Hito0(("yinkana", 2000), os.environ["USER"])

		debug("main", "INFO", f"Hito1:\n{msg.decode()}")

		msg = Hito1(("yinkana", 4000), ObtainIdentifier(msg), 25565)

		debug("main", "INFO", f"Hito2:\n{msg.decode()}")

		msg = Hito2(("yinkana", 3010), ObtainIdentifier(msg), 1000)

		debug("main", "INFO", f"Hito3:\n{msg.decode()}")

		msg = Hito3(("yinkana", 5501), ObtainIdentifier(msg), 1200)

		debug("main", "INFO", f"Hito4:\n{msg.decode()}")
		...
	except Exception as e:
		debug("main", "FATAL", f"Exception: {e}")

