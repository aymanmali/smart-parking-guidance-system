# ESP32 Signage Controller Firmware (`SPG-CTRL-v1`)

Embedded C firmware (ESP-IDF) for the **Smart Parking Guidance & Management System** directional sign nodes (`SIGN-ENT-01..02`, `SIGN-INT-01..04`).

## Features
- **RS-485 Half-Duplex Binary Protocol** (`rs485_protocol.c`) with CRC-16/MODBUS validation, bit-for-bit compatible with `backend/protocol.py`.
- **Directional LED & Counter Driver HAL** (`display_driver.c`): drives 12V/24V Red/Green/Amber directional arrow MOSFET stages and numeric counters.
- **Safety & Watchdog:** ESP-IDF task watchdog + 15-second backend timeout amber fallback.

## GPIO Pinout (Matches `hardware/kicad/SPG-CTRL-v1`)

| Signal | ESP32 GPIO | Function |
| --- | --- | --- |
| `RS485_TX` | `GPIO17` | UART2 TX -> SN65HVD72 DI |
| `RS485_RX` | `GPIO16` | UART2 RX <- SN65HVD72 RO |
| `RS485_DE_RE` | `GPIO4` | Half-duplex transceiver direction |
| `ARROW_LEFT_G / R` | `GPIO25 / GPIO26` | Left directional arrow MOSFET gates |
| `ARROW_STR_G / R` | `GPIO27 / GPIO14` | Straight directional arrow MOSFET gates |
| `ARROW_RIGHT_G / R` | `GPIO12 / GPIO13` | Right directional arrow MOSFET gates |

## Run Host-Side C Unit Tests
```bash
clang -Wall -Wextra -Werror -std=c99 \
  firmware/main/rs485_protocol.c \
  firmware/main/display_driver.c \
  firmware/tests/test_protocol.c \
  -o /tmp/test_spg_firmware && /tmp/test_spg_firmware
```

## Build & Flash with ESP-IDF
```bash
cd firmware
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```
