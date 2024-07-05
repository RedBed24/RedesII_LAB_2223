USER := fast_rhino
PORT := 2222
HOSTNAME := yinkana-host.duckdns.org
IDENTITYFILE := fast_rhino

MQTT_PASSWORD := iknSyrFN
MQTT_TOPIC := yinkana/fast_rhino/+
MQTT_HOST := mqtt
MQTT_PORT := 1234

SRC := yinkana_2324.py

all: send execute

send: $(SRC) $(IDENTITYFILE)
	scp -P $(PORT) -i $(IDENTITYFILE) $(SRC) $(USER)@$(HOSTNAME):

execute: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) ./$(SRC)

connect: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME)

doc: $(SRC)
	python3 -m pydoc yinkaana

debug: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) python3 -m pdb $(SRC)

mqtt:
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) mosquitto_sub -h $(MQTT_HOST) -p $(MQTT_PORT) -u $(USER) -P $(MQTT_PASSWORD) -t $(MQTT_TOPIC)

lint:
	pylint $(SRC)

type_check:
	mypy $(SRC)

format:
	ruff $(SRC)

clean:
	rm -rf *~ __pycache__/

.PHONY: clean mqtt execute send connect

