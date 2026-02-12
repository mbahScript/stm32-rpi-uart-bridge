# Transport Protocol v1 (Detailed)

## Checksum
XOR checksum over ASCII bytes of:
TYPE|NODE|DATA

Example:
payload = "HB|BUS01|OK"
chk = XOR(payload bytes)
frame = STX + payload + "|" + chk_hex + ETX

## Errors
- FORMAT: missing fields
- CHK: checksum mismatch
- RX_OVERFLOW: STM32 receive buffer overflow
- UNKNOWN_CMD / UNKNOWN_TYPE
