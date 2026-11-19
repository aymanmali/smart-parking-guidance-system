# Marketing & Showcase Kit — SmartPark 300 (Galleria40 LEED Case Study)

Ready-to-use copy for LinkedIn, GitHub, and your resume/portfolio.

---

## 1. LinkedIn Launch Post (Full Technical Story)

> **Back in 2019, I designed and installed a 300-slot Computer Vision Smart Parking Guidance System at Galleria40 Mall (LEED Certified) in Egypt.**
>
> Today, I open-sourced a modernized reference architecture—complete with an interactive live simulator so you can test the Entrance Counters and Intersection Directional Signs right in your browser.
>
> **Why it mattered in a LEED-certified facility:**
> Drivers circling for open stalls create entrance queues, indoor CO/NOx spikes, and heavier garage ventilation loads. Multi-camera computer vision monitors ~25 stalls per camera (no per-stall ultrasonic wiring) and guides drivers cleanly at every entrance and internal intersection.
>
> **What's inside the full-stack repo (from Silicon to Cloud UI):**
> - **Computer Vision (`Python · PyTorch · OpenCV · YOLO`):** Real-time vehicle detection + calibrated ROI polygon matching + PyTorch CNN crop classifier + temporal hysteresis to prevent passing-car flicker.
> - **Backend & Routing (`FastAPI · WebSockets · MQTT · RS-485`):** Aggregates 300 live slots into entrance totals and intersection directional branches (`← Left / ↑ Straight / → Right`) with CRC-16/MODBUS wire framing.
> - **Embedded C Firmware (`ESP32 / ESP-IDF`):** Half-duplex RS-485 frame decoder, MOSFET LED arrow HAL, task watchdog, and 15-second amber offline fallback (+ host-run C unit tests).
> - **Custom Hardware (`KiCad PCB`):** 2-layer `SPG-CTRL-v1` controller schematic, PCB layout, and production BOM (12–24V buck power stage, ESD-protected RS-485, 6× MOSFET LED arrow drivers).
>
> **Try the Live Interactive Demo:** https://smart-parking-guidance-system.vercel.app  
> *(Try clicking "Zone A Full" on the Intersection Signs tab or toggling any of the 300 slots!)*
>
> **Explore the Open-Source Repo:** https://github.com/aymanmali/smart-parking-guidance-system
>
> `#ComputerVision` `#PyTorch` `#YOLO` `#FastAPI` `#EmbeddedC` `#PCBDesign` `#KiCad` `#SmartParking` `#IoT` `#LEED` `#SmartBuildings`

---

## 2. Short & Punchy LinkedIn Post (Ideal for a 20-Second Screen Recording)

> In 2019, I built and deployed a 300-slot Computer Vision Smart Parking Guidance System at **Galleria40 Mall (LEED Certified)** in Egypt—spanning **PyTorch/OpenCV/YOLO**, **FastAPI**, **ESP32 Embedded C**, and custom **KiCad PCB** controllers driving real entrance and intersection LED displays.
>
> I just open-sourced a modernized reference architecture + interactive live demo where you can watch all 300 slots, Entrance counters, Intersection directional signs, and live RS-485 CRC-16 frames react in real time:
>
> Live Demo: https://smart-parking-guidance-system.vercel.app  
> GitHub: https://github.com/aymanmali/smart-parking-guidance-system
>
> `#ComputerVision` `#EmbeddedSystems` `#IoT` `#SmartParking` `#LEED` `#Python` `#FastAPI`

---

## 3. Resume / CV Project Bullets

**Smart Parking Guidance & Management System — Galleria40 Mall (LEED Certified), Egypt (2019)**  
*Python, PyTorch, OpenCV, YOLO, FastAPI, Edge Cameras, Embedded C (ESP32), KiCad PCB Design*
- Architected and commissioned an end-to-end computer-vision parking guidance system monitoring **300 individual slots** across a LEED-certified commercial complex, reducing driver stall-search cruising time and indoor vehicle idling.
- Built real-time **YOLO + OpenCV ROI polygon** and **PyTorch CNN** classification pipelines with temporal hysteresis filtering across multi-camera feeds, streaming live occupancy via **FastAPI WebSockets** and **RS-485 (CRC-16) / MQTT** bridges.
- Designed custom **ESP32 Embedded C firmware** and **2-layer KiCad controller PCBs** (ESD-protected RS-485, 12–24V MOSFET LED drivers, watchdog offline fallback) to drive facility entrance counters and internal intersection directional signage.
- Published open-source reference architecture and interactive live simulator: `github.com/aymanmali/smart-parking-guidance-system`
