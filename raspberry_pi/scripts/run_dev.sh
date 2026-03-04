#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."

python3 -m venv .venv || true
source .venv/bin/activate
pip install -r requirements.txt
python3 host.py