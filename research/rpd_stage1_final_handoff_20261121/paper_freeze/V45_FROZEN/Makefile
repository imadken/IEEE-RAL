PYTHON ?= python3
BUILD ?= ../V45_BUILD
FIGURE_BUILD ?= ../V45_FIGURES
.PHONY: all check figures
all check:
	$(PYTHON) build_paper.py --source . --output $(BUILD)
figures:
	$(PYTHON) figure_source.py --output $(FIGURE_BUILD)
