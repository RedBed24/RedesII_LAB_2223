#!/usr/bin/env python3
"""Collection of functions to solve the Yinkana challenge."""

import socket
import logging
import re
import json
import time
import base64
import sys
import struct
import array
import _thread


logging.basicConfig(
    format="%(levelname)s: %(funcName)s: %(message)s", level=logging.INFO
)


def cksum(pkt: bytes) -> int:
    # pylint: disable=invalid-name disable=missing-function-docstring
    if len(pkt) % 2 == 1:
        pkt += b"\0"
    s = sum(array.array("H", pkt))
    s = (s >> 16) + (s & 0xFFFF)
    s += s >> 16
    s = ~s

    if sys.byteorder == "little":
        s = ((s >> 8) & 0xFF) | s << 8

    return s & 0xFFFF


def get_message_identifier(message: bytes) -> bytes:
    """Obtains the identifier from the message.

    Args:
        message (bytes): The message that contains the identifier.

    Returns:
        bytes: The identifier of the message.
    """
    return re.search(b"identifier:(.+)", message).group(1)  # type: ignore


def chamber_0(target_ip: str, target_port: int, username: bytes) -> bytes:
    """Sends the username to the specified IP address and port.
    Returns the next chamber prompt.

    Args:
        target_ip (str): The IP address to send the username to.
        target_port (int): The port to send the username to.
        username (str): The username to send.

    Returns:
        bytes: The next chamber prompt.
    """
    received_data: bytes

    with socket.socket() as client_socket:
        client_socket.connect((target_ip, target_port))

        received_data = client_socket.recv(1024)
        logging.info(received_data.decode())

        client_socket.sendall(username)

        received_data = client_socket.recv(1024)
        logging.debug(received_data)

    return received_data


def chamber_1(target_ip: str, target_port: int, chamber_id: bytes) -> bytes:
    """Sends the chamber_id and a free port to the target IP address and port.
    Returns the next chamber prompt.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.

    Returns:
        bytes: The next chamber prompt.
    """
    received_data: bytes

    with socket.socket(type=socket.SOCK_DGRAM) as udp_server_socket:
        udp_server_socket.bind(("", 0))
        unused_port: int = udp_server_socket.getsockname()[1]
        message: bytes = str(unused_port).encode() + b" " + chamber_id

        udp_server_socket.sendto(message, (target_ip, target_port))

        received_data, client_socket = udp_server_socket.recvfrom(1024)

        logging.debug(received_data.decode())

        if received_data == b"upper-code?":
            logging.debug("upper-code request recieved from %s", str(client_socket))

            udp_server_socket.sendto(chamber_id.upper(), client_socket)

            received_data = udp_server_socket.recv(1024)

    return received_data


def word_count_flag(sender_tcp_socket: socket.socket, flag: bytes) -> int:
    """Reads and counts words from a TCP socket until a flag is found.
    A word is considered to be a sequence of characters separated by a space or a newline.

    Args:
        sender_tcp_socket (socket.socket): The TCP socket from which to receive messages.
        flag (bytes): The flag to search for in the received data.

    Returns:
        int: The number of words received before the flag.
    """
    word_count: int = 0
    flag_found: bool = False

    # used to store the last bytes received in case the flag is split between two messages
    previous_bytes: bytes = b""

    while not flag_found:
        received_data: bytes = previous_bytes + sender_tcp_socket.recv(1024)
        i: int = 0

        logging.debug(received_data)

        while not flag_found and i < len(received_data) - len(flag):
            if received_data[i : i + len(flag)] == flag:
                flag_found = True
            elif received_data[i] == ord(" ") or received_data[i] == ord("\n"):
                word_count += 1

            i += 1

        previous_bytes = received_data[-len(flag) :]

    return word_count


def chamber_2(
    target_ip: str, target_port: int, chamber_id: bytes, flag: bytes
) -> bytes:
    """Sends the chamber_id and the number of words before a flag to the target IP address and port.
    Returns the next chamber prompt.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.
        flag (bytes): The flag to search for in the received data.

    Returns:
        bytes: The next chamber prompt.
    """
    next_chamber_prompt: bytes = b""

    with socket.socket() as client_socket:
        client_socket.connect((target_ip, target_port))

        message: bytes = (
            chamber_id + b" " + str(word_count_flag(client_socket, flag)).encode()
        )

        logging.debug("message: %s", str(message))

        client_socket.sendall(message)

        while not next_chamber_prompt:
            received_data: bytes = client_socket.recv(2048)

            logging.debug(received_data)

            if received_data.startswith(b"identifier:"):
                next_chamber_prompt = received_data
            elif not received_data:
                # pylint: disable=broad-exception-raised
                raise Exception("No data received...")

    return next_chamber_prompt


def read_last_x_words(tcp_socket: socket.socket) -> bytes:
    """Reads words from a TCP socket until a number is found, Returns the last X words read.

    Args:
        tcp_socket (socket.socket): The TCP socket from which to receive messages.

    Returns:
        bytes: The last X words read from the socket.
    """
    num_words: int = 0

    end: int = 0

    received_data: bytes = b""

    while not num_words:
        received_data += tcp_socket.recv(1024)

        logging.debug(received_data)

        while not num_words and end < len(received_data):
            if chr(received_data[end]).isdigit():
                while not num_words:
                    number_bytes: list[bytes] = received_data[end:].split(b" ", 1)

                    if len(number_bytes) > 1:
                        num_words = int(number_bytes[0].decode())
                    else:
                        received_data += tcp_socket.recv(1024)
                        logging.debug(received_data)

            end += 1

    logging.debug("num words: %d", num_words)

    end -= 2
    start: int = end

    while num_words > 0:
        start -= 1
        if received_data[start] == ord(" "):
            num_words -= 1

    return received_data[start + 1 : end]


def encrypt_char(char: int, alphabet: bytes) -> int:
    """Encrypts a character using a given alphabet.

    Args:
        char (int): The character to encrypt.
        alphabet (bytes): The alphabet to use for encryption.

    Returns:
        int: The encrypted character.
    """
    if chr(char).isalpha():
        return alphabet[ord(chr(char).lower()) - ord("a")]
    return char


def chamber_3(target_ip: str, target_port: int, chamber_id: bytes) -> bytes:
    """Sends the chamber_id and then reads words and encrypts them using the received alphabet.
    Reads a number X from the socket and returns the last X encrypted words.
    Returns the next chamber prompt.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.

    Returns:
        bytes: The next chamber prompt.
    """
    next_chamber_prompt: bytes = b""

    with socket.socket() as client_socket:
        client_socket.connect((target_ip, target_port))
        client_socket.sendall(chamber_id)

        encrypted_alphabet: bytes = client_socket.recv(26)
        logging.debug("encrypted alphabet: %s", encrypted_alphabet)

        words: bytes = read_last_x_words(client_socket)
        logging.debug(words)

        encrypted_words: bytes = bytes(
            map(lambda x: encrypt_char(x, encrypted_alphabet), words)
        )
        client_socket.sendall(encrypted_words + b" --")

        while not next_chamber_prompt:
            receive_data: bytes = client_socket.recv(2048)

            logging.debug(receive_data)

            if receive_data.startswith(b"identifier:"):
                next_chamber_prompt = receive_data
            elif not receive_data:
                # pylint: disable=broad-exception-raised
                raise Exception("No data received...")

    return next_chamber_prompt


def chamber_4(
    target_ip: str, target_port: int, chamber_id: bytes, username: str
) -> bytes:
    """Sends the chamber_id to the target IP address and port.
    Then, reads jsons until they are complete, extracts the uppercase letters from the sentence.
    Finally, sends the uppercase letters, username and timestamp to the target IP address and port.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.
        username (str): The username to send.

    Returns:
        bytes: The next chamber prompt.
    """
    next_chamber_prompt: bytes = b""

    with socket.socket() as client_socket:
        client_socket.connect((target_ip, target_port))
        client_socket.sendall(chamber_id)

        while not next_chamber_prompt:
            received_data: bytes = b""
            data_is_complete: bool = False
            request: dict[str, str] = {}

            while not data_is_complete:
                received_data += client_socket.recv(1024)
                logging.debug(received_data)

                try:
                    request = json.loads(received_data)
                    data_is_complete = True
                except json.JSONDecodeError:
                    pass

            logging.debug(request)

            sentence: str = request["sentence"]
            uppers: list[str] = list(filter(lambda x: x.isupper(), sentence))
            message: bytes = json.dumps(
                {
                    "player": username,
                    "upperletters": uppers,
                    "timestamp": int(time.time()),
                }
            ).encode()
            logging.debug("message: %s", str(message))
            client_socket.sendall(message)

            if sentence.startswith("identifier:"):
                next_chamber_prompt = sentence.encode()

    return next_chamber_prompt


def chamber_5(target_ip: str, target_port: int, chamber_id: bytes) -> bytes:
    """Creates a YAP request with the chamber_id as payload.
    Sends the request to the target IP address and port.
    Returns the decoded response.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.

    Returns:
        bytes: The decoded response.
    """
    no_sum_header: bytes = struct.pack("!3sHBHH", b"YAP", 0, 0, 0, 1)
    encoded_payload: bytes = base64.b64encode(chamber_id)
    checksum: int = cksum(no_sum_header + encoded_payload)
    full_header: bytes = struct.pack("!3sHBHH", b"YAP", 0, 0, checksum, 1)

    logging.debug(full_header)

    received_data: bytes
    with socket.socket(type=socket.SOCK_DGRAM) as client_udp_socket:
        client_udp_socket.sendto(
            full_header + encoded_payload, (target_ip, target_port)
        )

        received_data = client_udp_socket.recv(2048)

    logging.debug(received_data)

    return base64.b64decode(received_data[10:])


def error_message_listener(
    target_ip: str, target_port: int, first_message: bytes
) -> None:
    """Listens for error messages from the target IP and port.
    Logs the received messages.
    Sends the first message to the target IP and port.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        first_message (bytes): The first message to send.

    Returns:
        None
    """
    with socket.socket() as error_listener_client:
        error_listener_client.connect((target_ip, target_port))
        error_listener_client.sendall(first_message)

        while received_data := error_listener_client.recv(1024):
            logging.warning(received_data)


def bucle_aceptar(
    http_server_socket: socket.socket, http_provider_ip: str, http_provider_port: int
) -> bytes:
    """Accepts incoming HTTP requests and proxies them to a provider.
    Returns the next chamber prompt received as a POST request.

    Args:
        http_server_socket (socket.socket): The socket to accept incoming requests.
        http_provider_ip (str): The IP address of the provider.
        http_provider_port (int): The port of the provider.

    Returns:
        bytes: The next chamber prompt.
    """
    next_chamber_prompt: bytes = b""
    while not next_chamber_prompt:
        petition_socket, _ = http_server_socket.accept()

        received_data: bytes = petition_socket.recv(1024)
        logging.debug("incoming request %s", str(received_data))

        if received_data.startswith(b"GET"):
            uri: bytes = b"/rfc/" + received_data.split(b" ")[1]
            try:
                _thread.start_new_thread(
                    proxy_request,
                    (petition_socket, uri, http_provider_ip, http_provider_port),
                )
            except RuntimeError:
                proxy_request(
                    petition_socket, uri, http_provider_ip, http_provider_port
                )
        else:
            next_chamber_prompt = petition_socket.recv(1024)
            petition_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

    return next_chamber_prompt


def proxy_request(
    incoming_request_socket: socket.socket,
    uri: bytes,
    http_provider_ip: str,
    http_provider_port: int,
) -> None:
    """Creates a HTTP request to a provider and sends the response to the incoming socket.

    Args:
        incoming_request_socket (socket.socket): The socket that made the request.
        uri (bytes): The URI to request.
        http_provider_ip (str): The IP address of the provider.
        http_provider_port (int): The port of the provider.

    Returns:
        None
    """
    http_header: bytes = (
        b"GET "
        + uri
        + b" HTTP/1.1\r\nHost: "
        + http_provider_ip.encode()
        + b":"
        + str(http_provider_port).encode()
        + b"\r\nConnection: close\r\n\r\n"
    )
    logging.debug("outgoing header: %s", str(http_header))

    with socket.socket() as outgoing_client_socket:
        outgoing_client_socket.connect((http_provider_ip, http_provider_port))
        outgoing_client_socket.sendall(http_header)

        while data := outgoing_client_socket.recv(1024):
            incoming_request_socket.sendall(data)

    incoming_request_socket.close()


def chamber_6(
    target_ip: str,
    target_port: int,
    chamber_id: bytes,
    http_provider_ip: str,
    http_provider_port: int,
    concurrent_connection_limit: int = 4,
) -> bytes:
    """Sends the chamber_id and listens for incoming HTTP requests.
    Proxies the requests to a provider.
    Returns the next chamber prompt received as a POST request.
    Starts a thread to listen for error messages from the target IP and port.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.
        http_provider_ip (str): The IP address of the provider.
        http_provider_port (int): The port of the provider.
        concurrent_connection_limit (int): The maximum number of concurrent connections.

    Returns:
        bytes: The next chamber prompt.
    """
    next_chamber_prompt: bytes = b""

    with socket.socket() as http_server_socket:
        http_server_socket.bind(("", 0))
        free_port: int = http_server_socket.getsockname()[1]
        http_server_socket.listen(concurrent_connection_limit)

        _thread.start_new_thread(
            error_message_listener,
            (
                target_ip,
                target_port,
                chamber_id + b" " + str(free_port).encode(),
            ),
        )

        next_chamber_prompt = bucle_aceptar(
            http_server_socket, http_provider_ip, http_provider_port
        )

    return next_chamber_prompt


def chamber_7(target_ip: str, target_port: int, chamber_id: bytes) -> bytes:
    """Sends chamber_id and obtains cake.

    Args:
        target_ip (str): The target IP address to send the message to.
        target_port (int): The target port to send the message to.
        chamber_id (bytes): The identifier to send.

    Returns:
        bytes: The cake.
    """
    received_data: bytes
    with socket.socket() as client_socket:
        client_socket.connect((target_ip, target_port))
        client_socket.sendall(chamber_id)
        received_data = client_socket.recv(1024)
    return received_data


def main() -> None:
    """Main function to solve the Yinkana challenge."""
    try:
        received_data: bytes = chamber_0("rick", 2000, b"on_eagle")
        logging.info(received_data.decode())

        received_data = chamber_1("rick", 4000, get_message_identifier(received_data))
        logging.info(received_data.decode())

        received_data = chamber_2(
            "rick", 3002, get_message_identifier(received_data), b"that's the end"
        )
        logging.info(received_data.decode())

        received_data = chamber_3("rick", 6510, get_message_identifier(received_data))
        logging.info(received_data.decode())

        received_data = chamber_4(
            "rick", 3061, get_message_identifier(received_data), "on_eagle"
        )
        logging.info(received_data.decode())

        received_data = chamber_5("rick", 6001, get_message_identifier(received_data))
        logging.info(received_data.decode())

        received_data = chamber_6(
            "rick", 8002, get_message_identifier(received_data), "web", 81
        )
        logging.info(received_data.decode())

        received_data = chamber_7("rick", 33333, get_message_identifier(received_data))
        logging.info(received_data.decode())

        # This was a triumph.
        # I'm making a note here:
        # huge success.
        #
        # It's hard to overstate
        # My satisfaction.
        #
        # Redes II.
        # We do what we must
        # Because we can.
        # For the good of all of us.
        # Except the ones who are failed.
        #
        # But there's no sense crying
        # Over every mistake.
        # You just keep on trying
        # Till you run out of cake.
        # And the Science gets done.
        # And you make a neat code.
        # For the people who are
        # Still in 1º.
        #
        # I'm not even angry.
        # I'm being so sincere right now.
        # Even though you broke my heart.
        # And failed me.
        #
        # And tore the marks to pieces.
        # And failed every piece into a fire.
        # As they burned it hurt because
        # I was so happy for you!
        #
        # Now these points of data
        # Make a beautiful line.
        # And we're out of beta.
        # We're releasing on time.
        # So I'm RICE. I got failed.
        # Think of all the things we learned
        # For the people who are
        # Still in 1º.
        #
        # Go ahead and leave me.
        # I think I prefer to stay inside.
        # Maybe you'll find someone else
        # To help you.
        # Maybe OrCo...
        # THAT WAS A JOKE, HA HA, FAT CHANCE.
        #
        # Anyway this cake is great
        # It's so delicious and moist
        #
        # Look at me still talking when there's science to do
        # When I look out there
        # It makes me RICE I'm not you.
        #
        # I've experiments to run
        # There is research to be done
        # On the people who are
        # Still in 1º.
        #
        # And believe me I am still in 1º
        # I'm doing science and I'm still in 1º
        # I feel FANTASTIC and I'm still in 1º
        # While you're dying I'll be still in 1º
        # And when you're dead I will be still in 1º
        # Still in 1º
        # Still in 1º.

    except Exception as ex:  # pylint: disable=broad-exception-caught
        logging.error("Unexpected error: %s", ex)


if __name__ == "__main__":
    main()
