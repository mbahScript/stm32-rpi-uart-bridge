# Reliability Design

This project includes several mechanisms to ensure reliable communication between the Raspberry Pi gateway and the STM32 microcontroller.

---

## Packet Integrity

Each packet includes an XOR checksum.

The receiver verifies the checksum before processing the message.

If validation fails:


ERR|CHK


is returned.

---

## Sequence Numbers

Each frame includes a sequence counter:


TYPE|NODE|SEQ|DATA


This allows:

- duplicate detection
- message ordering
- retry handling

---

## Duplicate Protection

If the host retransmits a command with the same sequence number, the STM32 firmware resends the previously stored reply.

This prevents repeated command execution.

---

## Framing

The protocol uses explicit start and end markers:


STX = 0x02
ETX = 0x03


This ensures reliable message extraction even when:

- bytes are dropped
- messages arrive back-to-back

---

## Background Gateway Service

The Raspberry Pi gateway runs as a **systemd service**, enabling:

- automatic restart on failure
- system logging
- boot-time startup

Service management:


sudo systemctl start tfl-uart-bridge
sudo systemctl stop tfl-uart-bridge
sudo systemctl status tfl-uart-bridge


Logs can be monitored using:


journalctl -u tfl-uart-bridge -f


---

## Embedded Design Principles

The protocol and firmware are designed to support:

- low memory usage
- deterministic behaviour
- simple parsing logic
- minimal computational overhead