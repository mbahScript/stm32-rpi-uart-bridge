import serial
import time

STX = 0x02
ETX = 0x03


def checksum_xor(data: bytes) -> int:
    """XOR checksum over bytes."""
    chk = 0
    for b in data:
        chk ^= b
    return chk


def build_frame(msg_type: str, node: str, data: str) -> bytes:
    """
    Build frame:
      <STX>TYPE|NODE|DATA|CHK<ETX>

    CHK is XOR over ASCII bytes of: TYPE|NODE|DATA
    """
    # Important: clean the DATA field so we don't accidentally include whitespace/newlines
    data = data.strip()

    core = f"{msg_type}|{node}|{data}".encode("utf-8")
    chk = checksum_xor(core)

    payload = f"{msg_type}|{node}|{data}|{chk:02X}".encode("utf-8")
    return bytes([STX]) + payload + bytes([ETX])


def send_and_read(ser: serial.Serial, frame: bytes, wait_s: float = 0.15) -> bytes:
    """
    Send a frame and attempt to read a reply frame ending with ETX.
    (STM32 replies may arrive quickly, so we do a short wait.)
    """
    ser.write(frame)
    ser.flush()
    time.sleep(wait_s)

    # Try to read one reply frame (up to 256 bytes)
    resp = ser.read_until(bytes([ETX]), 256)
    return resp


def main():
    ser = serial.Serial("/dev/serial0", 115200, timeout=1)

    commands = [
        ("CMD", "HOST", "PING"),
        ("CMD", "HOST", "STATUS"),
        ("CMD", "HOST", "SETROUTE=12A"),
        ("CMD", "HOST", "SETETA=7"),
        ("CMD", "HOST", "STATUS"),
    ]

    print("Sending commands...\n")

    for msg_type, node, data in commands:
        frame = build_frame(msg_type, node, data)
        print("Sent:", frame)

        # Optional: read back STM32 response immediately
        reply = send_and_read(ser, frame)
        if reply:
            print("Reply:", reply)
        else:
            print("Reply: (none)")

        print("-" * 40)

    ser.close()


if __name__ == "__main__":
    main()
