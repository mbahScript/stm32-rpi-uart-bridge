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
## v0.4.0 – Real TfL Data Integration

# Project Overview

This project implements a custom reliable UART transport protocol between:

- STM32F767 (Bare-Metal, HAL-based)

- Raspberry Pi 5 (Python, Linux-based)

Starting from framed communication and reliability features, the system has now evolved into a real-time embedded transport node that integrates live Transport for London (TfL) Unified API data.

## System Architecture
```md
            ┌────────────────────────────┐
            │        TfL Unified API     │
            └──────────────┬─────────────┘
                           │ HTTPS
                           ▼
            ┌────────────────────────────┐
            │     Raspberry Pi 5         │
            │  - Python transport layer  │
            │  - TfL API integration     │
            │  - Retry logic + logging   │
            └──────────────┬─────────────┘
                           │ UART (115200)
                           ▼
            ┌────────────────────────────┐
            │        STM32F767           │
            │  - Interrupt RX framing    │
            │  - SEQ duplicate handling  │
            │  - Checksum validation     │
            │  - TfL summary storage     │
            └────────────────────────────┘
```

 ## Custom UART Protocol (v2)

### Frame format:
```md
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
```
```md
Field	Description
STX	0x02
ETX	0x03
TYPE	CMD / ACK / STATUS / HB / ARR / DL / ERR
NODE	HOST / BUS01
SEQ	Sequence number (0–255)
DATA	Payload
CHK	XOR over ASCII bytes of `TYPE
```

## Reliability Features
```md
✔ SEQ-based request/response matching
✔ Duplicate detection on STM32
✔ Last reply frame storage + resend
✔ XOR checksum validation
✔ RX overflow protection
✔ Host-side retry logic
```

## v0.4.0 — Real TfL API Integration

This version upgrades the system from mock telemetry to live real-world data.

### Added Features
```md
🔹 TfL Unified API integration
🔹 Compact summary formatting on Pi
🔹 TFL=<summary> command transmission
🔹 On-device storage of latest TfL summary
🔹 GETTFL command for retrieval
```

### Example Flow
- Pi fetches live tube status.

- Pi sends:
```md
CMD|HOST|226|TFL=TUBE: Bakerloo=Good Service; ...|CHK
```
- STM32 stores summary.

- STM32 replies:
```md
ACK|BUS01|226|TFL_RX|CHK
```                       
- Host requests stored data:
```md
CMD|HOST|164|GETTFL|CHK
```
- STM32 responds:
```md
STATUS|BUS01|164|TFL=TUBE: Bakerloo=Good Service; ...|CHK
```

## Repository Structure
```md
stm32-rpi-uart-bridge/
│
├── docs/
│   ├── protocol.md
│   └── release-notes/
│       └── v0.4.0.md
│
├── raspberry-pi/
│   ├── .env.example
│   ├── requirements.txt
│   ├── logs/
│   │   └── .gitkeep
│   └── src/
│       ├── host.py
│       ├── uart_transport.py
│       ├── tfl_client.py
│       ├── tfl_poll.py
│
└── stm32/
    └── Core/Src/main.c
```

### Raspberry Pi Setup
1️. Create virtual environment
```md
python3 -m venv .venv
source .venv/bin/activate
```
2️. Install dependencies
```md
pip install -r raspberry-pi/requirements.txt
```
3️. Configure .env
Create:
```md
raspberry-pi/.env
```
Example:
```md
TFL_APP_KEY=YOUR_TFL_APP_KEY
UART_PORT=/dev/serial0
UART_BAUD=115200
POLL_INTERVAL=30
```
4. Run host
```md
python3 host.py
```

### Command Menu
```
Option	Description
1	PING
2	STATUS
3	SETROUTE
4	SETETA
5	TFL_TUBE (fetch + send)
6	TFL_ARR (StopPoint arrivals)
7	GETTFL (read stored summary)
```

## Security Considerations
- API key loaded via environment variables
- .env excluded from version control
- No plaintext credentials committed
- Checksum validation prevents corrupted frames

## Roadmap
v0.5.0 (Planned)
- systemd auto-start service
- Background TfL polling daemon
- Improved TX (non-blocking interrupt/DMA)
- Display integration (LCD/OLED)
