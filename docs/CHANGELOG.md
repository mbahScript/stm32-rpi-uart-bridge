# Changelog

All notable changes to this project will be documented in this file.

This project follows Semantic Versioning:

MAJOR.MINOR.PATCH  
- MAJOR → incompatible protocol changes  
- MINOR → new features, backward compatible  
- PATCH → fixes and stability improvements  

---

## [v0.3.1]

### Added
- Duplicate HOST `SEQ` detection with reply re-send support.
- Persistent storage of last reply frame on STM32.
- Per-session structured logging on Raspberry Pi.
- `raspberry-pi/logs/` directory for UART session logs.
- Logging categories: `TX`, `RX`, `RX_INVALID`, `INFO`.

### Improved
- Host retry reliability (3 retry attempts with timeout).
- Deterministic request/response matching using `SEQ`.
- Protocol validation and checksum error reporting.
- Internal firmware structure clarity and documentation comments.

### Technical Details
- Protocol v2 frame format:

<STX>TYPE|NODE|SEQ|DATA|CHK<ETX>

- Checksum: XOR over ASCII bytes of:

TYPE|NODE|SEQ|DATA

- Duplicate HOST sequence numbers now trigger re-transmission of the last stored reply.

---

## [v0.3.0]

### Added
- Protocol upgraded to v2 with `SEQ` field.
- Host-side ACK matching logic.
- Retry logic (3 attempts).
- Telemetry frames:
- `HB` (Heartbeat)
- `ARR` (Arrival update)
- `DL` (Delay event)

### Changed
- Frame structure updated from:

TYPE|NODE|DATA|CHK

to:

TYPE|NODE|SEQ|DATA|CHK


---

## [v0.2.0]

### Added
- STX/ETX framing.
- XOR checksum validation.
- Command parsing (`PING`, `STATUS`, `SETROUTE`, `SETETA`).
- Interrupt-driven UART RX handling.

### Fixed
- Format validation errors.
- Basic overflow handling in RX buffer.

---

## [v0.1.0]

### Initial Release
- Basic UART communication between STM32F767 and Raspberry Pi.
- Simple command-response structure.
- No checksum.
- No sequence tracking.