#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export MPLCONFIGDIR="$PWD/.cache/mpl"
PY=${PY:-.venv/bin/python}

echo "[1/6] fetch";      $PY -m macrodata.sources
echo "[2/6] build";      $PY -m macrodata.build
echo "[3/6] validate";   $PY -m macrodata.validation
echo "[4/6] dsge";       $PY -m macrodata.dsge.estimate
                          $PY -m macrodata.dsge.medium
echo "[5/6] reports";    $PY -m macrodata.report
                          $PY scripts/cross_country_moments.py
                          $PY scripts/make_docs.py
echo "[6/6] tests";      $PY -m pytest -q tests
echo "OK"
