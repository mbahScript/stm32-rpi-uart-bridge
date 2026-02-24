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

ACK_TIMEOUT_S = 0.5
ACK_RETRIES = 3


def checksum_xor(data: bytes) -> int:
    chk = 0
    for b in data:
        chk ^= b
    return chk


def build_frame(msg_type: str, node: str, seq: int, data: str) -> bytes:
    """
    v2 payload: TYPE|NODE|SEQ|DATA|CHK
    CHK = XOR over ASCII bytes of "TYPE|NODE|SEQ|DATA"
    """
    core_str = f"{msg_type}|{node}|{seq}|{data}"
    core = core_str.encode()
    chk = checksum_xor(core)
    payload = f"{core_str}|{chk:02X}".encode()
    return bytes([STX]) + payload + bytes([ETX])


def parse_payload_v2(payload: str):
    """
    payload string (no STX/ETX): TYPE|NODE|SEQ|DATA|CHK
    DATA may contain '|' so we split checksum from end, then parse first 3 fields.
    """
    last_bar = payload.rfind("|")
    if last_bar == -1:
        return None, "FORMAT"

    chk_str = payload[last_bar + 1 :]
    core = payload[:last_bar]  # TYPE|NODE|SEQ|DATA

    # Parse checksum
    try:
        recv_chk = int(chk_str, 16)
    except ValueError:
        return None, "CHK_FORMAT"

    calc_chk = checksum_xor(core.encode())
    if calc_chk != recv_chk:
        return None, "CHK"

    # Now parse core fields
    parts = core.split("|", 3)  # maxsplit=3 => TYPE, NODE, SEQ, DATA(rest)
    if len(parts) != 4:
        return None, "FORMAT"

    msg_type, node, seq_str, data = parts

    try:
        seq = int(seq_str)
    except ValueError:
        return None, "SEQ_FORMAT"

    return {
        "type": msg_type,
        "node": node,
        "seq": seq,
        "data": data,
        "chk": f"{recv_chk:02X}",
    }, None


def open_serial_with_retry():
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"[OK] Connected to {PORT} @ {BAUD}")
            return ser
        except SerialException as e:
            print(
                f"[WARN] Cannot open {PORT}: {e}\n"
                f"       Close other UART apps and retrying in {RECONNECT_DELAY_S:.0f}s..."
            )
            time.sleep(RECONNECT_DELAY_S)


class RxBus:
    """
    Thread-safe mailbox for received messages by (type, seq).
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.by_type_seq = {}  # (type, seq) -> msg dict

    def put(self, msg: dict):
        with self.lock:
            self.by_type_seq[(msg["type"], msg["seq"])] = msg

    def pop(self, msg_type: str, seq: int):
        with self.lock:
            return self.by_type_seq.pop((msg_type, seq), None)


def reader_loop(get_ser_callable, mailbox: RxBus):
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

                msg, err = parse_payload_v2(payload)
                if err:
                    print(f"[INVALID] {err} :: {payload}")
                else:
                    # Print nicely
                    print(f"[OK] {msg['type']} node={msg['node']} seq={msg['seq']} data={msg['data']} chk={msg['chk']}")
                    # Store for ACK-wait logic
                    mailbox.put(msg)

                buf.clear()
                continue

            if in_frame:
                if len(buf) < MAX_FRAME_LEN:
                    buf.append(byte)
                else:
                    in_frame = False
                    buf.clear()
                    print("[INVALID] RX_TOO_LONG (dropped)")

        except SerialException as e:
            print(f"[WARN] Serial read error: {e}\n       Waiting for reconnect...")
            time.sleep(RECONNECT_DELAY_S)
        except Exception as e:
            print(f"[WARN] Reader exception: {e}")
            time.sleep(0.5)


def main():
    ser_holder = {"ser": None}
    ser_lock = threading.Lock()

    mailbox = RxBus()

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

    # Start reader thread
    threading.Thread(target=reader_loop, args=(get_ser, mailbox), daemon=True).start()

    # Connect
    set_ser(open_serial_with_retry())

    seq_counter = 0

    def send_cmd_and_wait(expect_types, data: str):
        """
        Send CMD|HOST|SEQ|<data>|CHK and wait for a reply type in expect_types with same SEQ.
        Retries up to ACK_RETRIES.
        """
        nonlocal seq_counter

        seq = seq_counter
        seq_counter = (seq_counter + 1) % 256

        frame = build_frame("CMD", "HOST", seq, data)

        for attempt in range(1, ACK_RETRIES + 1):
            ser = get_ser()
            if ser is None:
                print("[WARN] Serial not connected. Reconnecting...")
                set_ser(open_serial_with_retry())
                ser = get_ser()

            try:
                ser.write(frame)
                ser.flush()
            except SerialException as e:
                print(f"[WARN] Write failed: {e} -> reconnecting")
                set_ser(open_serial_with_retry())
                continue

            # Wait for matching response
            deadline = time.time() + ACK_TIMEOUT_S
            while time.time() < deadline:
                for t in expect_types:
                    msg = mailbox.pop(t, seq)
                    if msg:
                        return True, msg
                time.sleep(0.01)

            print(f"[WARN] Timeout waiting for {expect_types} (seq={seq}) attempt {attempt}/{ACK_RETRIES}")

        return False, None

    print("Host running. Commands:")
    print("  1 = PING")
    print("  2 = STATUS")
    print("  3 = SETROUTE=12A")
    print("  4 = SETETA=7")
    print("  q = quit")

    try:
        while True:
            cmd = input("> ").strip().lower()
            if cmd == "q":
                break

            if cmd == "1":
                ok, msg = send_cmd_and_wait(["ACK", "ERR"], "PING")
                print("[RESULT] " + ("OK " + msg["data"] if ok else "FAILED"))
            elif cmd == "2":
                ok, msg = send_cmd_and_wait(["STATUS", "ERR"], "STATUS")
                print("[RESULT] " + ("OK " + msg["data"] if ok else "FAILED"))
            elif cmd == "3":
                ok, msg = send_cmd_and_wait(["ACK", "ERR"], "SETROUTE=12A")
                print("[RESULT] " + ("OK " + msg["data"] if ok else "FAILED"))
            elif cmd == "4":
                ok, msg = send_cmd_and_wait(["ACK", "ERR"], "SETETA=7")
                print("[RESULT] " + ("OK " + msg["data"] if ok else "FAILED"))
            else:
                print("Unknown option.")

    finally:
        s = get_ser()
        if s:
            try:
                s.close()
            except Exception:
                pass
        print("Exited host.")


if __name__ == "__main__":
    main()