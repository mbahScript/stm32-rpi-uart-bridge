# Protocol Specification (High Level)

This project uses UART with framed ASCII messages to communicate between:
- STM32F767 (node/controller)
- Raspberry Pi 5 (host/controller)

## UART Settings
- 115200 baud
- 8 data bits, no parity, 1 stop bit (8N1)

## Framing
- STX = 0x02 (start byte)
- ETX = 0x03 (end byte)

## Message Format
<STX> TYPE|NODE|DATA|CHK <ETX>

Where:
- TYPE: Message type (HB, ARR, DL, CMD, ACK, STATUS, ERR)
- NODE: Sender node identifier (e.g., BUS01 or HOST)
- DATA: Payload string
- CHK: XOR checksum (hex, 2 chars) computed over `TYPE|NODE|DATA`

## Example
<STX>HB|BUS01|OK|3A<ETX>
