USER := boring_meninsky
IDENTITYFILE := ~/.ssh/$(USER)

FILENAME := Yincana.py

HOSTNAME := 161.22.47.12
PORT := 2222


all: send execute

send: $(FILENAME) $(IDENTITYFILE)
	scp -P $(PORT) -i $(IDENTITYFILE) $(FILENAME) $(USER)@$(HOSTNAME):

execute: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME) ./$(FILENAME)

connect: $(IDENTITYFILE)
	ssh -p $(PORT) -i $(IDENTITYFILE) $(USER)@$(HOSTNAME)

