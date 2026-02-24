# Wiring

## STM32F767ZI (USART3)

| STM32 | Function |
|--------|----------|
| PB10 | TX |
| PB11 | RX |
| GND  | GND |

## Raspberry Pi 5

| Pi Pin | Function |
|--------|----------|
| GPIO14 | TXD0 |
| GPIO15 | RXD0 |
| GND    | GND |

---

## Important

- Cross TX ↔ RX
- Use 3.3V logic only
- Ensure `/boot/firmware/config.txt` contains:


dtparam=uart0=on