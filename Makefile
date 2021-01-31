PIPENV_PYTHON_VERSION  ?= 3.7


.PHONY: all
all:
	$(error please pick a target)

.PHONY: upload
upload: clean build lint test
	python -m pipenv run upload

.PHONY: build
build:
	python -m pipenv run build

.PHONY: clean
clean:
	@rm -rf dist build nuclio_sdk.egg-info

.PHONY: clean_pyc
clean_pyc:
	@find . -name '*.pyc' -exec rm {} \;

.PHONY: clean_all
clean_all: clean clean_pyc
	@echo "Done cleaning"

.PHONY: lint
lint:
	python -m pipenv run lint
	python -m pipenv run flake8

.PHONY: test
test:
	python -m pipenv run test

.PHONY: install_pipenv
install_pipenv:
	python -m pip install --user pipenv
	python -m pipenv --python ${PIPENV_PYTHON_VERSION}
	python -m pipenv install --dev
