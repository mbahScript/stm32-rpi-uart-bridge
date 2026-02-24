# STM32 ↔ Raspberry Pi 5 UART Transport Protocol

![Release](https://img.shields.io/github/v/release/mbahScript/stm32-rpi-uart-bridge?style=for-the-badge)
![License](https://img.shields.io/github/license/mbahScript/stm32-rpi-uart-bridge?style=for-the-badge)
![Last Commit](https://img.shields.io/github/last-commit/mbahScript/stm32-rpi-uart-bridge?style=for-the-badge)
![Repo Size](https://img.shields.io/github/repo-size/mbahScript/stm32-rpi-uart-bridge?style=for-the-badge)

![STM32](https://img.shields.io/badge/MCU-STM32F767-03234B?style=for-the-badge&logo=stmicroelectronics)
![Raspberry Pi](https://img.shields.io/badge/SBC-Raspberry%20Pi%205-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)
![Firmware](https://img.shields.io/badge/Firmware-C-00599C?style=for-the-badge&logo=c&logoColor=white)
![Host](https://img.shields.io/badge/Host-Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Protocol](https://img.shields.io/badge/Protocol-UART-000000?style=for-the-badge)

---

## Overview

A lightweight, checksum-validated UART transport protocol between an **STM32F767 (Nucleo-144)** and a **Raspberry Pi 5**.

This repo implements a simple framed protocol over UART with:
- **STX/ETX framing**
- **XOR checksum**
- **SEQ-based request/response matching**
- **host-side retries**
- **telemetry streaming (HB/ARR/DL)**

> Current release: **v0.3.1**

---

## What this project solves

When you connect an MCU to a Linux host over UART, you quickly run into reliability issues:
- framing & partial reads
- checksum validation
- duplicate packets from retries
- matching replies to requests
- logging and debugging

This project provides a clean baseline transport layer you can reuse for larger systems (e.g., IoT dashboards, public display systems, bus/tube-style information boards).

---

## Protocol (v2)

Frame format:
```
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
```

- `STX` = `0x02`
- `ETX` = `0x03`
- `CHK` = XOR checksum over ASCII bytes of: `TYPE|NODE|SEQ|DATA`
- `SEQ` (0–255) is used to match responses to commands

### Example
```
CMD|HOST|7|PING|5A
ACK|BUS01|7|PONG|56
```

---

## Features

### Raspberry Pi (Host)
- Interactive CLI: `PING`, `STATUS`, `SETROUTE`, `SETETA`
- **Retry logic**: up to **3 retries** per command
- **Per-session logging**: RX/TX/INVALID frames saved to `raspberry-pi/logs/`

### STM32 (Node)
- UART RX interrupt parsing (byte-by-byte)
- Telemetry streaming:
  - `HB` (Heartbeat)
  - `ARR` (Arrival/status update)
  - `DL` (Delay event)
- **Duplicate SEQ handling** (v0.3.1): host retry with same SEQ → **re-sends last reply**

---

## Hardware

- **STM32F767ZI Nucleo-144**
- **Raspberry Pi 5**
- UART wiring (crossed):
  - STM32 **TX (PB10 / USART3_TX)** → Pi **RX (GPIO15 / RXD0)**
  - STM32 **RX (PB11 / USART3_RX)** → Pi **TX (GPIO14 / TXD0)**
  - **GND ↔ GND** (required)

> Ensure voltage levels are compatible (Pi uses 3.3V UART logic).

---

## Raspberry Pi Setup

From `raspberry-pi/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 host.py
```
### Output 
![System Result](docs/output.png)

If you see “device busy”, close other programs using /dev/serial0 (screen/minicom/another script).

### Logs (v0.3.1)

Each run creates a new session log:
```
raspberry-pi/logs/session_YYYYMMDD_HHMMSS.log
```
Entries include:
```
TX ...
RX ...
RX_INVALID ...
INFO ...
```

## Repository Layout:
```
docs/                # protocol notes, wiring, troubleshooting, changelog
raspberry-pi/         # host CLI + logging
stm32/                # STM32CubeIDE project / firmware code
```

## Roadmap
- v0.4.x: multi-node addressing + message routing
- v0.5.x: API integration (TFL-style live data) + UI renderer on Pi
- v1.0.0: production-style bridge service (systemd) + dashboard integration


