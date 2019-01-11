PY = python3
APP = src/web.py

all: data
	$(PY) $(APP)

debug: data
	FLASK_DEBUG=1 FLASK_APP=$(WEBAPP_DEV) flask run

dev: data
	FLASK_APP=$(WEBAPP_DEV) FLASK_ENV=development flask run

data:
	mkdir -p data

.PHONY: report
