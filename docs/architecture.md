# System Architecture

## Overview

The system integrates:

- STM32F767 (Bare-metal, HAL)
- Raspberry Pi 5 (Python, Linux)
- Transport for London Unified API

---

## High-Level Architecture


TfL API (HTTPS)
↓
Raspberry Pi 5

API Client

Summary Formatter

UART Transport Layer
↓ UART (115200)
STM32F767

Interrupt RX

Framed Parser

SEQ handling

Data storage


---

## Layered Design

### 1. External Data Layer
- `tfl_client.py`
- HTTPS requests
- JSON parsing

### 2. Application Formatting Layer
- `tfl_poll.py`
- Converts raw JSON into compact summaries
- Truncates to fit embedded constraints

### 3. Transport Layer
- `uart_transport.py`
- Frame building
- Checksum
- Parsing
- STX/ETX framing

### 4. Embedded Command Layer
- `main.c`
- UART interrupt parsing
- Duplicate detection
- State storage

---

## Data Flow (TFL)

1. Pi fetches tube status
2. Formats into compact string
3. Sends `CMD|HOST|SEQ|TFL=...`
4. STM32 stores summary
5. STM32 replies `ACK TFL_RX`
6. Pi may request `GETTFL`
7. STM32 returns stored summary

---

## Design Principles

- Deterministic parsing
- Minimal dynamic allocation
- Predictable memory usage
- Framed communication
- Stateless retry logic

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