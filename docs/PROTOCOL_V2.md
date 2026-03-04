# UART Transport Protocol Specification (v2)

## Overview

This project implements a custom framed UART protocol between:

- Raspberry Pi (HOST)
- STM32F767 (NODE: BUS01)

The protocol is designed for:
- Reliability
- Duplicate detection
- Corruption detection
- Deterministic parsing on microcontrollers

---

## Frame Format


<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>


| Field | Description |
|--------|------------|
| STX | 0x02 |
| ETX | 0x03 |
| TYPE | CMD / ACK / STATUS / HB / ARR / DL / ERR |
| NODE | HOST / BUS01 |
| SEQ | 0–255 (8-bit sequence counter) |
| DATA | Command or payload |
| CHK | XOR over ASCII bytes of `TYPE|NODE|SEQ|DATA` |

---

## Checksum

Checksum is computed as:


CHK = XOR of all ASCII bytes in:
TYPE|NODE|SEQ|DATA


Example:


CMD|HOST|12|PING


All characters including separators (`|`) are included.

---

## Message Types

### CMD
Sent from HOST to STM32.

Examples:
- `PING`
- `STATUS`
- `SETROUTE=12A`
- `SETETA=7`
- `TFL=<summary>`
- `GETTFL`

---

### ACK
Acknowledgement from STM32.

Example:

ACK|BUS01|12|PONG


---

### STATUS
Structured response from STM32.

Example:

STATUS|BUS01|164|TFL=TUBE: Bakerloo=Good Service


---

### HB (Heartbeat)
Periodic 5s status broadcast.

---

### ARR (Arrival Update)
Periodic route + ETA broadcast.

---

### DL (Delay)
Periodic delay simulation event.

---

## Duplicate Handling

If STM32 receives a `CMD` with the same SEQ as the last processed command:

- It re-sends the last reply frame.
- It does NOT re-execute the command.

This ensures idempotent retry handling.

---

## Error Handling

If:
- Checksum mismatch → `ERR|BUS01|SEQ|CHK`
- Format invalid → `ERR|BUS01|SEQ|FORMAT`
- RX overflow → `ERR|BUS01|AUTO_SEQ|RX_OVERFLOW`

---

## Version History

| Version | Change |
|----------|--------|
| v0.1 | Basic framing |
| v0.2 | SEQ support |
| v0.3 | Duplicate detection + resend |
| v0.4 | TfL integration + GETTFL |