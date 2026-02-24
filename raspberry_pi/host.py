import os
import time
import threading
from datetime import datetime

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
    Protocol v2 frame:
      <STX>TYPE|NODE|SEQ|DATA|CHK<ETX>
    CHK = XOR over ASCII bytes of: TYPE|NODE|SEQ|DATA
    """
    data = data.strip()
    core_str = f"{msg_type}|{node}|{seq}|{data}"
    core = core_str.encode()
    chk = checksum_xor(core)
    payload = f"{core_str}|{chk:02X}".encode()
    return bytes([STX]) + payload + bytes([ETX])


def parse_payload(payload: str):
    """
    Protocol v2 payload (no STX/ETX):
      TYPE|NODE|SEQ|DATA|CHK
    DATA may contain '|', so split checksum from end then split core into 4 parts.
    """
    last_bar = payload.rfind("|")
    if last_bar == -1:
        return None, "FORMAT"

    chk_hex = payload[last_bar + 1 :]
    core = payload[:last_bar]  # TYPE|NODE|SEQ|DATA

    try:
        recv = int(chk_hex, 16)
    except ValueError:
        return None, "CHK_FORMAT"

    calc = checksum_xor(core.encode())
    if calc != recv:
        return None, "CHK_MISMATCH"

    parts = core.split("|", 3)
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
        "chk": f"{recv:02X}",
        "raw": payload,
    }, None


class Logger:
    def __init__(self, log_dir="raspberry-pi/logs"):
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(log_dir, f"session_{ts}.log")
        self.lock = threading.Lock()

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"# UART session log started {datetime.now().isoformat(timespec='seconds')}\n")

    def _ts(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def log(self, direction: str, message: str):
        line = f"{self._ts()} {direction} {message}\n"
        with self.lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line)

    def info(self, message: str):
        self.log("INFO", message)


class Mailbox:
    def __init__(self):
        self.lock = threading.Lock()
        self.map = {}  # (type, seq) -> msg dict

    def put(self, msg: dict):
        with self.lock:
            self.map[(msg["type"], msg["seq"])] = msg

    def pop(self, msg_type: str, seq: int):
        with self.lock:
            return self.map.pop((msg_type, seq), None)


def open_serial_with_retry(logger: Logger):
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"[OK] Connected to {PORT} @ {BAUD}")
            logger.info(f"Connected to {PORT} @ {BAUD}")
            return ser
        except SerialException as e:
            print(
                f"[WARN] Cannot open {PORT}: {e}\n"
                f"       Tip: Close anything using UART (screen/minicom/another host).\n"
                f"       Retrying in {RECONNECT_DELAY_S:.0f}s..."
            )
            logger.info(f"Cannot open {PORT}: {e} (retrying)")
            time.sleep(RECONNECT_DELAY_S)


def reader_loop(get_ser_callable, mailbox: Mailbox, logger: Logger):
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
                    logger.log("RX_INVALID", f"{err} :: {payload}")
                else:
                    print(f"[OK] {msg['type']} node={msg['node']} seq={msg['seq']} data={msg['data']} chk={msg['chk']}")
                    logger.log("RX", payload)
                    mailbox.put(msg)

                buf.clear()
                continue

            if in_frame:
                if len(buf) < MAX_FRAME_LEN:
                    buf.append(byte)
                else:
                    in_frame = False
                    buf.clear()
                    print("[INVALID] RX_TOO_LONG (frame dropped)")
                    logger.log("RX_INVALID", "RX_TOO_LONG (frame dropped)")

        except SerialException as e:
            print(f"[WARN] Serial read error: {e}\n       Waiting for reconnect...")
            logger.info(f"Serial read error: {e} (waiting for reconnect)")
            time.sleep(RECONNECT_DELAY_S)
        except Exception as e:
            print(f"[WARN] Reader exception: {e}")
            logger.info(f"Reader exception: {e}")
            time.sleep(0.5)


def main():
    logger = Logger(log_dir="raspberry-pi/logs")
    print(f"[OK] Logging to: {logger.path}")

    ser_holder = {"ser": None}
    ser_lock = threading.Lock()
    mailbox = Mailbox()

    seq_counter = 0

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

    def ensure_connected():
        if get_ser() is None:
            set_ser(open_serial_with_retry(logger))

    def send_cmd_and_wait(expect_types, cmd_data: str):
        nonlocal seq_counter

        seq = seq_counter
        seq_counter = (seq_counter + 1) % 256

        frame = build_frame("CMD", "HOST", seq, cmd_data)

        for attempt in range(1, ACK_RETRIES + 1):
            ensure_connected()
            ser = get_ser()

            try:
                # Log TX payload without STX/ETX for readability
                payload = frame[1:-1].decode(errors="replace")
                logger.log("TX", payload)

                ser.write(frame)
                ser.flush()
            except SerialException as e:
                print(f"[WARN] Serial write error: {e}\n       Reconnecting...")
                logger.info(f"Serial write error: {e} (reconnecting)")
                set_ser(open_serial_with_retry(logger))
                continue

            deadline = time.time() + ACK_TIMEOUT_S
            while time.time() < deadline:
                for t in expect_types + ["ERR"]:
                    msg = mailbox.pop(t, seq)
                    if msg:
                        return True, msg
                time.sleep(0.01)

            warn = f"Timeout waiting for {expect_types} (seq={seq}) attempt {attempt}/{ACK_RETRIES}"
            print(f"[WARN] {warn}")
            logger.info(warn)

        return False, None

    threading.Thread(target=reader_loop, args=(get_ser, mailbox, logger), daemon=True).start()

    print("Host running. Commands:")
    print("  1 = PING")
    print("  2 = STATUS")
    print("  3 = SETROUTE=12A")
    print("  4 = SETETA=7")
    print("  q = quit")

    try:
        set_ser(open_serial_with_retry(logger))

        while True:
            cmd = input("> ").strip().lower()
            if cmd == "q":
                break

            if cmd == "1":
                ok, msg = send_cmd_and_wait(["ACK"], "PING")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))
            elif cmd == "2":
                ok, msg = send_cmd_and_wait(["STATUS"], "STATUS")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))
            elif cmd == "3":
                ok, msg = send_cmd_and_wait(["ACK"], "SETROUTE=12A")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))
            elif cmd == "4":
                ok, msg = send_cmd_and_wait(["ACK"], "SETETA=7")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))
            else:
                print("Unknown option.")

    finally:
        s = get_ser()
        if s:
            try:
                s.close()
            except Exception:
                pass
        logger.info("Host exited")
        print("Exited host.")


if __name__ == "__main__":
    main()