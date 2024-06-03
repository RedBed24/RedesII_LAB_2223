#!/usr/bin/env python3
"""Script para la resolución de la yinkana de la asignatura de Redes de Computadores."""

import socket
import logging
import re
import hashlib
import base64
import sys
import struct
import array
import _thread
import urllib.parse


def cksum(pkt):
    # type: (bytes) -> int
    if len(pkt) % 2 == 1:
        pkt += b"\0"
    s = sum(array.array("H", pkt))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    s = ~s

    if sys.byteorder == "little":
        s = ((s >> 8) & 0xFF) | s << 8

    return s & 0xFFFF


def obtener_identificador(msg: bytes) -> bytes:
    """Obtiene el identificador del mensaje.

    :param msg: El mensaje que contiene el identificador.
    :type msg: bytes

    :return: El identificador del mensaje.
    :rtype: bytes
    """
    # buscamos una línea que comience con "identifier:" y nos quedamos con el resto de la línea
    return re.search(b"^identifier:(.+)$", msg, re.MULTILINE).group(1)


def hito0(ip: str, puerto: int, username: bytes) -> bytes:
    """Envía el nombre de usuario a la dirección IP y puerto especificados.
    Devuelve el mensaje recibido.
    Se usa un socket RAW.

    :param ip: La dirección IP a la que enviaremos el nombre de usuario.
    :type ip: str
    :param puerto: El puerto al que enviaremos el nombre de usuario.
    :type puerto: int
    :param username: El nombre de usuario que enviaremos.
    :type username: str

    :return: El mensaje de respuesta de la dirección IP y puerto especificados.
    Contiene el identificador y las instrucciones para el siguiente hito.
    :rtype: bytes
    """
    recibido: bytes

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))

        recibido = cliente.recv(1024)

        logging.info(recibido.decode())

        cliente.sendall(username)

        recibido = cliente.recv(1024)

    return recibido


def hito1(ip: str, puerto: int, identificador: bytes) -> bytes:
    """Envía un mensaje a la dirección IP y puerto especificados.
    El mensaje se forma con el pruerto libre del servidor UDP y el identificador.
    El puerto es obtenido al bindear un socket UDP a un puerto libre.
    Devuelve el mensaje recibido.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes

    :return: El mensaje de respuesta de la dirección IP y puerto especificados.
    :rtype: bytes
    """
    puerto_libre: int
    mensaje: bytes
    recibido: bytes
    socket_cliente_yinkana: tuple[str, int]

    with socket.socket(type=socket.SOCK_DGRAM) as servidor_udp:
        servidor_udp.bind(("", 0))
        puerto_libre = servidor_udp.getsockname()[1]
        mensaje = bytes(str(puerto_libre), encoding="utf-8") + b" " + identificador

        servidor_udp.sendto(mensaje, (ip, puerto))

        recibido, socket_cliente_yinkana = servidor_udp.recvfrom(1024)

        logging.debug(recibido.decode())

        if recibido == b"upper-code?":
            logging.debug(
                "sending %s to %s", identificador.upper(), str(socket_cliente_yinkana)
            )

            servidor_udp.sendto(identificador.upper(), socket_cliente_yinkana)

            recibido = servidor_udp.recv(1024)

    return recibido


def longitudes(tcp_socket: socket.socket, maximo: int) -> bytes:
    """Recibe mensajes de un socket TCP y devuelve un stream de números.
    Los números son la longitud de las palabras recibidas.
    Las palabras están separadas por espacios.
    Se seguirán recibiendo palabras hasta que la suma de las longitudes de las palabras sea
    mayor o igual al máximo dado.

    :param tcp_socket: El socket TCP del que recibiremos los mensajes.
    :type tcp_socket: socket.socket
    :param maximo: La suma de las longitudes de las palabras recibidas no superará este valor.
    :type maximo: int

    :return: Un stream de números que representan la longitud de las palabras recibidas.
    El stream está separado por espacios.
    Cada número está en formato texto decimal.
    :rtype: bytes
    """
    suma: int = 0
    stream_numeros: bytes = b" "

    recibido: bytes
    lista_palabras: list[bytes]
    # no sabemos cuál es la primera palabra
    palabra: bytes = b""

    while not suma >= maximo:
        recibido = tcp_socket.recv(1024)

        logging.debug(recibido.decode())

        # juntamos la palabra anterior con el nuevo mensaje
        # porque la palabra puede estar cortada por la mitad
        lista_palabras = (palabra + recibido).split(b" ")

        while not suma >= maximo and len(lista_palabras) > 1:
            palabra = lista_palabras.pop(0)

            suma += len(palabra)
            stream_numeros += bytes(str(len(palabra)), encoding="utf-8") + b" "

        # asumimos que la última palabra está cortada y la guardamos para la siguiente iteración
        palabra = lista_palabras.pop(0)

    return stream_numeros


def hito2(ip: str, puerto: int, identificador: bytes, suma: int) -> bytes:
    """Envía un mensaje a la dirección IP y puerto especificados.
    El mensaje se forma con el identificador y las longitudes de las palabras recibidas.
    Devuelve el mensaje recibido.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes
    :param suma: La suma de las longitudes de las palabras recibidas no superará este valor.
    :type suma: int

    :return: El enunciado del siguiente hito.
    :rtype: bytes
    """
    recibido: bytes
    enunciado: bytes = None

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))

        cliente.sendall(identificador + b" " + longitudes(cliente, suma) + b"--")

        while enunciado is None:
            recibido = cliente.recv(1024)

            if recibido.startswith(b"identifier:"):
                enunciado = recibido
            elif recibido == b"":
                raise Exception("No data recived")

    return enunciado


def descifrar_palabras(tcp_socket: socket.socket) -> bytes:
    """Recibe mensajes de un socket TCP y devuelve un stream de números.

    :param tcp_socket: El socket TCP del que recibiremos los mensajes.
    :type tcp_socket: socket.socket

    :return: Un stream de palabras
    El stream está separado por espacios.
    :rtype: bytes
    """
    stream_palabras: bytes = b""

    indice_final: int = 0
    indice_inicio: int

    numero_encontrado: bool = False
    numero: int
    division: list[bytes]

    palabras_restantes: int

    recorte: bytes

    while not numero_encontrado:
        # juntamos todo lo recibido
        stream_palabras += tcp_socket.recv(1024)

        logging.debug(stream_palabras)

        while not numero_encontrado and len(stream_palabras) > indice_final:
            if chr(stream_palabras[indice_final]).isdigit():
                # a lo mejor el número está cortado, por lo que tenemos que pedir más datos hasta
                # que tengamos el número completo, seguramente, se complete con los siguientes datos
                while not numero_encontrado:
                    division = stream_palabras[indice_final:].split(b" ", 1)

                    if len(division) > 1 and len(division[1]) > 0:
                        numero = int(division[0].decode())
                        numero_encontrado = True
                    else:
                        stream_palabras += tcp_socket.recv(1024)
                        logging.debug(stream_palabras)

            indice_final += 1

    indice_final -= 1  # quitamos el número
    indice_inicio = indice_final
    palabras_restantes = (
        numero + 1
    )  # + 1 para llegar al espacio antes de la primera palabra

    logging.debug("numero: %d", numero)

    while palabras_restantes > 0:
        if chr(stream_palabras[indice_inicio]) == " ":
            palabras_restantes -= 1
        indice_inicio -= 1

    indice_inicio += (
        2  # para saltar el espacio y ponernos al principio de la primera palabra
    )

    recorte = stream_palabras[indice_inicio:indice_final]

    logging.debug("recorte: %s", str(recorte))

    recorte = bytes(descifrar_chr(c, numero) for c in recorte)

    return recorte


def descifrar_chr(c: int, numero: int) -> int:
    """Descifra el carácter ascii c moviéndolo a la derecha tantas posiciones como indique
    el número. Ej: a movido 1 a la derecha es b, z movido 1 a la derecha es a.
    Sólo descifra letras, el resto de caracteres no los toca.

    :param c: El carácter a descifrar, como un byte.
    :type c: byte
    :param numero: El número de posiciones a mover a la derecha.
    :type numero: int

    :return: El caracter c descifrado.
    :rtype: byte
    """
    if chr(c).islower():  # si es minúscula
        if c + numero > ord("z"):  # si al descifrarlo, se pasa de la "z"
            # entonces, lo moveremos tantas posiciones a partir de "a" como nos faltaban
            return ord("a") + numero - 1 - (ord("z") - c)
        return c + numero
    if chr(c).isupper():
        if c + numero > ord("Z"):
            return ord("A") + numero - 1 - (ord("Z") - c)
        return c + numero

    return c


def hito3(ip: str, puerto: int, identificador: bytes) -> bytes:
    """Envía el identificador a la dirección IP y puerto especificados.
    Lee palabras hasta encontrar un número (X) y devuelve las últimas X palabras leídas.
    Mueve los caracteres tantas posiciones como indique el número X y envía el mensaje.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes

    :return: El enunciado del siguiente hito.
    :rtype: bytes
    """
    recibido: bytes
    enunciado: bytes = None
    palabras: bytes

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))

        cliente.sendall(identificador)

        palabras = descifrar_palabras(cliente)

        logging.debug(palabras)

        cliente.sendall(palabras + b"--")

        while enunciado is None:
            recibido = cliente.recv(1024)

            logging.debug(recibido)

            if recibido.startswith(b"identifier:"):
                enunciado = recibido
            elif recibido == b"":
                raise Exception("No data recived")

    return enunciado


def hito4(ip: str, puerto: int, identificador: bytes) -> bytes:
    """Envía el identificador a la ip y puerto especificados.
    Tras ello, recibe un mensaje separándolo en longitud y parte del fichero.
    Lee tantos bytes como la longitud indique, con estos, actualiza el hash.
    Manda el hash del fichero y devuelve el mensaje recibido.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes

    :return: El enunciado del siguiente hito.
    :rtype: bytes
    """
    hasher: hashlib.md5 = hashlib.md5()
    recibido: bytes
    longitud_b: bytes
    longitud: int

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))

        cliente.sendall(identificador)

        recibido = cliente.recv(1024)

        logging.debug(recibido)

        longitud_b, recibido = recibido.split(b":", 1)

        longitud = int(longitud_b.decode())

        logging.debug("longitud: %d", longitud)

        while longitud > 0:
            hasher.update(recibido)

            longitud -= len(recibido)

            recibido = cliente.recv(min(longitud, 1024))

        cliente.sendall(hasher.digest())

        recibido = cliente.recv(2048)

    return recibido


def preparar_peticion_yap(carga: bytes) -> bytes:
    """Crea un mensaje de petición YAP con su cabecera correspondiente.

    :param carga: Datos que se desean enviar.
    :type carga: bytes

    :return: El mensaje YAP completo formado a partir de la carga.
    :rtype: bytes
    """
    cabecera: bytes = struct.pack("!3sHBHH", b"YAP", 0, 0, 0, 1)
    carga_codificada: bytes = base64.b64encode(carga)

    mensaje: bytes = cabecera + carga_codificada

    suma: int = cksum(mensaje)
    cabecera = struct.pack("!3sHBHH", b"YAP", 0, 0, suma, 1)

    return cabecera + carga_codificada


def desempaquetar_mensaje_yap(mensaje: bytes) -> bytes:
    """Deshace un mensaje YAP y devuelve los datos recibidos.

    :param mensaje: Mensaje YAP completo.
    :type mensaje: bytes

    :return: La carga decodificada.
    :rtype: bytes
    """
    numero_magico: bytes
    tipo: int
    codigo: int
    suma: int
    secuencia: int
    carga: bytes

    numero_magico, tipo, codigo, suma, secuencia = struct.unpack(
        "!3sHBHH", mensaje[:10]
    )
    carga = mensaje[10:]

    logging.debug("tipo: %d", tipo)
    logging.debug("codigo: %d", codigo)

    return base64.b64decode(carga)


def hito5(ip: str, puerto: int, identificador: bytes) -> bytes:
    """Prepara un mensaje YAP con el identificador.
    Lo manda al socket especificado y recibe la respuesta.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes

    :return: Los datos del mensaje recibido
    :rtype: bytes
    """
    recibido: bytes
    mensaje: bytes = preparar_peticion_yap(identificador)

    with socket.socket(type=socket.SOCK_DGRAM) as cliente:

        cliente.sendto(mensaje, (ip, puerto))

        recibido = cliente.recv(2048)

    return desempaquetar_mensaje_yap(recibido)


def escucha_errores(ip: str, puerto: int, mensaje: bytes) -> None:
    """Crea un cliente para la escucha al socket especificado.
    Manda el mensaje dado y se pone en bucle a escuchar mientras la conexión esté activa.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param mensaje: Mensaje a enviar al socket.
    :type mensaje: bytes
    """
    seguir_escuchando: bool = True
    recibido: bytes

    with socket.socket() as cliente_errores:
        cliente_errores.connect((ip, puerto))
        cliente_errores.sendall(mensaje)

        while seguir_escuchando:

            recibido = cliente_errores.recv(1024)
            logging.warning(recibido)
            seguir_escuchando = recibido != b""


def hacer_de_proxy(
    peticion: socket.socket, nombre_archivo: bytes, ip: str, puerto: int
) -> None:
    """Dado un socket que pide un archivo, se pasa esta petición a la ip y puerto especificados.
    El resultado se envía al socket.

    :param peticion: Socket que realiza la petición.
    :type peticion: socket.socket
    :param nombre_archivo: El nombre del archivo pedido por el socket.
    :type nombre_archivo: bytes
    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    """
    queda_por_enviar: bool = True
    recibido: bytes
    cabecera: bytes

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))
        # Petición http debe especificar host: https://www.rfc-editor.org/rfc/rfc2616#section-14.23
        # Opción de conexión no debe pasarse: https://www.rfc-editor.org/rfc/rfc2616#section-14.10
        # Cambio todas las opciones ya que se deja libertad.
        cabecera = (
            b"GET /rfc"
            + nombre_archivo
            + b" HTTP/1.1\r\n"
            + b"Host: "
            + ip.encode()
            + b":"
            + bytes(str(puerto), encoding="utf-8")
            + b"\r\n"
            + b"Connection: close\r\n\r\n"
        )

        cliente.sendall(cabecera)

        logging.debug(cabecera)

        while queda_por_enviar:
            recibido = cliente.recv(1024)
            peticion.sendall(recibido)
            queda_por_enviar = bool(recibido)


def tratar_peticion(peticion: socket.socket, ip: str, puerto: int) -> None:
    """Recibe una petición HTTP y decide si se trata de un archivo o del enunciado.
    Si es un archivo, actuaremos de proxy.
    Si es el enunciado, lo guardaremos en una variable global.

    :param peticion: Socket que realiza la petición.
    :type peticion: socket.socket
    :param ip: La dirección IP que nos provee de los archivos.
    :type ip: str
    :param puerto: El puerto que nos provee de los archivos.
    :type puerto: int
    """
    recibido: bytes
    uri: bytes

    global enunciado

    recibido = peticion.recv(1024)
    logging.debug(recibido)

    uri = recibido.split(b" ")[1]

    # deberíamos preguntar por la `query`
    pide_archivo = not uri.startswith(b"/submit")

    if pide_archivo:
        hacer_de_proxy(peticion, uri, ip, puerto)
    else:
        enunciado = urllib.parse.unquote(uri)[len(b"/submit?") :].encode()
        #peticion.sendall(b"HTTP/1.1 200 OK\r\n\r\n" + obtener_identificador(enunciado))

    peticion.close()


def bucle_aceptar(servidor: socket.socket, ip: str, puerto: int) -> None:
    """Bucle que acepta las peticiones de un servidor.
    Crea un hilo para cada petición.

    :param servidor: Socket servidor que acepta las peticiones.
    :type servidor: socket.socket
    :param ip: La dirección IP que nos provee de los archivos.
    :type ip: str
    :param puerto: El puerto que nos provee de los archivos.
    :type puerto: int
    """
    peticion: socket.socket
    global enunciado

    while enunciado is None:
        peticion, _ = servidor.accept()

        try:
            _thread.start_new_thread(tratar_peticion, (peticion, ip, puerto))
        except RuntimeError as re:
            # la yinkana no tiene suficientes recursos :////
            # no se puede hacer en un hilo a parte, toca hacerlo
            # de forma secuencial...
            tratar_peticion(peticion, ip, puerto)


def hito6(
    ip: str, puerto: int, identificador: bytes, ip_archivos: str, puerto_archivos: int
) -> bytes:
    """Envía el identificador a la dirección IP y puerto especificados.
    Se queda a la escucha de peticiones HTTP y actúa de proxy,
    recibiendo el identificador de la última petición.
    Ejecuta un bucle para la escucha de errores.

    :param ip: La dirección IP a la que enviaremos el mensaje.
    :type ip: str
    :param puerto: El puerto al que enviaremos el mensaje.
    :type puerto: int
    :param identificador: El identificador que enviaremos.
    :type identificador: bytes
    :param ip_archivos: La dirección IP que nos provee de los archivos.
    :type ip_archivos: str
    :param puerto_archivos: El puerto que nos provee de los archivos.
    :type puerto_archivos: int
    """
    conexiones_max: int = 4
    puerto_libre: int
    mensaje: bytes

    global enunciado
    enunciado = None

    with socket.socket() as servidor:
        servidor.bind(("", 0))
        puerto_libre = servidor.getsockname()[1]
        servidor.listen(conexiones_max)

        mensaje = identificador + b" " + bytes(str(puerto_libre), encoding="utf-8")

        _thread.start_new_thread(bucle_aceptar, (servidor, ip_archivos, puerto_archivos))

        escucha_errores(ip, puerto, mensaje)

    return enunciado

def hito7(ip: str, puerto: int, identificador: bytes) -> bytes:
    recibido: bytes

    with socket.socket() as cliente:
        cliente.connect((ip, puerto))

        cliente.sendall(identificador)

        recibido = cliente.recv(1024)

    return recibido


def main():
    """Función principal del script.
    Se encarga de ejecutar los hitos de la yinkana."""
    usuario: bytes = b"fast_rhino"
    recibido: bytes

    try:
        # Configuramos el logger para que muestre el nivel de log y el nombre de la función
        logging.basicConfig(
            format="%(levelname)s: %(funcName)s: %(message)s", level=logging.DEBUG
        )

        recibido = hito0("rick", 2000, usuario)

        logging.info(recibido.decode())

        recibido = hito1("rick", 4000, obtener_identificador(recibido))

        logging.info(recibido.decode())

        recibido = hito2("rick", 3010, obtener_identificador(recibido), 1000)

        logging.info(recibido.decode())

        recibido = hito3("rick", 6501, obtener_identificador(recibido))

        logging.info(recibido.decode())

        recibido = hito4("rick", 9000, obtener_identificador(recibido))

        logging.info(recibido.decode())

        recibido = hito5("rick", 6001, obtener_identificador(recibido))

        logging.info(recibido.decode())

        recibido = hito6("rick", 8003, obtener_identificador(recibido), "web", 81)

        logging.info(recibido.decode())

        # This was a triumph!
        # I'm making a note here:
        # "Huge success!!"
        # 
        # It's hard to overstate
        # My satisfaction.
        recibido = hito7("rick", 33333, obtener_identificador(recibido))

        logging.info(recibido.decode())

        # THE CAKE IS A LIE!!!!!!!

    except Exception as ex:
        logging.error("Error inesperado: %s", ex)


if __name__ == "__main__":
    main()
