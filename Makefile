PIP = pip

dev:
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements-dev.txt
	$(PIP) install --upgrade --editable .
