# STM32 Firmware

Board: STM32F767ZI Nucleo-144  
UART: USART3 (PB10 TX, PB11 RX)  
Baud: 115200 8N1  

---

## Build

Open in STM32CubeIDE and build.

---

## Flash

Use ST-Link via CubeIDE.

---

## Behavior

- Sends heartbeat every 5s
- Sends arrival every 10s
- Sends delay every 30s
- Validates incoming CMD frames
- Echoes host SEQ on replies