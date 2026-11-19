# Production Case Study — Galleria40 Mall (LEED Certified), Egypt (2019)

> **Location:** Galleria40, Sheikh Zayed City, Greater Cairo, Egypt  
> **Building Certification:** LEED Certified Commercial, Retail & Office Complex  
> **Deployment Year:** 2019  
> **System Scope:** 300-slot automated computer-vision parking guidance, entrance counter displays, internal intersection directional signs, custom Embedded C firmware & PCB controller hardware.

---

## 1. Operational Challenge

Commercial and mixed-use destinations like **Galleria40** experience sharp arrival peaks across retail, dining, and corporate office hours. Without real-time stall visibility:
- Drivers spend several minutes circling aisles searching for open spaces ("cruising"), creating bottlenecks at entrances and internal junctions.
- Excess low-speed idling increases **indoor CO / NOx buildup**, pushing parking ventilation systems to run harder—working directly against the energy and indoor environmental quality goals of a **LEED-certified** building.
- Conventional per-slot ultrasonic sensor installations require heavy overhead conduit runs and maintenance across hundreds of stalls, whereas multi-camera computer vision covers 20–30 stalls per edge camera.

---

## 2. System Architecture Deployed

1. **Multi-Camera Computer Vision Layer (`Python · PyTorch · OpenCV · YOLO`)**
   - Overhead edge cameras monitor groups of individual parking stalls mapped to calibrated **Region-of-Interest (ROI) polygons**.
   - Real-time vehicle detection + ROI overlap/crop classification evaluates every stall state continuously.
   - **Temporal hysteresis filtering** prevents moving vehicles in drive aisles from triggering false occupancy flickers.

2. **Central Guidance & Routing Engine (`FastAPI · WebSockets · MQTT · RS-485`)**
   - Aggregates all **300 individual slot states** into real-time zone totals, main **entrance car counters**, and **internal intersection directional counts** (`← Left`, `↑ Straight`, `→ Right`).
   - Streams instant updates to management displays and encodes CRC-16/MODBUS binary frames for physical signage controllers.

3. **Physical Signage Hardware (`Embedded C · ESP32 · Custom KiCad PCB`)**
   - Custom controller PCB (`SPG-CTRL-v1`) featuring wide-input `12V–24V DC` surge/reverse-polarity protected power, ESD-protected half-duplex RS-485 bus, and high-current MOSFET LED arrow drivers.
   - Embedded C firmware with hardware watchdog supervision and automatic **amber offline fallback** if backend communication drops.

---

## 3. LEED Sustainability & Facility Impact

Automated parking guidance directly supports green-building operational goals:
- **Reduced Cruising Time:** Directing drivers at facility entrances and every internal intersection cuts unnecessary aisle circling during peak mall hours.
- **Lower Indoor Emissions & HVAC Load:** Less low-speed idling inside the parking structure decreases CO/NOx spikes, helping demand-controlled exhaust ventilation operate more efficiently.
- **Improved Visitor Experience:** High-contrast entrance counters (`OPEN / LIMITED / FULL`) and directional arrows reduce entry-ramp queues and driver frustration.

---

## 4. Field Engineering Lessons Learned

| Real-World Challenge | Engineering Solution |
| --- | --- |
| **Headlight glare & shifting daylight/shadows** | Calibrated per-slot ROI polygons paired with secondary CNN crop classification and confidence thresholds. |
| **False flips from cars driving through aisles** | Multi-frame temporal hysteresis requiring consecutive frames before committing a state change. |
| **Electrical noise over long garage cable runs** | Differential half-duplex RS-485 with `SM712` TVS ESD diodes, switchable 120Ω bus termination, and CRC-16/MODBUS frame verification. |
| **Network or server maintenance windows** | Hardware task watchdog + 15-second timeout transitioning physical arrows to safe amber fallback mode. |

---

> **Confidentiality & Reference Notice:** This open-source repository and its interactive web simulator represent a modernized reference architecture inspired by the 2019 Galleria40 production deployment. All live data, camera addresses, and test scenarios in this repository are synthetic; no proprietary client footage or private site infrastructure data is exposed.
