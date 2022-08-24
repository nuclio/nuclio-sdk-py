# Copyright 2018 The Nuclio Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
PIPENV_PYTHON_VERSION ?= 3.7
NUCLIO_SDK_PY_VERSION ?= $(shell git describe --tags --abbrev=0)

.PHONY: all
all:
	$(error please pick a target)

.PHONY: upload
upload: ensure-version clean build lint test
	python -m pipenv run upload

.PHONY: build
build: ensure-version
	python -m pipenv run build

.PHONY: clean
clean:
	@rm -rf VERSION dist build nuclio_sdk.egg-info

.PHONY: clean_pyc
clean_pyc:
	@find . -name '*.pyc' -exec rm {} \;

.PHONY: clean_all
clean_all: clean clean_pyc
	@echo "Done cleaning"

.PHONY: fmt
fmt:
	python -m pipenv run fmt

.PHONY: lint
lint:
	python -m pipenv run flake8
	python -m pipenv run lint

.PHONY: test
test:
	python -m pipenv run test

.PHONY: install_pipenv
install_pipenv: ensure-version
	python -m pip install --user pipenv
	python -m pipenv --python ${PIPENV_PYTHON_VERSION}
	python -m pipenv install --dev

.PHONY: ensure-version
ensure-version:
	@echo $(NUCLIO_SDK_PY_VERSION) | tee VERSION
