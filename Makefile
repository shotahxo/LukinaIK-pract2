PYTHON ?= python3
export PYTHONPATH := src:tests

.PHONY: run test errors

run:
	$(PYTHON) -m depviz

test:
	$(PYTHON) -m unittest discover -s tests -v

errors:
	./scripts/check_config_errors.sh

.PHONY: mini-index serve

mini-index:
	$(PYTHON) examples/build_mini_index.py

serve: mini-index
	$(PYTHON) -m http.server 8000 --directory examples/mini-index

.PHONY: demo-graph

demo-graph:
	./scripts/demo_graph.sh

.PHONY: demo-reverse

demo-reverse:
	./scripts/demo_reverse.sh

.PHONY: demo-visual demo-real

demo-visual:
	./scripts/demo_visual.sh

demo-real:
	./scripts/demo_real.sh
