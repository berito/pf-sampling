#!/usr/bin/env bash
# Runs once when the container is created: fetches upstream code and datasets, builds gmapping,
# and reports what is available. Each step skips work that is already done.
set -u
cd "$(dirname "$0")/.."

echo "=== python ==="
python -c "import numpy,scipy,matplotlib,pandas;print('numpy',numpy.__version__,'| scipy',scipy.__version__,'| matplotlib',matplotlib.__version__,'| pandas',pandas.__version__)"

echo
echo "=== upstream code (vendor/) ==="
python tools/fetch_vendors.py || echo "some vendor repos need attention (see above)"

echo
echo "=== datasets (datasets/) ==="
python tools/fetch_datasets.py || echo "some datasets need attention (see above)"

echo
echo "=== gmapping (C++) ==="
bash tools/build_gmapping.sh || echo "gmapping build failed; see .build/gmapping_make.log"

echo
echo "Ready. See README.md."
