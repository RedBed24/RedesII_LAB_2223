# Usuario del servidor de la yincana
USER := boring_meninsky
# Ruta del fichero con la llave privada del usuario
IDENTITYFILE := ~/.ssh/$(USER)

# Nombre del archivo con el código
FILENAME := Yincana.py

DEPEND := inet_checksum.py

# Ip del servidor de la yincana
HOSTNAME := 161.22.47.12
# Puerto del servidor de la yincana que admite conexiones ssh
PORT := 2222


# regla por defecto
all: send execute

# envia el código al servidor, se pone en el directorio ~ del servidor
send: $(FILENAME) $(IDENTITYFILE)
	scp -P $(PORT) -i $(IDENTITYFILE) $(FILENAME) $(USER)@$(HOSTNAME):

# envia el código de dependencias al servidor
send_depend: $(DEPEND) $(IDENTITYFILE)
	scp -P $(PORT) -i $(IDENTITYFILE) $(DEPEND) $(USER)@$(HOSTNAME):

# ejecuta el fichero del código que se encuentra en el servidor de al yincana
execute: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) ./$(FILENAME)

# te conecta al servidor de la yincana; exit o control+d para salir
connect: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME)

# muestra la documentación escrita en el fichero de tu máquina
doc: $(FILENAME)
	python3 -m pydoc Yincana

# ejecuta la yincana en modo debug, no recomendado ya que esta tiene requisitos temporales
debug: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) python3 -m pdb $(FILENAME)

# limpia los ficheros no necesarios
clean:
	rm -rf *~ __pycache__/

