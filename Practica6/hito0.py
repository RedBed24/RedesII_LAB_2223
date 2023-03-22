#!/usr/bin/python3

import socket
import os

# 1024 va a ser el tamaño mínimo de recivo

# funciona raw
sock = socket.socket()

# nos conectamos con la yinkana
sock.connect(("yinkana", 2000))

# recibimos lo que nos envíe
msg = sock.recv(1024)

# vemos qué nos ha enviado
print(f"{msg.decode()}")

# Aquí entre medias habrá que hacer el código

# le enviamos lo que nos pide, nuestro nombre de usuario
sock.send(os.environ["USER"].encode())

# obtenemos las instrucciones de la siguiente
msg = sock.recv(1024)

print(f"{msg.decode()}")

sock.close()

#hito 1
# leo, 

# manda malo, upper con mi código, si no es lo mismo, seguimos escuchand

# yinkana tiene trozos udp

# cuando el código coincida con lo que nos han pasado

# guardar cada mensaje que nos envíen
# abuso de prints se penaliza

# cuidado con el espacio al final

# código tiene x chars SIEMPRE

