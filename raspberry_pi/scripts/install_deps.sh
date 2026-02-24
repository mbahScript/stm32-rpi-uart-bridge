#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r raspberry-pi/requirements.txt

echo "Done."

# Make executable:
# chmod +x raspberry-pi/scripts/install_deps.sh