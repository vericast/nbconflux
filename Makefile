.PHONY: help clean dev-env sdist release test test-debug

# Shell that make should use
SHELL:=bash

help:
# http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: ## Make a clean source tree
	-find . -name '*.pyc' -exec rm -fv {} \;
	rm -rf nbconflux/__pycache__ __pycache__ dist *.egg-info

dev-env: ## Make a developer environment using pip install
	pip install -r requirements.txt -r requirements-test.txt

sdist: ## Make a source distribution
	python setup.py sdist

release: clean ## Make a pypi release of a tagged build
	python setup.py sdist register upload

test: clean ## Make a test run with coverage report
	python run_tests.py -vxrs tests/

test-debug: clean ## Make a test run with pdb enabled
	python run_tests.py -vxrs --pdb tests/
