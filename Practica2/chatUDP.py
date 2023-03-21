#!/usr/bin/python3
"""usage: %s [--server|--client]"""

# pydoc ^

import sys
import socket
import _thread

SERVER = ("127.0.0.1", 12345)
QUIT = "bye"

def recieveMessages(peer, sock):
	"""Recibe los mensajes de peer mediante el socket y los muestra por la salida estandar"""
	while True:
		# recibimos un mensaje
		msg, sender = sock.recvfrom(1024)

		# comprobamos si el que nos ha enviado el mensaje es nuestro compañero
		if sender == peer:
			# mostramos el mensaje decodificado
			print(f"{msg.decode()}")
		else:
			# marcamos que hemos recibido un mensaje de un desconocido
			print(f"You've recieved a mesage from {sender} while you where in a connection with {peer}.")

		# si nos han enviado el mensaje de salida
		if msg.decode() == QUIT:
			# le respondemos con el mensaje de salida para que él también termine
			sock.sendto(QUIT.encode(), peer)
			# terminamos la ejecución
			break

def sendMessages(peer, sock):
	"""Envía mensajes recogidos de la entrada estandar mediante el socket a peer"""
	while True:
		# recibimos un string de la entrada estandar
		msg = input()
		
		# lo codificamos y se lo enviamos a nuestro compañero
		sock.sendto(msg.encode(), peer)

		# si le hemos mandado el mensaje de salida
		if msg == QUIT:
			# terminamos la ejecución
			break

# comprobamos que el uso de este fichero sea como ejecución principal
if __name__ == "__main__":

	# clausula guardia para obtener el modo
	if len(sys.argv) != 2:
		# mostramos pydoc del inicio del fichero
		# está formateado con un String (%s), este es el nombre del programa
		print(f"{__doc__ % sys.argv[0]}")
		sys.exit(1)

	# obtenemos el modo de ejecución
	mode = sys.argv[1]

	# abrimos el socket de internet para UDP
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
		
		# dependiendo del modo
		if mode == "--server":
			# escucharemos de todo internet por el puerto 12345
			sock.bind(("", 12345))

			print(f"Waiting for a connection...")

			# esperamos a recibir un mensaje para obtener a quién tenemos que hablar
			# MSG_PEEK, definido en <sys/socket.h> no quita el mensaje de la cola
			msg, peer = sock.recvfrom(0, socket.MSG_PEEK)

			print(f"{peer} started a conversation.")

		elif mode == "--client":
			# hablaremos al servidor
			peer = SERVER
		else:
			# un modo no reconocido
			print(f"{__doc__ % sys.argv[0]}")
			sys.exit(1)

		# empezamos un hilo para enviar mensajes con el compañero y el socket dado
		# el hilo termina su ejecución cuando se sale de la función
		_thread.start_new_thread(sendMessages, (peer, sock))

		# el hilo principal lo destinamos a recibir mensajes
		recieveMessages(peer, sock)

	# el socket se cierra automáticamente por el uso de with

