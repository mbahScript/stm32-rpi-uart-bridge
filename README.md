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

##  Overview

This project implements a **structured, bidirectional UART transport protocol** between:

- **STM32F767 (Nucleo-144)** – Real-time embedded node
- **Raspberry Pi 5** – Host controller

It goes beyond basic UART by implementing:

-  STX/ETX framed packets  
-  XOR checksum validation  
-  Typed messages (HB / ARR / DL / CMD / ACK / STATUS / ERR)  
-  Bidirectional command-response handling  
-  Interactive host controller with auto-reconnect  

This repository serves as the **communication foundation** for a future smart transport (TfL-style) simulation system.

---

##  Why This Project Matters

In real embedded systems, UART communication must handle:

- Framing & partial data
- Corruption detection
- Message typing
- State updates
- Host–node coordination
- Fault tolerance

This project demonstrates those principles using real hardware.

---

##  Protocol Format

All packets follow:

```md
<STX>TYPE|NODE|DATA|CHK<ETX>
```


Where:

- **STX** = `0x02`
- **ETX** = `0x03`
- **CHK** = XOR of ASCII bytes of `TYPE|NODE|DATA`

### Example


```md
<STX>HB|BUS01|OK|4B<ETX>
<STX>CMD|HOST|PING|5A<ETX>
<STX>ACK|BUS01|PONG|1A<ETX>
```


---

##  Telemetry (STM32 → Pi)

| Type | Description |
|------|-------------|
| HB   | Heartbeat   |
| ARR  | Arrival update |
| DL   | Delay event |

---

##  Commands (Pi → STM32)

| Command | Response |
|---------|----------|
| PING | ACK PONG |
| STATUS | STATUS (node info) |
| SETROUTE=12A | ACK ROUTE_SET |
| SETETA=7 | ACK ETA_SET |

---

##  Hardware Setup

### Boards
- STM32 Nucleo-144 (STM32F767)
- Raspberry Pi 5

### Wiring (USART3)

| STM32 | Function | Raspberry Pi |
|--------|----------|--------------|
| PB10 | TX | GPIO15 (RX) |
| PB11 | RX | GPIO14 (TX) |
| GND  | GND | GND |

UART Configuration:
- 115200 baud
- 8 data bits
- No parity
- 1 stop bit

---

##  Running the Host (Raspberry Pi)

```bash
cd raspberry_pi
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 host.py
```

```c
Interactive commands:
1 → PING
2 → STATUS
3 → SETROUTE=12A
4 → SETETA=7
q → quit
```

## Repository Structure
```md
stm32-rpi-uart-bridge/
├── docs/
├── protocol/
├── raspberry_pi/
└── stm32_firmware/
```


## Current Release
```
v0.2.0 – Structured UART Transport Protocol
Includes:
Framing
Checksum validation
Telemetry engine
Command-response handling
Interactive host with auto-reconnect
```


## Roadmap

**Planned improvements:**
ACK retry + timeout handling
Sequence numbers (duplicate prevention)
Logging + replayable tests
Transport simulation engine
Display integration (large touchscreen)
