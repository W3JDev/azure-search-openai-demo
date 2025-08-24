#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT="${SCRIPT_DIR}/.."
cd "$REPO_ROOT"

python -m pip install -r requirements-dev.txt
npm --prefix app/frontend ci
npm --prefix app/frontend run build
python -m playwright install --with-deps
pytest tests/e2e.py
