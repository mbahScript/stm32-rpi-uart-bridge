#!/usr/bin/env bash
set -e

SERVICE_NAME="tfl-uart-bridge.service"
SERVICE_SRC="$(dirname "$0")/../systemd/$SERVICE_NAME"
SERVICE_DST="/etc/systemd/system/$SERVICE_NAME"

echo "[INFO] Installing systemd service..."
sudo cp "$SERVICE_SRC" "$SERVICE_DST"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "[OK] Service installed."
echo "Check status with:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "View logs with:"
echo "  journalctl -u $SERVICE_NAME -f"