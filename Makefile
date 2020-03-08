PIPENV_PYTHON_VERSION  ?= 3.6


.PHONY: all
all:
	$(error please pick a target)

.PHONY: upload
upload: clean build
	python -m pipenv run upload

.PHONY: build
build:
	python -m pipenv run build

.PHONY: clean
clean:
	rm -rf dist build nuclio_sdk.egg-info

.PHONY: clean_pyc
clean_pyc:
	find . -name '*.pyc' -exec rm {} \;

.PHONY: flake8
flake8:
	python -m pipenv run flake8

.PHONY: test
test:
	python -m pipenv run test

.PHONY: install_pipenv
install_pipenv:
	python -m pip install --user pipenv
	python -m pipenv --python ${PIPENV_PYTHON_VERSION}
ifeq ($(PIPENV_PYTHON_VERSION), 2.7)
	python -m pipenv install -r requirements.py2.txt
else
	python -m pipenv install --dev
endif
