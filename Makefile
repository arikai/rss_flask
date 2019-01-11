PY = python3
APP = src/web.py

VENV = venv
VENV_ACTIVATE = . $(VENV)/bin/activate
VENV_DEACTIVATE = deactivate

REQUIREMENTS = requirements.txt

TEMP_FILES = data

all: $(VENV) data
	$(VENV_ACTIVATE) && \
	$(PY) $(APP) && \
	$(VENV_DEACTIVATE)

$(VENV):
	$(PY) -m venv $(VENV)
	$(VENV_ACTIVATE) && pip3 install -r $(REQUIREMENTS)

debug: data
	FLASK_DEBUG=1 FLASK_APP=$(WEBAPP_DEV) flask run

dev: data
	FLASK_APP=$(WEBAPP_DEV) FLASK_ENV=development flask run

data:
	mkdir -p data

clean:
	rm -r $(TEMP_FILES)

.PHONY: clean debug
