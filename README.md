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

STM32 ↔ Raspberry Pi UART Bridge for Live TfL Data










Overview

This project demonstrates a hybrid embedded system architecture where a Raspberry Pi retrieves real-time public transport data from the Transport for London (TfL) Unified API, processes it, and transmits summarized updates to an STM32F767 microcontroller over a custom UART protocol.

The STM32 firmware receives, verifies, and stores the data for future use (e.g., display integration).

The project highlights:

embedded communication design

reliable UART transport protocol

integration between Linux SBC and microcontroller firmware

real-time API data ingestion

service-oriented background operation on Raspberry Pi

System Architecture
              Internet
                 │
                 │
        Transport for London API
                 │
                 ▼
         Raspberry Pi 5
    (Python background service)
                 │
                 │ UART (115200)
                 ▼
            STM32F767 MCU
      (protocol parsing + storage)
                 │
                 ▼
       Future output devices
       (LCD / OLED / signage)
Responsibilities

Raspberry Pi

Fetch real-time TfL data

Summarize transport status

Send updates to STM32

Run as a background service

STM32

Receive UART frames

Validate checksums

Store TfL summaries

Respond to host commands

Protocol Design

The communication protocol is a lightweight framed UART transport.

Frame Format
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>

Where:

Field	Description
STX	Start of frame (0x02)
TYPE	Message type
NODE	Sender node identifier
SEQ	Sequence number
DATA	Payload data
CHK	XOR checksum
ETX	End of frame (0x03)
Example Frame
<STX>CMD|HOST|42|TFL=Bakerloo=Good Service|5F<ETX>
Message Types
Type	Meaning
CMD	Command from host
ACK	Acknowledgement
STATUS	System status
HB	Heartbeat
ARR	Arrival update
DL	Delay event
ERR	Error response
Supported Commands
Command	Description
PING	Connectivity test
STATUS	Retrieve system status
SETROUTE=<id>	Set simulated route
SETETA=<min>	Set arrival ETA
TFL=<summary>	Send TfL summary
GETTFL	Retrieve stored TfL summary
Repository Structure
stm32-rpi-uart-bridge
│
├── README.md
├── LICENSE
├── .gitignore
│
├── docs
│   ├── architecture.md
│   ├── protocol.md
│   └── release-notes
│
├── raspberry-pi
│   ├── host.py
│   ├── service.py
│   ├── uart_transport.py
│   ├── tfl_client.py
│   ├── tfl_poll.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── logs
│   │   └── .gitkeep
│   │
│   ├── scripts
│   │   ├── run_dev.sh
│   │   └── install_service.sh
│   │
│   └── systemd
│       └── tfl-uart-bridge.service
│
└── stm32
    └── firmware
        └── main.c
Raspberry Pi Setup
Install dependencies
sudo apt update
sudo apt install python3 python3-venv

Create environment

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
Environment Configuration

Create .env

cp .env.example .env

Example:

TFL_APP_KEY=YOUR_TFL_APP_KEY
UART_PORT=/dev/serial0
UART_BAUD=115200
POLL_INTERVAL=30
Running the System
Manual development mode
python3 host.py

Interactive commands:

1 = PING
2 = STATUS
3 = SETROUTE
4 = SETETA
5 = TFL_TUBE
6 = TFL_ARR
7 = GETTFL
Background Service Mode (v0.5.0)

The Raspberry Pi can run as a continuous background service.

Start manually:

python3 service.py

The service will:

fetch TfL data every 30 seconds

summarize results

send TFL= update to STM32

retry on UART failures

systemd Auto-Start

Install service:

bash scripts/install_service.sh

Check service:

sudo systemctl status tfl-uart-bridge.service

View logs:

journalctl -u tfl-uart-bridge.service -f
STM32 Firmware

The STM32 firmware implements:

UART RX interrupt state machine

framed protocol parsing

XOR checksum verification

duplicate command detection

reply retransmission

Key features:

interrupt-driven UART reception

safe RX buffer handling

host command handling

persistent TfL summary storage

Example telemetry messages:

HB|BUS01|81|OK
ARR|BUS01|83|ROUTE=25B,STOP=STOP12,ETA=3
DL|BUS01|87|+5MIN
Example Runtime Output
[OK] Connected to /dev/serial0 @ 115200
[TX] CMD HOST seq=42 TFL=Bakerloo=Good Service
[RX] ACK node=BUS01 seq=42 data=TFL_RX

STM32 telemetry:

[OK] HB node=BUS01 seq=84 data=OK
[OK] ARR node=BUS01 seq=86 data=ROUTE=25B
Security Notes

The following files are excluded from the repository:

.env
logs/*.log
.venv

Instead use:

.env.example
Version Roadmap
v0.4.0

Real TfL API integration

GETTFL command

structured protocol

v0.5.0

Raspberry Pi background service

continuous TfL polling

automatic UART updates

systemd auto-start

Planned
v0.6.0

non-blocking STM32 UART TX

DMA/interrupt transmission

improved buffering

v0.7.0

LCD / OLED display integration

embedded passenger information display

Skills Demonstrated

Embedded systems engineering

STM32 firmware development

UART transport protocol design

interrupt-driven communication

host-microcontroller integration

Software engineering

Python service architecture

REST API integration

Linux service management

Systems integration

SBC ↔ MCU communication

real-time data processing

fault tolerant background services

License

MIT License