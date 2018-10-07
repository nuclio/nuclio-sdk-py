.PHONY: all
all:
	$(error please pick a target)

.PHONY: upload
upload:
	rm -r dist
	python setup.py sdist bdist_wheel
	pipenv run twine upload dist/*

.PHONY: clean_pyc
clean_pyc:
	find . -name '*.pyc' -exec rm {} \;

.PHONY: flask8
flake8:
	pipenv run flake8 nuclio tests
