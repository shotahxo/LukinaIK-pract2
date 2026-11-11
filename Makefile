PYTHON ?= python3
export PYTHONPATH := src:tests

.PHONY: run test errors

run:
	$(PYTHON) -m depviz

test:
	$(PYTHON) -m unittest discover -s tests -v

errors:
	./scripts/check_config_errors.sh
