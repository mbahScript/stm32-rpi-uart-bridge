STX = 0x02
ETX = 0x03
MAX_FRAME_LEN = 256

def checksum_xor(data: bytes) -> int:
    chk = 0
    for b in data:
        chk ^= b
    return chk

def build_frame(msg_type: str, node: str, seq: int, data: str) -> bytes:
    data = data.strip()
    core_str = f"{msg_type}|{node}|{seq}|{data}"
    core = core_str.encode()
    chk = checksum_xor(core)
    payload = f"{core_str}|{chk:02X}".encode()
    return bytes([STX]) + payload + bytes([ETX])

def parse_payload(payload: str):
    """
    Parses: TYPE|NODE|SEQ|DATA|CHK
    """
    last_bar = payload.rfind("|")
    if last_bar == -1:
        return None, "FORMAT"
    chk_hex = payload[last_bar + 1 :]
    core = payload[:last_bar]

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

    return {"type": msg_type, "node": node, "seq": seq, "data": data, "chk": f"{recv:02X}"}, None