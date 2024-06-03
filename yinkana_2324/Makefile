USER := fast_rhino
PORT := 2222
HOSTNAME := yinkana-host.duckdns.org
IDENTITYFILE := fast_rhino

MQTT_PASSWORD := iknSyrFN
MQTT_TOPIC := yinkana/fast_rhino/+
MQTT_HOST := mqtt
MQTT_PORT := 1234

SRC := yinkana_2324.py

connect: config ${IDENTITYFILE}
	ssh -F config yinkana

send: config ${IdentityFile} ${SRC}
	scp -F config ${SRC} yinkana:

execute: send
	ssh -F config yinkana ./${SRC}

config:
	echo "Host yinkana" >> config
	echo "	User ${USER}" >> config
	echo "	HostName ${HOSTNAME}" >> config
	echo "	Port ${PORT}" >> config
	echo "	IdentityFile ${IDENTITYFILE}" >> config

mqtt:
	ssh -F config yinkana mosquitto_sub -h ${MQTT_HOST} -p ${MQTT_PORT} -u ${USER} -P ${MQTT_PASSWORD} -t ${MQTT_TOPIC}

lint:
	pylint ${SRC}

type_check:
	mypy ${SRC}

format:
	ruff ${SRC}

clean:
	rm *~
	rm config

.PHONY: clean mqtt execute send connect

