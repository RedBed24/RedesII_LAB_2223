#!/usr/bin/python3

"""Yicana"""
__author__ = "Samuel Espejo"


import socket

# Para obtener el usuario que está ejecutando el código
import os

# Cálculo de la suma md5 del fichero en el hito 4
import hashlib

# Empaquetar datos para las cabeceras de los hitos 5 y 6
import struct

# Codificar y decodificar payload del hito 5, YAP
import base64

# Concurrencia para el hito 6
import _thread

# Para obtener los rfc
import urllib.request

# Muestra de mensajes
import logging


# Función dada por los profesores para calcular el campo checksum del hito 5, YAP
from inet_checksum import cksum


# Definir algunas "constantes"

DEFAULT_PACKET_SIZE : int = 1024
MAGIC_WORD : bytes = b"identifier"


def ObtainIdentifier(msg : bytes) -> bytes:
	"""
	Si no se encuentra la palabra mágica al principio del mensaje, no se puede obtener el identificador
	Función que devuelve el identificador encontrado en el mensaje

	Parameters:
		msg: Bytes que deben ser del estilo: b"MAGIC_WORD:.*\\n.*" La primera instancia del patrón contiene el identificador

	Returns:
		El identificador (en bytes), se encuentra entre b":" y b"\\n" del patrón encontrado quitando los espacios
	"""
	if msg[:len(MAGIC_WORD)] != MAGIC_WORD:
		raise Exception(f"msg does not start with {MAGIC_WORD = }")
	return msg.split(b"\n")[0].split(b":")[1].strip()

def Hito0(connection_tuple : tuple[str, int], username : str) -> bytes:
	"""
	Envía el nombre de usuario a la tupla de conexión y devuelve el mensaje recibido. Se usa un socket RAW

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que le enviaremos el nombre de usuario
		username: El nombre de usuario que enviaremos

	Returns:
		El mensaje de respuesta de connection_tuple. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	with socket.socket() as clienteRAWHito0:
		clienteRAWHito0.connect(connection_tuple)

		msg = clienteRAWHito0.recv(DEFAULT_PACKET_SIZE)

		logging.info(f"Hito0:\n{msg.decode()}")

		clienteRAWHito0.sendall(username.encode())

		msg = clienteRAWHito0.recv(DEFAULT_PACKET_SIZE)

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

	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidorUPDHito1:
		servidorUPDHito1.bind(("", port))

		servidorUPDHito1.sendto(mensaje, connection_tuple)

		msg, sender = servidorUPDHito1.recvfrom(DEFAULT_PACKET_SIZE)

		logging.debug(f"Hito1: \n{msg.decode()}")

		if msg == b"upper-code?":

			logging.debug(f"Hito1: sending {identifier.upper()} to {sender}")

			servidorUPDHito1.sendto(identifier.upper(), sender)

			msg = servidorUPDHito1.recv(DEFAULT_PACKET_SIZE)

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

		logging.debug(f"ObtainWordsLen: new message:\n{msg = }")

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
	Recibe todos los mensajes hasta que se encuentra uno vacío, cuando el otro socket se ha cerrado, y devuelve todos los leídos.

	Parameters:
		socket: Socket previamente abierto que enviará los mensajes.

	Returns:
		Array conteniendo todos los mensajes.
	"""

	msg_list : [bytes] = []
	msg = socket.recv(DEFAULT_PACKET_SIZE)

	while msg:
		logging.debug(f"ObtainAllMessages: new message:\n{msg = }")

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

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clienteTCPHito2:
		clienteTCPHito2.connect(connection_tuple)

		mensaje : bytes = identifier + ObtainWordsLen(clienteTCPHito2, maximum) + b"--"

		logging.info(f"Hito2: sending {mensaje = }")

		clienteTCPHito2.sendall(mensaje)

		msg = ObtainAllMessages(clienteTCPHito2)[-1]

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

		logging.debug(f"ObtainWordAfterSum: new message:\n{msg = }")

		# juntamos el último token recibido con el mensaje ya que podríamos haber cortado por una palabra o número
		divisiones = (token + msg).split(b" ")

		for token in divisiones[:-1]:
			# intentamos obtener el valor
			try:
				# en cuyo caso, sumamos su valor
				suma +=	int(token.decode())
			except ValueError as ve:
				# comprobamos si ya hemos superado la suma
				if suma > maximum:
					# entonces esta es la palabra
					palabra = token
					break

				# si es una palabra, sumamos 1
				suma += 1

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

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clienteTCPHito3:
		clienteTCPHito3.connect(connection_tuple)

		mensaje : bytes = ObtainWordAfterSum(clienteTCPHito3, maximum) + b" " + identifier

		logging.info(f"Hito3: sending {mensaje = }")

		clienteTCPHito3.sendall(mensaje)

		msg = ObtainAllMessages(clienteTCPHito3)[-1]

	return msg

def ObtainLengthFile(socketRAW : socket.socket) -> bytes:
	"""
	Divide el mensaje como se especifica, asegurando que no añadamos al fichero más de lo necesario
	Mientras la longitud del fichero no sea la esperada
		Leer tantos datos como queden o menos
		Concatenar datos al fichero
	Devolver el fichero

	Parameters:
		socketRAW: Socket abierto por el que se esperan los datos

	Returns:
		El fichero leído como bytes
	"""

	msg : bytes = socketRAW.recv(DEFAULT_PACKET_SIZE)

	logging.debug(f"ObtainLengthFile: {len(msg) = }, {msg = }")

	# Limitamos a 1 división
	divisiones : [bytes] = msg.split(b":", 1)

	longitud : int = int(divisiones[0].decode("ASCII"))

	# Puede ser que ya hayamos leído todo lo necesario, de eso, sólo cogemos tantos bytes como la longitud nos indique
	fichero : bytes = divisiones[1][0:longitud]

	logging.debug(f"ObtainLengthFile: START: {longitud = }, {len(fichero) = }, {fichero = }")

	while len(fichero) != longitud:
		# recibimos sólo hasta lo que quede
		fichero += socketRAW.recv(longitud - len(fichero))
		logging.debug(f"ObtainLengthFile: READING: {len(fichero) = }")

	logging.debug(f"ObtainLengthFile: EXIT: {longitud = }, {len(fichero) = }")

	return fichero


def Hito4(connection_tuple : tuple[str, int], identifier : bytes) -> bytes:
	"""
	Abre la conexión con la tupla dada
	Manda el identificador
	Obtiene el fichero provisto por la conexión
	Calcula el MD5 del fichero
	Obtiene los últimos mensajes de la conexión y los devuelve como uno

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito

	Returns:
		Los últimos mensajes recibidos por el socket. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	with socket.socket() as clienteRAWHito4:
		clienteRAWHito4.connect(connection_tuple)

		clienteRAWHito4.sendall(identifier)

		fichero : bytes = ObtainLengthFile(clienteRAWHito4)

		md5 = hashlib.md5()

		md5.update(fichero)

		digest : bytes = md5.digest()

		logging.info(f"Hito4: sending {digest = }")

		clienteRAWHito4.sendall(digest)

		msg_list = ObtainAllMessages(clienteRAWHito4)

	return msg_list[-2] + msg_list[-1]

def Hito5(connection_tuple : tuple[str, int], identifier : bytes) -> bytes:
	"""
	Empaqueta la cabecera con el checksum a 0 y codifica el payload
	Junta el mensaje y calcula el checksum de este para asignarselo a la cabecera de verdad
	Envía el mensaje a la tupla y espera un mensaje de vuelta
	Lo desempaqueta y separa, comprobando que sea todo correcto
	En cuyo caso devuelve el payload decodificado

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que enviaremos el mensaje YAP
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito

	Returns:
		El payload decodificado del mensaje recibido. Contiene el identificador y las instrucciones para el siguiente Hito
	"""

	# Crear mensaje con checksum a 0 para calcular el checksum verdadero
	header : bytes = struct.pack("!3sHBHH", b"YAP", 0, 0, 0, 1)
	payload : bytes = base64.b64encode(identifier)

	mensaje : bytes = header + payload

	# Cálculo del checksum y actualización del campo
	cks : int = cksum(mensaje)

	header : bytes = struct.pack("!3sHBHH", b"YAP", 0, 0, cks, 1)
	mensaje : bytes = header + payload

	logging.info(f"Hito5: sending {mensaje = }")

	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clienteYAPoUDP:

		clienteYAPoUDP.sendto(mensaje, connection_tuple)

		msg : bytes = clienteYAPoUDP.recv(DEFAULT_PACKET_SIZE * 2)

	logging.debug(f"Hito5: {msg = }")

	# Desempaquetado del mensaje recibido
	header : tuple = struct.unpack("!3sHBHH", msg[:10])
	payload : bytes = msg[10:]

	# check errors
	if header[1] != 1 or header[2] != 0:
		raise Exception("Unexpected YAP request or error code.")

	cks : int = header[3]
	header : bytes = struct.pack("!3sHBHH", header[0], header[1], header[2], 0, header[4])
	msg : bytes = header + payload

	if cks != cksum(msg):
		raise Exception("Wrong checksum")

	return base64.b64decode(payload)

def GET(request_socket : socket.socket, msg : bytes, provider : tuple[str, int]) -> None:
	"""
	Obtiene el fichero a enviar
	Se lo pide al proveedor
	Devuelve el fichero si se ha encontrado o una línea con el error
	Cierra el socket

	Parameters:
		request_socket: Socket que pide el fichero
		msg: Mensaje HTTP que ha enviado el request_socket socket con la petición GET del que se obtiene el fichero
		provider: Tupla dirección puerto que identifica al proveedor de los ficheros a devolver
	"""

	file = msg.split(b" ")[1]

	with urllib.request.urlopen(f"http://{provider[0]}:{provider[1]}/rfc{file.decode()}") as response:
		if response.status == 200:
			logging.debug(f"GET: sending {file = }")
			request_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + response.read())
		else:
			logging.debug(f"GET: {file = } not sent")
			request_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

	request_socket.close()

def HTTP(HTTPserver_socket : socket.socket, provider : tuple[str, int]) -> bytes:
	"""
	Siempre:
		Acepta una nueva conexión
		Recibe un mensaje de esta
		Comprueba si es una petición GET
			Dedica un hilo a tratar esta
		En caso contrario
			Devuelve el mensaje

	Parameters:
		HTTPserver_socket: Socket del servidor HTTP que está a la escucha de nuevas conexiones
		provider: Tupla dirección puerto que identifica al proveedor de los ficheros a devolver

	Returns:
		El primer mensaje que no sea una petición GET. Este contiene una cabecera HTTP y en el payload, el identificador y las instrucciones para el siguiente Hito
	"""

	while True:
		request_socket, peer = HTTPserver_socket.accept()

		msg = request_socket.recv(DEFAULT_PACKET_SIZE)
		logging.debug(f"HTTP: {msg = }")

		if msg[:3] == b"GET":
			_thread.start_new_thread(GET, (request_socket, msg, provider))
		else:
			return msg

def ErrorListening(connection_tuple : tuple[str, int], identifier : bytes, port : int) -> None:
	"""
	Crea el mensaje a enviar con el identificador y el puerto
	Abre el socket cliente, se conecta a la tupla de conexión y envía el mensaje
	Entra en bucle mientras el socket esté abierto
		Recibe y muestra el mensaje

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito
	"""

	mensaje : bytes = identifier + f" {port}".encode()
	logging.info(f"ErrorListening: sending {mensaje = }")

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente_erroresTCP:

		cliente_erroresTCP.connect(connection_tuple)
		cliente_erroresTCP.sendall(mensaje)

		while True:
			msg = cliente_erroresTCP.recv(DEFAULT_PACKET_SIZE)

			if not msg:
				break

			logging.warning(f"ErrorListening: {msg = }")

def Hito6(connection_tuple : tuple[str, int], identifier : bytes, port : int, max_connections : int, provider : tuple[str, int]) -> bytes:
	"""
	Abre el servidor HTTP conectandose al puerto dado y escucha la cantidad de conexiones dadas
	Crea un hilo para la escucha de errores
	Atiende a las peticiones HTTP
	Busca y devuelve el payload del último mensaje HTTP

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito
		port: Puerto por el que escuchará el servidor
		max_connections: Numero máximo de conexiones a atender a la vez
		provider: Tupla dirección puerto que identifica al proveedor de los ficheros a devolver

	Returns:
		El payload del último mensaje HTTP, el identificador y las instrucciones para el siguiente Hito
	"""

	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidorHTTP:

		servidorHTTP.bind(("", port))
		servidorHTTP.listen(max_connections)

		_thread.start_new_thread(ErrorListening, (connection_tuple, identifier, port))

		msg = HTTP(servidorHTTP, provider)

	http_header_end = msg.find(b"\r\n\r\n")

	return msg[http_header_end + 4:]

def Hito7(connection_tuple : tuple[str, int], identifier : bytes) -> bytes:
	"""
	Se conecta a la tupla de conexión
	Envia el identificador
	Espera un mensaje y lo devuelve

	Parameters:
		connection_tuple: Una tupla con la dirección y el puerto al que nos conectaremos
		identifier: Bytes que representan el identificador obtenido de las instrucciones del hito

	Returns:
		Tarta :D
	"""

	with socket.socket() as clienteRAWHito7:
		clienteRAWHito7.connect(connection_tuple)

		clienteRAWHito7.sendall(identifier)

		msg = clienteRAWHito7.recv(DEFAULT_PACKET_SIZE)

	return msg

# función main: llama a todos los hitos en orden con los parámetros necesarios
if __name__ == "__main__":
	try:
		#logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

		print(f"main: Starting {__file__} as {os.environ['USER']}.")

		msg = Hito0(("yinkana", 2000), os.environ["USER"])

		print(f"main: Hito1:\n{msg.decode()}")

		msg = Hito1(("yinkana", 4000), ObtainIdentifier(msg), 25565)

		print(f"main: Hito2:\n{msg.decode()}")

		msg = Hito2(("yinkana", 3010), ObtainIdentifier(msg), 1000)

		print(f"main: Hito3:\n{msg.decode()}")

		msg = Hito3(("yinkana", 5501), ObtainIdentifier(msg), 1200)

		print(f"main: Hito4:\n{msg.decode()}")

		msg = Hito4(("yinkana", 9000), ObtainIdentifier(msg))

		print(f"main: Hito5:\n{msg.decode()}")

		msg = Hito5(("yinkana", 6001), ObtainIdentifier(msg))

		print(f"main: Hito6:\n{msg.decode()}")

		msg = Hito6(("yinkana", 8002), ObtainIdentifier(msg), 25565, 5, ("rick", 81))

		print(f"main: Hito6:\n{msg.decode()}")

		msg = Hito7(("yinkana", 33333), ObtainIdentifier(msg))

		print(f"main: Hito7:\n{msg.decode()}")

	except Exception as e:
		logging.error(f"main: Exception: {e}")

