import struct

try:
    # i: Fichero que contiene las llamadas (1 por línea) en formato
    # hora,minuto,telefono1,telefono2,duracion

    # o: Fichero donde pondremos los datos empaquetados 
    with open('data/Llamadas.txt', 'r') as i, open('data/dummy~', 'wb') as o:

        # Leemos cada línea
        for line in i:
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
            print(f"Succesfully processed line: {line}", end = "")

except FileNotFoundError as fnfe:
    print("The file does not exit")
except KeyboardInterrupt as ki:
    print("The process has been killed")

