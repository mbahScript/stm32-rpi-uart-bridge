# UART Transport Protocol v2

## Frame Structure
```
<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
```

### Fields

| Field | Description |
|--------|-------------|
| TYPE | HB, ARR, DL, ACK, STATUS, CMD, ERR |
| NODE | Node identifier (e.g., BUS01) |
| SEQ | 0-255 sequence number |
| DATA | Payload |
| CHK | XOR checksum |

---

## Checksum
```
CHK = XOR(TYPE|NODE|SEQ|DATA)
```

Example:
```
ACK|BUS01|0|PONG
```
```
XOR of ASCII bytes → 0x56
```
---

## Message Types

- HB — Heartbeat
- ARR — Arrival update
- DL — Delay event
- CMD — Host command
- ACK — Command acknowledgement
- STATUS — System state
- ERR — Error
