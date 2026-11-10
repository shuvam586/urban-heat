#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <city>" >&2
    exit 1
fi

CITY="$1"
cd "$(dirname "$0")"

python 00_smoke_test.py --city "$CITY"

python 01_grid_attrs.py --city "$CITY"
python tests/check_01_grid.py --city "$CITY"

python 02_landsat.py --city "$CITY"
python tests/check_02_landsat.py --city "$CITY"

python 03_panel.py --city "$CITY"
python tests/check_03_panel.py --city "$CITY"

python 04_gradient.py --city "$CITY"
python tests/check_04_gradient.py --city "$CITY"

python 05_gam.py --city "$CITY"
python tests/check_05_gam.py --city "$CITY"

python 06_summary.py --city "$CITY"
python tests/check_06_summary.py --city "$CITY"

echo "run_city.sh: $CITY complete"