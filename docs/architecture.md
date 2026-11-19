# System Architecture & Protocol Specification

## 1. Facility Topology (300 Slots)

| Entity | Count | Details |
| --- | --- | --- |
| Parking Slots | 300 | `A-001`..`A-075`, `B-001`..`B-075`, `C-001`..`C-075`, `D-001`..`D-075` |
| Zones | 4 | `ZONE-A` (NW), `ZONE-B` (NE), `ZONE-C` (SW), `ZONE-D` (SE) — 75 slots each |
| Edge Cameras | 12 | `CAM-01`..`CAM-12` — 3 cameras/zone, 25 slots/camera (1280×720 @ 15 FPS) |
| Facility Entrances | 2 | `ENT-NORTH` (North Main), `ENT-SOUTH` (South Main) |
| Internal Intersections | 4 | `INT-1`..`INT-4` — 3 directional branches each (`left`, `straight`, `right`) |

---

## 2. Computer Vision Pipeline

1. **Frame Acquisition:** RTSP stream (`cv2.VideoCapture`) or synthetic frame generator in simulator mode.
2. **Vehicle Detection (YOLO / PyTorch):** Runs YOLOv8 inference filtering COCO vehicle classes (`car=2`, `motorcycle=3`, `bus=5`, `truck=7`).
3. **ROI Polygon Matching (OpenCV):** Computes polygon intersection / bounding-box overlap ratio between detected vehicle boxes and each slot's calibrated polygon in `config/rois.json`.
4. **ROI Crop Classification (PyTorch CNN):** For ambiguous/borderline overlap ratios (`0.15 <= overlap < 0.45`), crops the slot ROI and runs a lightweight PyTorch binary CNN classifier (`occupied` vs `free`).
5. **Temporal Hysteresis:** Requires `N` consecutive matching observations (default `N=3`) before flipping a slot's committed state, preventing false transitions from aisle traffic.

---

## 3. Hardware Wire Protocols

### 3.1 MQTT Topics (Wi-Fi Mode)
- Entrance displays: `parking/displays/entrance/{entrance_id}`
- Intersection displays: `parking/displays/intersection/{intersection_id}`
- Node telemetry/heartbeat: `parking/nodes/{node_id}/health`

Example Intersection Payload:
```json
{
  "display_id": "INT-1",
  "timestamp": "2026-11-19T13:30:00Z",
  "branches": {
    "left": {"label": "Zone A (NW)", "available": 42, "status": "OPEN"},
    "straight": {"label": "South Zones (C & D)", "available": 88, "status": "OPEN"},
    "right": {"label": "Zone B (NE)", "available": 0, "status": "FULL"}
  }
}
```

### 3.2 RS-485 Binary Frame (Wired Daisy-Chain Mode)
Used by the `SPG-CTRL-v1` ESP32 board over half-duplex RS-485 (115200 8N1):

| Byte(s) | Field | Description |
| --- | --- | --- |
| `0..1` | `SOF` | Start of Frame `0xAA 0x55` |
| `2` | `ADDR` | Node RS-485 address (`1..247`, `0xFF` broadcast) |
| `3` | `CMD` | `0x01` Entrance Update, `0x02` Intersection Update, `0x03` Heartbeat Ping |
| `4` | `LEN` | Payload length in bytes (`0..64`) |
| `5..5+LEN-1` | `PAYLOAD` | Packed big-endian counts + status bitmask |
| `last 2` | `CRC16` | CRC-16/MODBUS over `ADDR..PAYLOAD` (little-endian) |

**Intersection Update Payload (`CMD=0x02`, 7 bytes):**
- `left_count` (`uint16_t` BE)
- `straight_count` (`uint16_t` BE)
- `right_count` (`uint16_t` BE)
- `flags` (`uint8_t`): bit 0 = left open, bit 1 = straight open, bit 2 = right open, bit 7 = emergency/override
