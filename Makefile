# One-command entry points for the project.
#
# Required at the defense: `make run` must produce something visible
# in two commands or fewer. We make it a single command.

.PHONY: help install traces test plots run clean

help:
	@echo "Targets:"
	@echo "  install  -- pip install requirements"
	@echo "  traces   -- generate the synthetic trace files"
	@echo "  test     -- run the pytest suite (41 tests)"
	@echo "  plots    -- run every experiment and rebuild every plot"
	@echo "  run      -- install -> traces -> test -> plots (full pipeline)"
	@echo "  clean    -- remove generated traces and plots"

install:
	pip install -r requirements.txt

traces:
	python -m traces.generate_all

test:
	pytest tests/ -v

plots: traces
	python -m experiments.run_all

run: install traces test plots
	@echo ""
	@echo "Done. Plots are in experiments/plots/"
	@ls experiments/plots/

clean:
	rm -rf traces/data experiments/plots
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
