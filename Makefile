PIP = pip
PYTHON = python

dev:
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -r requirements-dev.txt
	$(PIP) install --upgrade --editable .

dist:
	rm -rf dist/
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	twine check dist/*

publish: dist
	twine upload dist/*