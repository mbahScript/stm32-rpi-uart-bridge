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

## 🚀 STM32 ↔ Raspberry Pi UART Transport Protocol v0.3.0

This release introduces a structured and reliable transport layer over UART between:

<<<<<<< HEAD
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


##  Commands (Pi → STM32)

| Command | Response |
|---------|----------|
| PING | ACK PONG |
| STATUS | STATUS (node info) |
| SETROUTE=12A | ACK ROUTE_SET |
| SETETA=7 | ACK ETA_SET |


## Architecture Diagram
![System Diagram](docs/architecture_diagram.png)

---

##  Hardware Setup

### Boards
- STM32 Nucleo-144 (STM32F767)
=======
- STM32F767ZI (Nucleo-144)
>>>>>>> efa4d4a (v0.3.0 - Protocol v2 (SEQ + retries) with structured transport layer)
- Raspberry Pi 5

---

## ✨ What’s New

### 🔢 Sequence Numbers (SEQ)
- Every frame now includes a sequence number.
- Enables deterministic command-response matching.

### 🔁 Host Retry Mechanism
- Raspberry Pi host retries up to 3 times if no matching response is received.
- Ensures reliable command execution.

### 🛡 Duplicate Protection
- STM32 ignores duplicate commands based on SEQ.
- Prevents repeated command execution.

### 📡 Telemetry Streaming
STM32 periodically sends:
- `HB` – Heartbeat
- `ARR` – Arrival updates
- `DL` – Delay events

---

<<<<<<< HEAD
##  Running the Host (Raspberry Pi)
*NB: [host.py] is paser.py and send_command.py combined.*
=======

## 📦 Protocol Version

**v2 Format**

```
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
```

Where:
```
- `STX = 0x02`
- `ETX = 0x03`
- `CHK = XOR checksum over ASCII bytes of TYPE|NODE|SEQ|DATA`
```
---

## 🧠 Example Frame
```
\x02ACK|BUS01|0|PONG|56\x03
```

---

## 📁 Project Structure
```
stm32-rpi-uart-bridge/
├── docs/
├── raspberry-pi/
└── stm32/
```
---

## 🔌 Hardware

- STM32F767ZI Nucleo-144
- Raspberry Pi 5 (`/dev/serial0`)
- USART3 (PB10 TX, PB11 RX)
- 115200 8N1

---

##  Running the Host (Raspberry Pi)
>>>>>>> efa4d4a (v0.3.0 - Protocol v2 (SEQ + retries) with structured transport layer)
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

<<<<<<< HEAD
![System Result](docs/bash.png)

## Repository Structure
```md
stm32-rpi-uart-bridge/
├── docs/
├── protocol/
├── raspberry_pi/
└── stm32_firmware/
```
=======
![System Result](docs/output.png)
>>>>>>> efa4d4a (v0.3.0 - Protocol v2 (SEQ + retries) with structured transport layer)

---

## 🏷️ Current Version (Status)

**v0.3.0 – Structured Transport Layer**

- SEQ implemented
- Host retries (3 attempts)
- Telemetry streaming
- Command echo replies

<<<<<<< HEAD
**Planned improvements:**
ACK retry + timeout handling
Sequence numbers (duplicate prevention)
Logging + replayable tests
Transport simulation engine
Display integration (large touchscreen)
=======
This version establishes a reliable, versioned transport layer and forms the foundation for:

- Backend service integration
- 16" Touchscreen dashboard UI
- Embedded LCD status module
- Deployment-ready system architecture

---

## 🛣️ Roadmap

See `ROADMAP.md`

Next milestone: `v0.3.1 – Reliability polish + logging`
>>>>>>> efa4d4a (v0.3.0 - Protocol v2 (SEQ + retries) with structured transport layer)
