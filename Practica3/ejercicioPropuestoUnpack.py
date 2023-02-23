import struct

# open a file in read bits mode
f = open('ListinLlamadas', 'rb')

# se intentan leer datos, 12 bytes ya que es lo que ocupa cada registo, este tamaño viene dado por 'cciih'
packedData = f.read(12)

# Mientras nos queden datos por leer (y estos ocupen lo que queremos)
while len(packedData) == 12:

    # desempaquetamos los datos en 2 chars, 2 int y 1 short
    UnpackedData = struct.unpack('!cciih', packedData)

    # pasamos a Byte (dato numérico) los chars
    hour = ord(UnpackedData[0])
    minute = ord(UnpackedData[1])

    # 2 int 4B
    callerPhone = UnpackedData[2]
    reciverPhone = UnpackedData[3]

    # short 2B
    duration = UnpackedData[4]

    # mostramos la información leída
    print('The call made from {0} to {1} started at {2:2d}:{3:02d} and lasted {4} minutes'.format(callerPhone, reciverPhone, hour, minute, duration))

    # intentamos leer los siguientes datos
    datos = f.read(12)

# cerramos el archivo
f.close()

