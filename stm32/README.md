# STM32 Firmware

This folder contains the STM32 firmware for UART communication with a Raspberry Pi.

## MCU
- STM32F767ZI (Nucleo-144)

## UART Configuration
- Peripheral: USART3
- TX: PB10
- RX: PB11
- Baud rate: 115200
- Mode: Interrupt-driven RX

## Responsibilities
- UART framing & parsing
- Command handling (PING, STATUS)
- Deterministic real-time behavior

## Build
- STM32CubeIDE
- HAL drivers

The firmware continuously listens for framed commands and responds accordingly.
