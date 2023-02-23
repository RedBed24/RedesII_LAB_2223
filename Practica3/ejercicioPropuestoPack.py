import struct

# Fichero que contiene las llamadas (1 por línea) en formato
# hora,minuto,telefono1,telefono2,duracion
f = open('Llamadas.txt', 'r')

# Fichero donde pondremos los datos empaquetados 
o = open('dummy~', 'wb')

# Leemos cada línea
for line in f:
    # Separamos la linea por las ','
    data = line.split(',')
    
    # se pasa a entero (porque estaba en String) y ese se convierte a char (para forzar que sea 1 Byte), luego, se codifica
    hour = chr(int(data[0])).encode()
    minute = chr(int(data[1])).encode()

    # sólo se pasa a entero, suponemos que tienen el tamaño esperado 4B y 2B
    callerPhone = int(data[2])
    reciverPhone = int(data[3])
    duration = int(data[4])

    # empaquetamos los datos en el orden esperado
    packedData = struct.pack('!cciih', hour, minute, callerPhone, reciverPhone, duration)

    # Escribimos los datos empaquetados en el archivo
    o.write(packedData)

# cerramos los ficheros
f.close()
o.close()

