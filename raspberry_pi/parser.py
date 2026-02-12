import time
import serial
from serial.serialutil import SerialException
from logger import log_line

STX = 0x02
ETX = 0x03

PORT = "/dev/serial0"
BAUD = 115200

RECONNECT_DELAY_S = 2.0
MAX_FRAME_LEN = 256


def checksum_xor(data: bytes) -> int:
    chk = 0
    for b in data:
        chk ^= b
    return chk


def parse_payload(payload: str):
    """
    Payload format: TYPE|NODE|DATA|CHK
    CHK is XOR over bytes of: TYPE|NODE|DATA
    """
    parts = payload.split("|")
    if len(parts) != 4:
        return None, "FORMAT"

    msg_type, node, data, chk_hex = parts

    try:
        recv_chk = int(chk_hex, 16)
    except ValueError:
        return None, "CHK_FORMAT"

    core = f"{msg_type}|{node}|{data}".encode()
    calc_chk = checksum_xor(core)

    if calc_chk != recv_chk:
        return None, "CHK_MISMATCH"

    return {
        "type": msg_type,
        "node": node,
        "data": data,
        "chk": chk_hex.upper(),
    }, None


def open_serial_with_retry():
    """
    Keeps trying to open the serial port until successful.
    """
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            msg = f"Connected to {PORT} @ {BAUD}"
            print(msg)
            log_line(msg)
            return ser
        except SerialException as e:
            # Port busy, disconnected, permission issues, etc.
            msg = (
                f"[WARN] Cannot open {PORT}: {e}\n"
                f"       Tip: Make sure ONLY ONE program is using the UART.\n"
                f"       Close host.py/minicom/screen/other parser instances, then retrying in {RECONNECT_DELAY_S:.0f}s..."
            )
            print(msg)
            log_line(f"SERIAL_OPEN_FAIL: {e}")
            time.sleep(RECONNECT_DELAY_S)
            

def main():
    print(f"Starting parser on {PORT} @ {BAUD}")
    log_line("START parser")

    while True:
        ser = open_serial_with_retry()

        buf = bytearray()
        in_frame = False

        try:
            print("Listening... (Ctrl+C to stop)")
            while True:
                try:
                    b = ser.read(1)

                    # Some serial drivers raise SerialException mid-read if port is taken/disconnected
                    # We handle that below in except SerialException.
                    if not b:
                        continue

                    byte = b[0]

                    if byte == STX:
                        buf.clear()
                        in_frame = True
                        continue

                    if byte == ETX and in_frame:
                        in_frame = False
                        payload = buf.decode(errors="replace")

                        msg, err = parse_payload(payload)
                        if err:
                            out = f"[INVALID] {err} :: {payload}"
                            print(out)
                            log_line(out)
                        else:
                            out = f"[OK] {msg['type']} node={msg['node']} data={msg['data']} chk={msg['chk']}"
                            print(out)
                            log_line(out)

                        buf.clear()
                        continue

                    if in_frame:
                        if len(buf) < MAX_FRAME_LEN:
                            buf.append(byte)
                        else:
                            # Frame too long: reset safely
                            in_frame = False
                            buf.clear()
                            out = "[INVALID] RX_TOO_LONG (frame dropped)"
                            print(out)
                            log_line(out)

                except SerialException as e:
                    # Port lost, multiple access, device disconnected, etc.
                    out = f"[WARN] Serial read error: {e}\n       Reconnecting in {RECONNECT_DELAY_S:.0f}s..."
                    print(out)
                    log_line(f"SERIAL_READ_FAIL: {e}")
                    break  # break inner loop -> close port -> reconnect

        except KeyboardInterrupt:
            print("\nStopped.")
            log_line("STOP parser")
            try:
                ser.close()
            except Exception:
                pass
            return

        # If we reach here, we had a serial error and want to reconnect
        try:
            ser.close()
        except Exception:
            pass
        time.sleep(RECONNECT_DELAY_S)


if __name__ == "__main__":
    main()
