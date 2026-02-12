import time
import threading
import serial
from serial.serialutil import SerialException

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
    
def build_frame(msg_type: str, node: str, data: str) -> bytes:
    """
    Frame format:
      <STX>TYPE|NODE|DATA|CHK<ETX>
    CHK = XOR over bytes of: TYPE|NODE|DATA
    """
    data = data.strip()
    core = f"{msg_type}|{node}|{data}".encode()
    chk = checksum_xor(core)
    payload = f"{msg_type}|{node}|{data}|{chk:02X}".encode()
    return bytes([STX]) + payload + bytes([ETX])


def parse_payload(payload: str):
    """
    Payload format: TYPE|NODE|DATA|CHK
    """
    parts = payload.split("|")
    if len(parts) != 4:
        return None, "FORMAT"

    msg_type, node, data, chk_hex = parts
    try:
        recv = int(chk_hex, 16)
    except ValueError:
        return None, "CHK_FORMAT"

    calc = checksum_xor(f"{msg_type}|{node}|{data}".encode())
    if calc != recv:
        return None, "CHK_MISMATCH"

    return (msg_type, node, data, chk_hex.upper()), None


def open_serial_with_retry():
    """
    Keep trying to open serial until successful.
    """
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"[OK] Connected to {PORT} @ {BAUD}")
            return ser
        except SerialException as e:
            print(
                f"[WARN] Cannot open {PORT}: {e}\n"
                f"       Tip: Close anything using UART (parser.py, screen, minicom, another host.py).\n"
                f"       Retrying in {RECONNECT_DELAY_S:.0f}s..."
            )
            time.sleep(RECONNECT_DELAY_S)


def reader_loop(get_ser_callable):
    """
    Background thread: continuously reads frames from UART and prints validated messages.
    If port errors occur, it waits until main reconnects.
    """
    buf = bytearray()
    in_frame = False

    while True:
        ser = get_ser_callable()
        if ser is None:
            time.sleep(0.2)
            continue

        try:
            b = ser.read(1)
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
                    print(f"[INVALID] {err} :: {payload}")
                else:
                    t, node, data, chk = msg
                    print(f"[OK] {t} node={node} data={data} chk={chk}")

                buf.clear()
                continue

            if in_frame:
                if len(buf) < MAX_FRAME_LEN:
                    buf.append(byte)
                else:
                    in_frame = False
                    buf.clear()
                    print("[INVALID] RX_TOO_LONG (frame dropped)")

        except SerialException as e:
            print(
                f"[WARN] Serial read error: {e}\n"
                f"       Waiting for reconnect..."
            )
            time.sleep(RECONNECT_DELAY_S)
        except Exception as e:
            # Keep reader alive even if something unexpected occurs
            print(f"[WARN] Reader exception: {e}")
            time.sleep(0.5)
            
def main():
    # Shared serial object, replaced on reconnect
    ser_holder = {"ser": None}
    ser_lock = threading.Lock()

    def get_ser():
        with ser_lock:
            return ser_holder["ser"]

    def set_ser(new_ser):
        with ser_lock:
            old = ser_holder["ser"]
            ser_holder["ser"] = new_ser
        if old:
            try:
                old.close()
            except Exception:
                pass

    # Start background reader
    threading.Thread(target=reader_loop, args=(get_ser,), daemon=True).start()

    print("Host running. Commands:")
    print("  1 = PING")
    print("  2 = STATUS")
    print("  3 = SETROUTE=12A")
    print("  4 = SETETA=7")
    print("  q = quit")

    try:
        # Initial connect
        set_ser(open_serial_with_retry())

        while True:
            cmd = input("> ").strip().lower()

            if cmd == "q":
                break

            # Ensure we have a live serial connection
            ser = get_ser()
            if ser is None:
                print("[WARN] Serial not connected. Reconnecting...")
                set_ser(open_serial_with_retry())
                ser = get_ser()

            try:
                if cmd == "1":
                    ser.write(build_frame("CMD", "HOST", "PING"))
                    ser.flush()
                elif cmd == "2":
                    ser.write(build_frame("CMD", "HOST", "STATUS"))
                    ser.flush()
                elif cmd == "3":
                    ser.write(build_frame("CMD", "HOST", "SETROUTE=12A"))
                    ser.flush()
                elif cmd == "4":
                    ser.write(build_frame("CMD", "HOST", "SETETA=7"))
                    ser.flush()
                else:
                    print("Unknown option.")
                    continue

            except SerialException as e:
                print(f"[WARN] Serial write error: {e}\n       Reconnecting...")
                set_ser(open_serial_with_retry())

    finally:
        # Cleanup
        s = get_ser()
        if s:
            try:
                s.close()
            except Exception:
                pass
        print("Exited host.")


if __name__ == "__main__":
    main()
