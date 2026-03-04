# Raspberry Pi Host
This script:

- Sends commands
- Validates checksum
- Implements retry logic
- Prints telemetry frames

---

## Install
```py
python3 -m pip install -r requirements.txt
```

---

## Run
```
python3 host.py
```

## Logs
Each run creates a new session log:
```md
`raspberry-pi/logs/session_YYYYMMDD_HHMMSS.log`
```