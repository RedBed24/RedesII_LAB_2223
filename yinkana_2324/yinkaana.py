import socket
import json
import time
import base64

# Función para manejar la conexión y enviar la respuesta al Test Chamber 0
def test_chamber_0():
    SERVER = "rick"
    PORT = 2000
    ADDR = (SERVER, PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mi_conector:
        mi_conector.connect(ADDR)
        username = "rapid_gnat"
        data = mi_conector.recv(1024)
        received_text = data.decode()
        print("Mensaje recibido en TCP:", received_text)

        mi_conector.send(username.encode())

        data = mi_conector.recv(1024)
        received_text = data.decode()
        print("Mensaje recibido en TCP:", received_text)

        identifier = encontrar_identificador(received_text)

        print("Identificador extraído:", identifier)
        return identifier


# Función para encontrar el identificador en el mensaje recibido
def encontrar_identificador(received_text):
    identifier_index = received_text.find('identifier:')

    identifier_start_index = identifier_index + len('identifier:')
    identifier_end_index = received_text.find('\n', identifier_start_index)
    identifier = received_text[identifier_start_index:identifier_end_index].strip()

    return identifier


# Función para manejar el servidor UDP del Test Chamber 1
def test_chamber_1(identificador):
    SERVER_TC1 = "rick"
    PORT_TC1 = 4000
    puerto = 65002
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket_servidor:
        socket_servidor.bind(('', puerto))
        print(f"Servidor UDP listo y escuchando en el puerto {puerto}")

        mensaje = f"{puerto} {identificador}"
        socket_servidor.sendto(mensaje.encode(), (SERVER_TC1, PORT_TC1))
        print(f"Notificación enviada al servidor de la Yinkana: {mensaje}")

        while True:
            data, client = socket_servidor.recvfrom(1024)
            mensaje_recibido = data.decode()
            print("Mensaje recibido:", mensaje_recibido)
            if "upper-code?" in mensaje_recibido:
                respuesta = identificador.upper().encode()
                socket_servidor.sendto(respuesta, client)
                print("Respuesta enviada:", respuesta.decode())
            elif "identifier:" in mensaje_recibido:
                return encontrar_identificador(mensaje_recibido)
            elif not data:
                break

# Función para manejar la conexión y enviar la respuesta al Test Chamber 2
def test_chamber_2(identifier):
    SERVER_TC2 = "rick"
    PORT_TC2 = 3010
    ADDR_TC2 = (SERVER_TC2, PORT_TC2)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mi_conector_tc2:
        mi_conector_tc2.connect(ADDR_TC2)

        response = identifier + ' '
        suma = 0
        palabra = b""
        # Recibir datos del Test Chamber 2
        while True:
            chunk = palabra + mi_conector_tc2.recv(1024)
            print("Mensaje recibido en TCP Test Chamber 2:", chunk.decode())

            words = chunk.split(b" ")

            for word in words[:-1]:
                word_length_str = str(len(word))
                response += word_length_str + ' '
                suma += len(word)
                if suma >= 1000:
                    break

            if suma >= 1000:
                break

            palabra = words[-1]


        # Procesar la respuesta según el formato esperado
        response = response + '--'
        print("Respuesta enviada para Test Chamber 2:", response)

        # Enviar la respuesta al Test Chamber 2
        mi_conector_tc2.send(response.encode())
        print("Respuesta enviada correctamente.")

        # Esperar y procesar las instrucciones después del Test Chamber 2
        while True:
            data = mi_conector_tc2.recv(1024).decode()
            print("Mensaje recibido después de Test Chamber 2:", data)

            if "identifier:" in data:
                return encontrar_identificador(data)
            elif not data:
                break


# Función para manejar la conexión y enviar la respuesta al Test Chamber 3
def test_chamber_3(identifier):
    SERVER_TC3 = "rick"
    PORT_TC3 = 5501

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mi_conector_tc3:
        mi_conector_tc3.connect((SERVER_TC3, PORT_TC3))
        mi_conector_tc3.sendall(identifier.encode())

        suma = 0
        palabra = b""
        palabra_posterior = b""
        while True:
            data = palabra + mi_conector_tc3.recv(1024)
            print("Mensaje recibido en TCP Test Chamber 3:", data.decode())

            words = data.split(b" ")

            for word in words[:-1]:
                if word.isdigit():
                    suma += int(word.decode())
                else:
                    suma += 1

                if suma > 1200 and not word.isdigit():
                    palabra_posterior = word
                    break


            if suma > 1200 and palabra_posterior:
                break

            palabra = words[-1]

        mi_conector_tc3.sendall(palabra_posterior)
        print("Palabra enviada al servidor:", palabra_posterior.decode())

        while True:
            data = mi_conector_tc3.recv(1024).decode()
            print("Mensaje recibido después de Test Chamber 3:", data)

            if "identifier:" in data:
                return encontrar_identificador(data)
            elif not data:
                break

# Función para manejar la conexión y enviar la respuesta al Test Chamber 4
def test_chamber_4(identifier):
    SERVER_TC4 = "rick"
    PORT_TC4 = 3061

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mi_conector_tc4:
        mi_conector_tc4.connect((SERVER_TC4, PORT_TC4))
        mi_conector_tc4.sendall(identifier.encode())

        while True:
            # Receive data from the server
            data = b""
            while True:
                chunk = mi_conector_tc4.recv(1024)
                data += chunk

                try:
                    received_json = json.loads(data)
                    break
                except json.JSONDecodeError:
                    pass

            print("Mensaje recibido en TCP Test Chamber 4:", received_json)
            # Extract the relevant information
            player = "rapid_gnat"
            sentence = received_json.get("sentence", "")
            
            # Find all uppercase letters in the sentence
            upperletters = [char for char in sentence if char.isupper()]
            
            # Create the response JSON
            response = {
                "player": player,
                "timestamp": int(time.time()),
                "upperletters": upperletters
            }
            
            print("Respuesta enviada para Test Chamber 4:", response)

            # Serialize the response to JSON
            response_json = json.dumps(response)
            
            # Send the response back to the server
            mi_conector_tc4.sendall(response_json.encode())
            
            if "identifier:" in sentence:
                print("Identificador encontrado en la oración:", sentence)
                return encontrar_identificador(sentence)
            elif not data:
                break

#!/usr/bin/python3
"Internet checksum algorithm RFC-1071"
# from scapy:
# https://github.com/secdev/scapy/blob/master/scapy/utils.py

import sys
import struct
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

def test_chamber_5(identifier):
    SERVER_TC5 = "rick"
    PORT_TC5 = 6001

    encoded_payload = base64.b64encode(identifier.encode())
    # Construct the header
    type = 0  # request
    code = 0  # no-error
    sequence = 1  # sequence number, can be incremented for each message
    header_without_checksum = struct.pack('!3sHBHH', b'YAP', type, code, 0, sequence)

    # Calculate checksum
    full_message_without_checksum = header_without_checksum + encoded_payload
    checksum = cksum(full_message_without_checksum)

    # Construct the final header with checksum
    header = struct.pack('!3sHBHH', b'YAP', type, code, checksum, sequence)

    # Create the full message
    message = header + encoded_payload

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as mi_conector_tc5:
        mi_conector_tc5.sendto(message, (SERVER_TC5, PORT_TC5))
        print("Mensaje enviado al servidor UDP Test Chamber 5:")

        response, _ = mi_conector_tc5.recvfrom(2048)

        # Process the response
        if response.startswith(b'YAP'):
            # Unpack the header
            response_header = response[:10]
            response_payload = response[10:]
            yap, r_type, r_code, r_checksum, r_sequence = struct.unpack('!3sHBHH', response_header)
            
            # Decode the payload from base64
            decoded_payload = base64.b64decode(response_payload).decode()
            print("Received instructions:", decoded_payload)
            return encontrar_identificador(decoded_payload)
        else:
            print("Invalid response format.")




# Función principal para manejar la comunicación inicial y lanzar el servidor UDP
def main():
    identificador = test_chamber_0()
    identificador = test_chamber_1(identificador)
    identificador = test_chamber_2(identificador)
    identificador = test_chamber_3(identificador)
    identificador = test_chamber_4(identificador)
    identificador = test_chamber_5(identificador)

if __name__ == "__main__":
    main()
