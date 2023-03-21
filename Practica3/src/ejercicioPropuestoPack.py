import struct

PATH_TO_INPUT_FILE = "data/Llamadas.txt"
PATH_TO_OUTPUT_FILE = "data/output~"

try:
	# inputFile: Fichero que contiene las llamadas (1 por línea) en formato
	# hora,minuto,teléfono1,teléfono2,duración

	# outputFile: Fichero donde pondremos los datos empaquetados
	with open(PATH_TO_INPUT_FILE, "r") as inputFile, open(PATH_TO_OUTPUT_FILE, "wb") as outputFile:

		# Leemos cada línea
		for line in inputFile:
			# Separamos la linea por las ","
			data = line.split(",")
			
			# se pasa a entero (porque estaba en String) y ese se convierte a char (para forzar que sea 1 Byte), luego, se codifica
			hour = chr(int(data[0])).encode()
			minute = chr(int(data[1])).encode()

			# sólo se pasa a entero, suponemos que tienen el tamaño esperado 4B y 2B
			callerPhone = int(data[2])
			reciverPhone = int(data[3])
			duration = int(data[4])

			# empaquetamos los datos en el orden esperado
			packedData = struct.pack("!cciih", hour, minute, callerPhone, reciverPhone, duration)

			# Escribimos los datos empaquetados en el archivo
			outputFile.write(packedData)
			print(f"Succesfully processed line: {line}", end = "")

except FileNotFoundError as fnfe:
	print(f"The \"{PATH_TO_INPUT_FILE}\" file does not exit.")
except KeyboardInterrupt as ki:
	print(f"The process has been killed.")
except IndexError as ie:
	print(f"Error trying to obtain a field from the file \"{PATH_TO_INPUT_FILE}\".")

