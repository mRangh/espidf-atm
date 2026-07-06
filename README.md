# Electronic Safe — ESP32 ATM Controller

A coin-operated ATM / electronic safe system: an **ESP32** (FreeRTOS, ESP-IDF) drives the physical hardware — a coin dispenser and a coin counter — while a **Python desktop app** (Tkinter) handles user accounts and talks to the board over UART.

## Overview

The project is split into two cooperating parts:

- **Firmware (C++ / ESP-IDF)** — runs on the ESP32. Drives a servo motor to dispense coins, uses an LM393-based sensor to count deposited coins, and exposes a simple line-based command protocol over UART.
- **Host application (Python / Tkinter)** — a dark-themed desktop GUI (window title "ATM Sys", home screen "Electronic Safe") that manages user accounts/balances in a local SQLite database and drives the ESP32 by sending `DEPOSIT` / `WITHDRAW` commands, updating balances once the hardware confirms the operation.

```
Python GUI (Tkinter) + SQLite DB
        │
        │  UART → "DEPOSIT <n>" / "WITHDRAW <n>"
        ▼
ESP32 Firmware (FreeRTOS / ESP-IDF)
  UART RX task → ATM state machine → Servo (withdraw) / LM393 sensor (deposit)
        │
        │  UART ← "DONE DEPOSIT <n>" / "DONE WITHDRAW <n>"
        ▼
GUI updates the SQLite balance and shows the result
```

## Features

- **Dual-core FreeRTOS firmware** — the UART receiver and the ATM state machine run as separate tasks pinned to different cores, synchronized through `std::atomic` flags.
- **Simple serial protocol** — plain-text, newline-terminated commands (`DEPOSIT <n>`, `WITHDRAW <n>`) and replies (`DONE DEPOSIT <n>`, `DONE WITHDRAW <n>`).
- **Physical coin handling** — a servo tilts to release coins one at a time on withdrawal; an LM393 sensor counts coins on deposit, guarded by a 20-second timeout.
- **Custom Tkinter GUI** — dark theme, rounded buttons, login/registration, deposit/withdraw flows, and balance inquiry.
- **Non-blocking serial polling** — the GUI polls the serial port every 100 ms via Tkinter's `.after()`, without freezing the UI, and can reconnect automatically if the ESP32 drops out.
- **SQLite-backed accounts** — per-user balances plus an aggregate bank balance and user count.
- **Virtual-port friendly** — tolerates serial ports that don't support DTR/RTS toggling, useful when developing without the physical board attached.

## Project structure

**Firmware — ESP32 / C++ (ESP-IDF + FreeRTOS)**

| File | Purpose |
|---|---|
| `main.cpp` | Entry point: wires up the servo, coin sensor, and `ATM` instance; starts the UART and ATM tasks |
| `atm_ctrl.hpp` | `ATM` class — the deposit/withdraw state machine |
| `uart_handler.hpp` | UART setup, command parsing, and the RX task |
| `esp32_hal.hpp`\* | Hardware abstraction layer providing the `Servo` and `LM393` classes used above |

\* Included via `<esp32_hal.hpp>` (angle brackets), suggesting it lives in a separate ESP-IDF component rather than alongside `main.cpp`. Not included in this document.

**Host application — Python**

| File | Purpose |
|---|---|
| `app.py` | Tkinter GUI — application entry point |
| `uart_client.py` | Thin `pyserial` wrapper for talking to the ESP32 |
| `data_base.py` | SQLite persistence layer for accounts and bank totals |

## Hardware

| Component | Connection | Role |
|---|---|---|
| Servo motor | GPIO 4 | Dispenses coins on withdrawal |
| LM393 sensor module | GPIO 13 | Detects/counts coins on deposit |
| UART0 | Default TX/RX pins (typically shared with the USB-serial console) | Link to the host PC — 115200 baud, 8N1 |

## Requirements

**Firmware**
- [ESP-IDF](https://docs.espressif.com/projects/esp-idf/) (developed with v6.0.1)
- An ESP32 development board

**Host application**
- Python 3
- [`pyserial`](https://pypi.org/project/pyserial/)
- `tkinter` (bundled with most Python installers; on Debian/Ubuntu: `sudo apt install python3-tk`)

## Getting started

### 1. Build and flash the firmware

```bash
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### 2. Run the host application

```bash
pip install pyserial
python app.py
```

The GUI connects on `/dev/ttyUSB0` by default. If your ESP32 enumerates elsewhere (e.g. `COM3` on Windows), update the port passed to `UartClient` in `app.py`.

## How it works

1. The GUI opens on the home screen ("Electronic Safe") with three actions — Deposit, Withdraw, Check Balance — plus a link to register a new user.
2. Choosing an action (or registering) prompts for a **username and password**, checked against — or written to — the local SQLite database.
3. **Check Balance** goes straight to a screen showing the user's balance and the bank's total funds.
4. **Deposit** / **Withdraw** instead ask for an **amount** (withdrawals are pre-validated against both the user's balance and the bank's total funds), then send `DEPOSIT <n>` / `WITHDRAW <n>` to the ESP32 and show a "Processing" screen.
5. The firmware's state machine either counts `n` coins via the LM393 sensor (deposit) or dispenses `n` coins one at a time via the servo (withdrawal), then replies `DONE DEPOSIT <n>` / `DONE WITHDRAW <n>`.
6. The GUI's serial-polling loop picks up the reply, updates the balance in SQLite, and shows a completion screen before returning to the main menu.

## Communication protocol

Plain ASCII, newline-terminated, 115200 baud / 8N1 / no flow control.

| Direction | Message | Meaning |
|---|---|---|
| Host → ESP32 | `DEPOSIT <n>` | Start a deposit; count up to `n` coins (0–255) |
| Host → ESP32 | `WITHDRAW <n>` | Dispense `n` coins (0–255) |
| ESP32 → Host | `DONE DEPOSIT <n>` | Deposit finished; `n` coins counted |
| ESP32 → Host | `DONE WITHDRAW <n>` | Withdrawal finished; `n` coins dispensed |

Any other message received by the firmware is silently ignored.

## Database schema

**`bank_accounts`**

| Column | Type | Notes |
|---|---|---|
| `u_name` | TEXT (PK) | Username |
| `password` | TEXT | Stored in plain text — see [Notes](#notes--current-limitations) |
| `money` | INTEGER | User balance (new accounts start with 3) |

**`bank_data`**

| Column | Type | Notes |
|---|---|---|
| `bank_hash` | TEXT (PK) | Fixed bank identifier (`"A1234"`) |
| `total_money` | INTEGER | Aggregate funds across all accounts |
| `total_users` | INTEGER | Registered user count |

## Notes & current limitations

- `init_db()` re-seeds the `bank_data` row on every run, so `total_money` / `total_users` reset to their defaults (10 / 0) each time the app starts — only individual `bank_accounts` rows persist across runs.
- Passwords are stored in plain text, which is fine for a prototype but not for production use.
- The schema supports a single bank identity (`"A1234"`).

## Roadmap

- Card-based user identification via an MFRC522 (RC522) RFID reader — the `ATM` class already reserves a `user_id` field for this.

## License

Apache License 2.0, as noted in the source file headers.

## Author

**Marco Antônio Ranghetti**
- GitHub: [@mRangh](https://github.com/mRangh)
- Email: marcoantonioranghetti@gmail.com