# Troubleshooting

## ModuleNotFoundError: serial

Install pyserial:
```py
python3 -m pip install pyserial
```

---

## Device busy

Check:
```
lsof /dev/serial0
```
Stop conflicting processes.

---

## INVALID FORMAT errors
Ensure `host.py` matches protocol v2 (SEQ included).

---

## No output

- Check wiring
- Confirm 115200 8N1
- Confirm STM32 clock configured
