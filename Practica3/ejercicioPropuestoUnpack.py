import struct

# open a file in read bits mode
f = open('ListinLlamadas', 'rb')

datos = f.read(12)
while len(datos) == 12:

    UnpackedData = struct.unpack('!cciih', datos)

    hour = ord(UnpackedData[0])
    minutes = ord(UnpackedData[1])
    callerPhone = UnpackedData[2]
    reciverPhone = UnpackedData[3]
    duration = UnpackedData[4]

    print('The call made from {0} to {1} started at {2:2d}:{3:02d} and lasted {4} minutes'.format(callerPhone, reciverPhone, hour, minutes, duration))

    datos = f.read(12)

f.close()

