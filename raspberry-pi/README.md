# Raspberry Pi UART Control

This folder contains the Raspberry Pi side of the UART bridge.

## Platform
- Raspberry Pi 5
- Linux
- UART via `/dev/serial0`

## Notes
- Serial console must be disabled
- UART conflicts resolved via config
- Permissions handled via `dialout` group

## Script
- `uart_control.py`: Sends framed commands and prints responses

## Example
```bash
python3 uart_control.py
```

## UART Protocol Specification

## Framing
```md
- STX: 0x02
- ETX: 0x03
```

## UART Message Framing:
```md
+------+-----+------+-----+------+
| STX  | '|' | CMD  | '|' | DATA | ... | ETX |
|0x02  |     | PING |     |      |     |0x03 |
+------+-----+------+-----+------+
```

## Legend:
```md
- STX (0x02) : Start of Text – marks the beginning of a message
- '|'         : Separator – makes the message readable
- CMD         : Command being sent (e.g., PING, STATUS)
- DATA        : Optional data or parameters
- ETX (0x03)  : End of Text – marks the end of the message
```

## Format
```md
<STX>|CMD|DATA|<ETX>
```

## Commands
| Command | Description |
|------|-------------|
| PING | Health check |
| STATUS | System status |

## Responses
| Response | Meaning |
|--------|--------|
| PONG | Device alive |
| STATUS|OK | System healthy |

This protocol is intentionally simple, readable, and extensible.
