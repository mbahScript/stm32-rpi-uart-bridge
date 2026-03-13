import os
import time
import threading
from datetime import datetime

import serial
from serial.serialutil import SerialException
from dotenv import load_dotenv

from uart_transport import build_frame, parse_payload, STX, ETX, MAX_FRAME_LEN
from tfl_client import get_tube_status, get_stoppoint_arrivals
from tfl_poll import summarize_tube_status, summarize_arrivals

load_dotenv()

PORT = os.getenv("UART_PORT", "/dev/serial0")
BAUD = int(os.getenv("UART_BAUD", "115200"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
STOPPOINT_ID = os.getenv("TFL_STOPPOINT_ID", "").strip()

RECONNECT_DELAY_S = 2.0
ACK_TIMEOUT_S = 0.5
ACK_RETRIES = 3

class Mailbox:
    def __init__(self):
        self.lock = threading.Lock()
        self.map = {}  # (type, seq) -> msg

    def put(self, msg: dict):
        with self.lock:
            self.map[(msg["type"], msg["seq"])] = msg

    def pop(self, msg_type: str, seq: int):
        with self.lock:
            return self.map.pop((msg_type, seq), None)

def open_serial_with_retry():
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            print(f"[OK] Connected to {PORT} @ {BAUD}")
            return ser
        except SerialException as e:
            print(f"[WARN] Cannot open {PORT}: {e} (retrying in {RECONNECT_DELAY_S}s)")
            time.sleep(RECONNECT_DELAY_S)

def reader_loop(get_ser, mailbox: Mailbox):
    buf = bytearray()
    in_frame = False

    while True:
        ser = get_ser()
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
                    print(f"[OK] {msg['type']} node={msg['node']} seq={msg['seq']} data={msg['data']} chk={msg['chk']}")
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

        except SerialException as e:
            print(f"[WARN] Serial read error: {e}")
            time.sleep(RECONNECT_DELAY_S)

def main():
    ser_holder = {"ser": None}
    ser_lock = threading.Lock()
    mailbox = Mailbox()
#    seq_counter = 0
    seq_counter = int(time.time()) % 256

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
            set_ser(open_serial_with_retry())

    def send_cmd_and_wait(expect_types, cmd_data: str):
        nonlocal seq_counter
        seq = seq_counter
        seq_counter = (seq_counter + 1) % 256

        frame = build_frame("CMD", "HOST", seq, cmd_data)

        for attempt in range(1, ACK_RETRIES + 1):
            ensure_connected()
            ser = get_ser()

            try:
                ser.write(frame)
                ser.flush()
            except SerialException:
                set_ser(open_serial_with_retry())
                continue

            deadline = time.time() + ACK_TIMEOUT_S
            while time.time() < deadline:
                for t in expect_types + ["ERR"]:
                    msg = mailbox.pop(t, seq)
                    if msg:
                        return True, msg
                time.sleep(0.01)

            print(f"[WARN] Timeout waiting for {expect_types} seq={seq} attempt {attempt}/{ACK_RETRIES}")

        return False, None

    # Start UART reader
    threading.Thread(target=reader_loop, args=(get_ser, mailbox), daemon=True).start()

    print("Host running. Commands:")
    print("  1 = PING")
    print("  2 = STATUS")
    print("  3 = SETROUTE=12A")
    print("  4 = SETETA=7")
    print("  5 = TFL_TUBE (fetch live tube status -> send to STM32)")
    print("  6 = TFL_ARR (fetch StopPoint arrivals -> send to STM32) [requires TFL_STOPPOINT_ID]")
    print("7 = GETTFL (read stored TfL summary from STM32)")
    print("  q = quit")

    try:
        set_ser(open_serial_with_retry())

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

                # Real TfL call -> compress -> send as command to STM32 (you can rename this later)
            elif cmd == "5":
                print("\n========== [TFL] TUBE STATUS ==========")
                lines = get_tube_status()
                summary = summarize_tube_status(lines, top_n=4)

                print(f"[TFL] summary -> {summary}")
                ok, msg = send_cmd_and_wait(["ACK"], f"TFL={summary}")

                print("========== [RESULT] ==========")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))
                print("=======================================\n")

            elif cmd == "6":
                if not STOPPOINT_ID:
                    print("[WARN] Set TFL_STOPPOINT_ID in .env first.")
                    continue
                arr = get_stoppoint_arrivals(STOPPOINT_ID)
                summary = summarize_arrivals(arr, top_n=3)
                ok, msg = send_cmd_and_wait(["ACK"], f"TFL={summary}")
                print("[RESULT] " + (f"OK {msg['data']}" if ok else "FAILED"))

            elif cmd == "7":
                ok, msg = send_cmd_and_wait(["STATUS"], "GETTFL")
                print("[RESULT] " + (f"{msg['data']}" if ok else "FAILED"))

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
