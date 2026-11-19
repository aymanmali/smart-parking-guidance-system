# Hardware Design — `SPG-CTRL-v1` Signage Controller PCB

Custom 2-layer KiCad PCB designed to drive physical **Entrance Counter Displays** and **Intersection Directional Guidance Signs** in the 300-slot parking facility.

## Board Specifications
- **Dimensions:** `80 mm × 55 mm`, 2-layer FR-4 (`1.6 mm`, 1 oz copper)
- **Input Power:** `12V – 24V DC` industrial rail (reverse-polarity Schottky `SS34` + `SMBJ28A` surge TVS)
- **Power Tree:** `12–24V DC` → `MP1584EN` (`5V / 3A` buck) → `AMS1117-3.3` (`3.3V / 1A` LDO for ESP32 & RS-485)
- **MCU:** `ESP32-WROOM-32E` (Wi-Fi/MQTT + UART2 RS-485)
- **Wired Bus:** `SN65HVD72DR` half-duplex RS-485 with `SM712-02HTG` ESD protection and `JP1` 120Ω end-of-line termination jumper
- **Outputs:** 6× `AO3400A` low-side N-channel MOSFETs (`30V / 5.7A` each) driving 12V/24V Red/Green/Amber LED directional arrows (`LEFT`, `STRAIGHT`, `RIGHT`)

## Files
- [`kicad/SPG-CTRL-v1.kicad_pro`](kicad/SPG-CTRL-v1.kicad_pro) — KiCad 8 project & net-class design rules
- [`kicad/SPG-CTRL-v1.kicad_sch`](kicad/SPG-CTRL-v1.kicad_sch) — System schematic
- [`kicad/SPG-CTRL-v1.kicad_pcb`](kicad/SPG-CTRL-v1.kicad_pcb) — 2-layer PCB outline, nets, and silkscreen
- [`bom.csv`](bom.csv) — Complete production Bill of Materials (MPNs & footprints)
