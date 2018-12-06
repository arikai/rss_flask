PY = python3
APP = src/web.py

all:
	$(PY) $(APP)

debug:
	FLASK_DEBUG=1 FLASK_APP=$(WEBAPP_DEV) flask run

dev:
	FLASK_APP=$(WEBAPP_DEV) FLASK_ENV=development flask run

.PHONY: report
