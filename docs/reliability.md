# Reliability Design

## Goals

- Prevent corrupted frame processing
- Allow safe retry on packet loss
- Ensure idempotent command handling
- Avoid duplicate execution

---

## Mechanisms Implemented

### 1. Framed Communication
STX/ETX ensures clear packet boundaries.

### 2. XOR Checksum
Lightweight corruption detection.

### 3. Sequence Numbers
Each command contains an 8-bit SEQ.

### 4. Duplicate Detection (STM32)
Stores:
- `last_host_seq`
- `last_reply_frame`

If duplicate SEQ received:
- Resend stored reply
- Skip re-processing

### 5. Host Retry Logic
If no ACK received within timeout:
- Retry up to 3 times

---

## Failure Scenarios Covered

| Scenario | Outcome |
|-----------|----------|
| Corrupted payload | CHK error |
| Duplicate CMD | Resend last reply |
| Frame overflow | RX_OVERFLOW |
| Packet loss | Host retry |

---

## Known Limitations (Prototype Stage)

- TX blocking inside RX interrupt
- No encryption
- No authentication
- No congestion control

---

## Future Improvements (v0.5+)

- DMA-based TX
- Background polling daemon
- Watchdog integration
- Secure message signing