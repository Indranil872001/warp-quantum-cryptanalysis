#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
python tests/verify_phase6.py
python tests/verify_depth_optimized.py
python tests/verify_sparse_support.py
python experiments/run_phase6.py
python experiments/resource_models_v2.py
