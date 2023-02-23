import socket

a = 0b101010
b = 0o52
c = 0x2A

bin(42)
oct(42)
hex(42)

# Python solo tiene un tipo para enternos (ni byte, ni long, ...)

# Devuelve el tipo (entero) de una variable
type(10 ** 100)

# char <=> int

# Devuelve el código ASCII de un char
ord('a')

# Dado un código ASCII, devuelve el char
chr(97)

a = 'cadena'

# devuelve la codificación ascii de cadena
b = bytes('cadena', 'ascii')

# igual que el anterior, pero mutable
c = bytearray('cadena', 'ascii')

# al imprimir una secuencia de bytes, te marca al principio que son bytes, con una b, si se encuentra un carácter raro como ñ, este se divide en varios bytes
# al usar bytearray no obtienes la representación del ascii

# little endian es más eficiente, ¿porqué?

# la arquitectura para networking es big-endian mientras que la gran mayoria de procesadores usan little endian
# socket permite convertir una a otra independientemente de en qué trabaje el host y la red
#socket.ntohs()
# ntohl, htons, htonl
# n: network, h: host, s: short, l: long

# Da error ya que la ñ no existe para ascii
#bytes('España', 'ascii')
bytes('España', 'utf-8')

# quedaría 'Espan~a'

# Struct

# Devuelve una secuencia de bytes con los datos
# pack(mascara, objetos, a, serializar)
# mascara:=
# {@ (nativo), = (nativo), < (little-endian), > (big), ! (network)} U
# formato de los datos:= {c (char), ...}

# Ejemplo:
#                      mask  dirección dest  orig direccion       datos
header = struct.pack('!6s6sh', b'\xFF' * 6, b'\xC4\x85\x08\xED\xD3\x07', )
# mask
# ! sigue el endianes de la network
# 6s van 6 chars (bytes) (dirección destino)
# 6s van otros 6 chars (bytes) (dirección origen)
# h va un número

# unpack()
struct.unpack('!6s6sh', header)

