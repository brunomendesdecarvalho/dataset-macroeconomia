PY ?= .venv/bin/python
export PYTHONPATH := src
export MPLCONFIGDIR := $(CURDIR)/.cache/mpl

.PHONY: fetch build validate dsge empirical reports docs test all clean

fetch:
	$(PY) -m macrodata.sources

build:
	$(PY) -m macrodata.build

validate:
	$(PY) -m macrodata.validation

dsge:
	$(PY) -m macrodata.dsge.estimate
	$(PY) -m macrodata.dsge.medium

empirical:
	$(PY) -m macrodata.empirical

reports:
	$(PY) -m macrodata.report
	$(PY) scripts/cross_country_moments.py
	$(PY) scripts/make_docs.py

docs: reports

test:
	$(PY) -m pytest -q tests

all: fetch build validate dsge reports test

clean:
	rm -rf .cache
	rm -f data/raw/parsed_*.parquet data/processed/*.parquet
