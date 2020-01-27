.PHONY: all
all:
	$(error please pick a target)

.PHONY: upload
upload: clean build
	pipenv run twine upload dist/*

.PHONE: build
build:
	python setup.py sdist bdist_wheel

.PHONE: clean
clean:
	rm -rf dist

.PHONY: clean_pyc
clean_pyc:
	find . -name '*.pyc' -exec rm {} \;

.PHONY: flask8
flake8:
	pipenv run flake8 nuclio tests
