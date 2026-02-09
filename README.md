# STM32 ↔ Raspberry Pi UART Bridge
![Embedded Systems](https://img.shields.io/badge/Embedded%20Systems-00599C?style=for-the-badge)
![STM32](https://img.shields.io/badge/STM32-03234B?style=for-the-badge&logo=stmicroelectronics)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-C51A4A?style=for-the-badge&logo=raspberrypi)
![UART](https://img.shields.io/badge/UART-000000?style=for-the-badge)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Microcontrollers](https://img.shields.io/badge/Microcontrollers-4CAF50?style=for-the-badge)
![Bare Metal](https://img.shields.io/badge/Bare--Metal-FF6F00?style=for-the-badge)
![Version](https://img.shields.io/badge/version-v0.1.0-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/status-active-success?style=for-the-badge)


This project implements a **bidirectional UART communication bridge** between an **STM32F767 (Nucleo-144)** microcontroller and a **Raspberry Pi 5** running Linux.

The goal is to build a **reliable, well-documented communication layer** that can be reused as a foundation for larger embedded systems involving:
- Microcontrollers (real-time control)
- Linux-based systems (data processing, UI, networking)

Rather than relying on USB or high-level abstractions, this project focuses on **bare-metal UART communication**, protocol framing, and system-level reliability.

---

## Hardware
- STM32F767ZI (Nucleo-144)
- Raspberry Pi 5
- UART (USART3 on STM32)
- 115200 baud, 8N1

---

## Features
- Interrupt-driven UART on STM32
- Framed command protocol
- Bidirectional messaging
- Linux-side UART handling on Raspberry Pi 5
- Reproducible setup and documentation

---

## Status
✅ STM32 → Pi transmission  
✅ Pi → STM32 commands  
✅ Framed protocol (STX/ETX)  
🚧 Error handling & CRC (planned)

---

## Why this project?
Modern embedded systems often combine:
- Low-level deterministic controllers
- High-level Linux systems

This repository demonstrates how to connect both worlds **cleanly and correctly**.

---

## Why I Built This

Many modern embedded systems combine:
- Real-time microcontrollers for deterministic control
- Linux-based systems for computation, networking, and user interfaces

However, reliable communication between these two layers is often treated as an afterthought or hidden behind high-level abstractions.

I built this project to:
- Understand UART communication at both the **bare-metal** and **Linux driver** levels
- Resolve real-world issues such as UART conflicts, serial console occupation, and device permissions on modern Raspberry Pi hardware
- Design a simple but structured communication protocol that can be extended for larger systems
- Create a reusable, well-documented bridge suitable for production-style embedded architectures

This project now serves as the communication backbone for future work involving embedded displays, transport-style information systems, and distributed embedded control.

