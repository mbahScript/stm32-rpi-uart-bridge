import serial
import time

ser = serial.Serial(
    port='/dev/serial0',
    baudrate=115200,
    timeout=1
)

def send(cmd):
    packet = b'\x02|' + cmd.encode() + b'|\x03'
    ser.write(packet)
    time.sleep(0.1)
    resp = ser.read(64)
    if resp:
        print("RX:", resp)

while True:
    send("PING")
    time.sleep(2)
    send("STATUS")
    time.sleep(2)
