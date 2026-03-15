# UART Transport Protocol

This project implements a lightweight framed UART protocol for reliable communication between an STM32F767 microcontroller and a Raspberry Pi gateway.

The protocol ensures message integrity, sequencing, and compatibility with resource-constrained embedded systems.

---

## Frame Structure

Each message is transmitted using the following format:

```
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
```

| Field | Description |
|------|-------------|
| STX | Start of frame (0x02) |
| TYPE | Message type |
| NODE | Device identifier |
| SEQ | Sequence number |
| DATA | Payload content |
| CHK | XOR checksum |
| ETX | End of frame (0x03) |

---

## Checksum

Checksum is calculated as:


XOR of ASCII bytes of "`TYPE|NODE|SEQ|DATA`"


Example payload:

```
HB|BUS01|12|OK
```

Checksum result:

```
CHK = XOR(all bytes)
```

---

## Message Types

| Type | Description |
|------|-------------|
| CMD | Host command |
| ACK | Acknowledgement |
| STATUS | Status response |
| ERR | Error response |
| HB | Heartbeat |
| ARR | Arrival update |
| DL | Delay event |
| TFL | TfL transport summary |

---

## Example Frame

```
<STX>HB|BUS01|12|OK|05<ETX>
```

---

## Reliability Mechanisms

The protocol implements:

- Sequence numbers for ordering
- XOR checksum validation
- Duplicate detection
- Command retry support
