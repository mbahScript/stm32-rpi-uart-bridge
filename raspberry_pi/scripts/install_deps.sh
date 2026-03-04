#!/usr/bin/env bash
set -e

SERVICE_SRC="raspberry-pi/systemd/tfl-uart-bridge.service"
SERVICE_DST="/etc/systemd/system/tfl-uart-bridge.service"

echo "[OK] Installing systemd service..."
sudo cp "$SERVICE_SRC" "$SERVICE_DST"

sudo systemctl daemon-reload
sudo systemctl enable tfl-uart-bridge.service
sudo systemctl restart tfl-uart-bridge.service

echo "[OK] Service installed & running."
echo "Check logs: sudo journalctl -u tfl-uart-bridge -f"