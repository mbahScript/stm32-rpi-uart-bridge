import os
import time
from datetime import datetime

import serial
from serial.serialutil import SerialException
from dotenv import load_dotenv

from uart_transport import build_frame, parse_payload, STX, ETX, MAX_FRAME_LEN
from tfl_client import get_tube_status
from tfl_poll import summarize_tube_status

load_dotenv()

PORT = os.getenv("UART_PORT", "/dev/serial0")
BAUD = int(os.getenv("UART_BAUD", "115200"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))

RECONNECT_DELAY_S = 2.0
ACK_TIMEOUT_S = 1.0
ACK_RETRIES = 3
NODE_ID = "HOST"


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def open_serial_with_retry():
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=1)
            log(f"[OK] Connected to {PORT} @ {BAUD}")
            return ser
        except SerialException as e:
            log(f"[WARN] Cannot open {PORT}: {e}")
            time.sleep(RECONNECT_DELAY_S)


def wait_for_reply(ser, expected_seq: int, expected_types=("ACK", "ERR", "STATUS")):
    buf = bytearray()
    in_frame = False
    deadline = time.time() + ACK_TIMEOUT_S

    while time.time() < deadline:
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
                log(f"[INVALID] {err} :: {payload}")
                buf.clear()
                continue

            log(f"[RX] {msg['type']} node={msg['node']} seq={msg['seq']} data={msg['data']} chk={msg['chk']}")

            if msg["seq"] == expected_seq and msg["type"] in expected_types:
                return True, msg

            buf.clear()
            continue

        if in_frame:
            if len(buf) < MAX_FRAME_LEN:
                buf.append(byte)
            else:
                in_frame = False
                buf.clear()
                log("[WARN] RX_TOO_LONG dropped")

    return False, None


def send_cmd_and_wait(ser, seq: int, cmd_data: str):
    frame = build_frame("CMD", NODE_ID, seq, cmd_data)

    for attempt in range(1, ACK_RETRIES + 1):
        try:
            ser.write(frame)
            ser.flush()
            log(f"[TX] seq={seq} cmd={cmd_data}")
        except SerialException as e:
            log(f"[WARN] UART write failed: {e}")
            raise

        ok, msg = wait_for_reply(ser, seq)
        if ok:
            return True, msg

        log(f"[WARN] Timeout waiting for reply (seq={seq}) attempt {attempt}/{ACK_RETRIES}")

    return False, None


def main():
    log("TfL UART background service starting...")
    ser = open_serial_with_retry()
    seq_counter = int(time.time()) % 256

    while True:
        try:
            lines = get_tube_status()
            summary = summarize_tube_status(lines, top_n=4)

            # Keep payload compact for STM32 RX safety
            summary = summary[:96]

            cmd = f"TFL={summary}"
            ok, msg = send_cmd_and_wait(ser, seq_counter, cmd)

            if ok:
                log(f"[OK] STM32 reply: {msg['type']} {msg['data']}")
            else:
                log("[WARN] No ACK received from STM32")

            seq_counter = (seq_counter + 1) % 256
            time.sleep(POLL_INTERVAL)

        except SerialException:
            log("[WARN] Serial disconnected, reconnecting...")
            try:
                ser.close()
            except Exception:
                pass
            time.sleep(RECONNECT_DELAY_S)
            ser = open_serial_with_retry()

        except Exception as e:
            log(f"[WARN] Service loop error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()