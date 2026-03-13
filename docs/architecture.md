# System Architecture

The project demonstrates a distributed embedded system consisting of a microcontroller node and an edge computing gateway.

---

## Overview


TfL Open Data API
│
│ HTTPS
▼
Raspberry Pi Gateway
(Python Service)
│
│ UART Protocol
▼
STM32F767 Microcontroller
│
▼
Transport Node Simulation


---

## Components

### STM32F767

Firmware responsibilities:

- UART protocol parsing
- command execution
- telemetry generation
- real-time event simulation

Telemetry generated:

| Event | Interval |
|------|------|
| Heartbeat | 5 seconds |
| Arrival update | 10 seconds |
| Delay event | 30 seconds |
| TfL broadcast | 15 seconds |

---

### Raspberry Pi Gateway

Responsibilities:

- UART communication
- TfL API polling
- command transmission
- background service execution

The gateway acts as an **edge computing node** translating internet APIs into embedded-friendly messages.

---

## Communication Layer

Transport medium:


UART
115200 baud
8N1


Protocol layer:


Framed ASCII protocol
Checksum validation
Sequence tracking


---

## Deployment Model

The gateway runs as a Linux system service using **systemd**, enabling:

- automatic startup
- crash recovery
- persistent operation