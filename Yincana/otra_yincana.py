#!/usr/bin/python3

import socket
import hashlib
import struct
import base64
import sys
import array

def cksum(pkt):
    # type: (bytes) -> int
    if len(pkt) % 2 == 1:
        pkt += b'\0'
    s = sum(array.array('H', pkt))
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    s = ~s

    if sys.byteorder == 'little':
        s = ((s >> 8) & 0xff) | s << 8

    return s & 0xffff

def obtenerID(mensaje):
    return mensaje.split(b"\n")[0].split(b":")[1].strip()

def Hito0(usuario):
    cliente = socket.socket()
    cliente.connect(("yinkana", 2000))

    mensaje = cliente.recv(1024)

    print(mensaje.decode())

    cliente.sendall(usuario.encode())
    mensaje = cliente.recv(1024)

    cliente.close()

    return mensaje

def Hito1(mensaje):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    servidor.bind(("", 5792))

    id = obtenerID(mensaje)

    servidor.sendto(b"5792 " + id, ("yinkana", 4000))
    mensaje, peer = servidor.recvfrom(1024)

    if mensaje.decode() == "upper-code?":
        servidor.sendto(id.upper(), peer)

        mensaje = servidor.recv(1024)
    
    servidor.close()

    return mensaje

def longitudHito2(cliente):
    suma = 0
    longitud = b" "

    ultimo = b""
    while suma < 1000:
        mensaje = cliente.recv(1024)

        divisiones = (ultimo + mensaje).split(b" ")
        i = 0
        while i < len(divisiones) - 1 and suma < 1000:
            suma += len(divisiones[i])
            longitud += str(len(divisiones[i])).encode() + b" "
            i += 1

        ultimo = divisiones[i]

    return longitud

def siguienteEnunciado(cliente):
    mensaje = cliente.recv(1024)

    while mensaje and not mensaje.decode().startswith("identifier:"):
        mensaje = cliente.recv(1024)

    return mensaje

def Hito2(mensaje):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(("yinkana", 3010))

    id = obtenerID(mensaje)
    longitud = longitudHito2(cliente)

    cliente.sendall(id + longitud + b"--")
    mensaje = siguienteEnunciado(cliente)

    cliente.close()

    return mensaje

def esPalindromo(palabra):
    i = 0
    while i < len(palabra) / 2:
        if palabra[i] != palabra[-(i + 1)]:
            return False
        i += 1
    
    return True

def invertirHito3(socket):
    invertidas = b" "
    palindromo = False

    ultimo = b""
    while not palindromo:
        mensaje = socket.recv(1024)

        divisiones = (ultimo + mensaje).split(b" ")
        i = 0
        while i < len(divisiones) - 1 and not palindromo:
            if divisiones[i].decode().isdecimal():
                invertidas += divisiones[i] + b" "
            elif esPalindromo(divisiones[i]):
                palindromo = True
            else:
                invertidas += divisiones[i][::-1] + b" "
            i += 1
        
        ultimo = divisiones[i]

    return invertidas

def Hito3(mensaje):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.connect(("yinkana", 6500))

    id = obtenerID(mensaje)
    invertidas = invertirHito3(cliente)

    cliente.sendall(id + invertidas + b"--")
    mensaje = siguienteEnunciado(cliente)

    cliente.close()

    return mensaje

def recibirArchivo(socket):
    mensaje = socket.recv(1024)

    divisiones = mensaje.split(b":")

    tamaño = int(divisiones[0].decode("ASCII"))

    archivo = b""

    i = 1
    while i < len(divisiones) - 1 and len(archivo) != tamaño:
        archivo += divisiones[i][:tamaño - len(archivo)] + b":"
        i += 1

    archivo += divisiones[i][:tamaño - len(archivo)]

    while len(archivo) != tamaño:
        archivo += socket.recv(1024)[:tamaño - len(archivo)]

    return archivo

def Hito4(mensaje):
    cliente = socket.socket()
    cliente.connect(("yinkana", 9003))

    cliente.sendall(obtenerID(mensaje))
    archivo = recibirArchivo(cliente)

    sha1 = hashlib.sha1()
    sha1.update(archivo)
    digest = sha1.digest()

    cliente.sendall(digest)
    mensaje = siguienteEnunciado(cliente) + cliente.recv(1024)

    cliente.close()

    return mensaje

def Hito5(mensaje):
    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    id = obtenerID(mensaje)

    cabecera = struct.pack("!3sBHHH", b"WYP", 0, 0, 0, 1)
    mensaje = base64.b64encode(id)

    suma = cksum(cabecera + mensaje)

    cabecera = struct.pack("!3sBHHH", b"WYP", 0, 0, suma, 1)

    cliente.sendto(cabecera + mensaje, ("yinkana", 6000))
    mensaje = cliente.recv(2048)[10:]

    cliente.close()

    return base64.b64decode(mensaje)

def main():
    mensaje = Hito0("heuristic_cray")
    print(mensaje.decode())
    mensaje = Hito1(mensaje)
    print(mensaje.decode())
    mensaje = Hito2(mensaje)
    print(mensaje.decode())
    mensaje = Hito3(mensaje)
    print(mensaje.decode())
    mensaje = Hito4(mensaje)
    print(mensaje.decode())
    mensaje = Hito5(mensaje)
    print(mensaje.decode())

main()

