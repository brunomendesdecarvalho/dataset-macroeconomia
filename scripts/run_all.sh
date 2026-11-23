#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
export MPLCONFIGDIR="$PWD/.cache/mpl"
PY=${PY:-.venv/bin/python}

echo "[1/7] fetch";      $PY -m macrodata.sources
echo "[2/7] build";      $PY -m macrodata.build
echo "[3/7] validate";   $PY -m macrodata.validation
echo "[4/7] empirical";  $PY -m macrodata.empirical
echo "[5/7] export";     $PY -m macrodata.export
echo "[6/7] reports";    $PY -m macrodata.report
                          $PY scripts/cross_country_moments.py
                          $PY scripts/make_docs.py
echo "[7/7] tests";      $PY -m pytest -q tests
echo "OK"
