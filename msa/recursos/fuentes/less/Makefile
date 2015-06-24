DATE=$(shell date +%I:%M%p)
CHECK=\033[32m✔\033[39m
DEBUG=False
LESS_FILES := $(wildcard *.less)
CSS_FILES=$(LESS_FILES:.less=.css)
LESS_DIR=./less/
CSS_DIR=../../../voto/gui/templates/css/
HR=\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#\#
FLAVOR=`export PYTHONPATH=/opt/eleccion; /opt/env_eleccion/bin/python /opt/eleccion/msa/tools/obtener_flavor.py`
	
ifeq ($(DEBUG),True)
	    LESSC=lessc --modify-var=\"flavor=$(FLAVOR)\"
	else
	    LESSC=lessc --modify-var=flavor=$(FLAVOR) -x
	endif

less: $(CSS_FILES)
	@echo "\n${HR}"
	@echo "Compilación LESS con $(LESSC)...               ${CHECK} Listo!"
	@echo "\n${HR}"
%.css: %.less
	 $(LESSC) $< > $(CSS_DIR)$@
