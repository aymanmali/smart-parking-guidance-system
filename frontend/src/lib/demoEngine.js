/**
 * Standalone client-side 300-slot parking guidance & RS-485 protocol engine.
 *
 * Automatically activates when the FastAPI backend is not reachable (e.g., static
 * Vercel deployment), providing full interactive fidelity—including bit-exact
 * CRC-16/MODBUS RS-485 frames matching `backend/protocol.py` and
 * `firmware/main/rs485_protocol.c`.
 */

const ZONES_META = [
  { id: "ZONE-A", code: "A", name: "Zone A — North-West", color: "#22c55e" },
  { id: "ZONE-B", code: "B", name: "Zone B — North-East", color: "#3b82f6" },
  { id: "ZONE-C", code: "C", name: "Zone C — South-West", color: "#a855f7" },
  { id: "ZONE-D", code: "D", name: "Zone D — South-East", color: "#f59e0b" },
];

const ENTRANCES_META = [
  {
    id: "ENT-NORTH",
    name: "North Main Entrance",
    display_node_id: "SIGN-ENT-01",
    rs485_address: 1,
    mqtt_topic: "parking/displays/entrance/ENT-NORTH",
    zones_displayed: ["ZONE-A", "ZONE-B", "ZONE-C", "ZONE-D"],
    recommended_zones: ["ZONE-A", "ZONE-B"],
  },
  {
    id: "ENT-SOUTH",
    name: "South Main Entrance",
    display_node_id: "SIGN-ENT-02",
    rs485_address: 2,
    mqtt_topic: "parking/displays/entrance/ENT-SOUTH",
    zones_displayed: ["ZONE-C", "ZONE-D", "ZONE-A", "ZONE-B"],
    recommended_zones: ["ZONE-C", "ZONE-D"],
  },
];

const INTERSECTIONS_META = [
  {
    id: "INT-1",
    name: "North Entry Junction",
    display_node_id: "SIGN-INT-01",
    rs485_address: 11,
    mqtt_topic: "parking/displays/intersection/INT-1",
    branches: [
      { direction: "left", label: "Zone A (NW)", zone_ids: ["ZONE-A"] },
      { direction: "straight", label: "South Zones (C & D)", zone_ids: ["ZONE-C", "ZONE-D"] },
      { direction: "right", label: "Zone B (NE)", zone_ids: ["ZONE-B"] },
    ],
  },
  {
    id: "INT-2",
    name: "Central West Spine",
    display_node_id: "SIGN-INT-02",
    rs485_address: 12,
    mqtt_topic: "parking/displays/intersection/INT-2",
    branches: [
      { direction: "left", label: "Zone A (NW)", zone_ids: ["ZONE-A"] },
      { direction: "straight", label: "Zone B & D (East)", zone_ids: ["ZONE-B", "ZONE-D"] },
      { direction: "right", label: "Zone C (SW)", zone_ids: ["ZONE-C"] },
    ],
  },
  {
    id: "INT-3",
    name: "Central East Spine",
    display_node_id: "SIGN-INT-03",
    rs485_address: 13,
    mqtt_topic: "parking/displays/intersection/INT-3",
    branches: [
      { direction: "left", label: "Zone D (SE)", zone_ids: ["ZONE-D"] },
      { direction: "straight", label: "Zone A & C (West)", zone_ids: ["ZONE-A", "ZONE-C"] },
      { direction: "right", label: "Zone B (NE)", zone_ids: ["ZONE-B"] },
    ],
  },
  {
    id: "INT-4",
    name: "South Entry Junction",
    display_node_id: "SIGN-INT-04",
    rs485_address: 14,
    mqtt_topic: "parking/displays/intersection/INT-4",
    branches: [
      { direction: "left", label: "Zone D (SE)", zone_ids: ["ZONE-D"] },
      { direction: "straight", label: "North Zones (A & B)", zone_ids: ["ZONE-A", "ZONE-B"] },
      { direction: "right", label: "Zone C (SW)", zone_ids: ["ZONE-C"] },
    ],
  },
];

const VEHICLES = ["car", "car", "car", "suv", "truck", "motorcycle"];

function computeStatus(available, total) {
  if (available <= 0) return "FULL";
  if (total > 0 && available / total <= 0.12) return "LIMITED";
  return "OPEN";
}

function crc16Modbus(bytes) {
  let crc = 0xffff;
  for (let i = 0; i < bytes.length; i++) {
    crc ^= bytes[i];
    for (let bit = 0; bit < 8; bit++) {
      if (crc & 0x0001) {
        crc = (crc >>> 1) ^ 0xa001;
      } else {
        crc >>>= 1;
      }
    }
  }
  return crc & 0xffff;
}

function toHex(bytes) {
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function packFrameHex(addr, cmd, payload) {
  const body = [addr & 0xff, cmd & 0xff, payload.length & 0xff, ...payload];
  const crc = crc16Modbus(body);
  const frame = [0xaa, 0x55, ...body, crc & 0xff, (crc >>> 8) & 0xff];
  return toHex(frame);
}

function u16BE(val) {
  const v = Math.max(0, Math.min(0xffff, val | 0));
  return [(v >>> 8) & 0xff, v & 0xff];
}

function encodeEntranceFrameHex(addr, totalFree, zoneFree, isOpen) {
  const z = [zoneFree[0] || 0, zoneFree[1] || 0, zoneFree[2] || 0, zoneFree[3] || 0];
  const payload = [
    ...u16BE(totalFree),
    ...u16BE(z[0]),
    ...u16BE(z[1]),
    ...u16BE(z[2]),
    ...u16BE(z[3]),
    isOpen ? 0x01 : 0x00,
  ];
  return packFrameHex(addr, 0x01, payload);
}

function encodeIntersectionFrameHex(addr, leftFree, straightFree, rightFree) {
  let flags = 0;
  if (leftFree > 0) flags |= 0x01;
  if (straightFree > 0) flags |= 0x02;
  if (rightFree > 0) flags |= 0x04;
  const payload = [...u16BE(leftFree), ...u16BE(straightFree), ...u16BE(rightFree), flags];
  return packFrameHex(addr, 0x02, payload);
}

// Deterministic PRNG for clean initial state
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export class DemoParkingEngine {
  constructor() {
    this.slots = [];
    this.cameras = [];
    const now = new Date().toISOString();

    let camIndex = 1;
    ZONES_META.forEach((z, zIdx) => {
      let slotNum = 1;
      for (let localCam = 0; localCam < 3; localCam++) {
        const camId = `CAM-${String(camIndex).padStart(2, "0")}`;
        for (let row = 0; row < 5; row++) {
          for (let col = 0; col < 5; col++) {
            const slotId = `${z.code}-${String(slotNum).padStart(3, "0")}`;
            const slotType =
              slotNum <= 4 ? "accessible" : slotNum <= 10 ? "ev_charging" : "standard";
            const quadX = (zIdx % 2) * 16;
            const quadY = Math.floor(zIdx / 2) * 6;
            this.slots.push({
              id: slotId,
              zone_id: z.id,
              camera_id: camId,
              aisle: `${z.code}${localCam + 1}`,
              slot_type: slotType,
              map_pos: { x: quadX + localCam * 5 + col, y: quadY + row },
              occupied: false,
              confidence: 0.96,
              vehicle_class: null,
              source: "demo_init",
              updated_at: now,
            });
            slotNum++;
          }
        }
        this.cameras.push({
          id: camId,
          name: `${z.code}-Aisle-${localCam + 1} Edge Cam`,
          zone_id: z.id,
          rtsp_url: `rtsp://edge-cam-${String(camIndex).padStart(2, "0")}.parking.local:554/stream1`,
          resolution: [1280, 720],
          fps: 15.0,
          online: true,
          slot_count: 25,
          occupied_count: 0,
          inference_ms: 10.4 + (camIndex % 4) * 0.8,
          last_frame_at: now,
        });
        camIndex++;
      }
    });

    this.applyScenario("balanced", 42);
  }

  _syncCameras(now) {
    for (const cam of this.cameras) {
      cam.occupied_count = this.slots.filter((s) => s.camera_id === cam.id && s.occupied).length;
      cam.last_frame_at = now;
    }
  }

  applyScenario(scenario, seed = null) {
    const rand = seed !== null ? mulberry32(seed) : Math.random;
    const now = new Date().toISOString();

    let probs = { "ZONE-A": 0.45, "ZONE-B": 0.35, "ZONE-C": 0.5, "ZONE-D": 0.38 };
    if (scenario === "empty") {
      probs = { "ZONE-A": 0, "ZONE-B": 0, "ZONE-C": 0, "ZONE-D": 0 };
    } else if (scenario === "morning_rush") {
      probs = { "ZONE-A": 0.92, "ZONE-B": 0.84, "ZONE-C": 0.65, "ZONE-D": 0.48 };
    } else if (scenario === "peak_full") {
      probs = { "ZONE-A": 1.0, "ZONE-B": 1.0, "ZONE-C": 0.98, "ZONE-D": 0.96 };
    } else if (scenario === "zone_a_full") {
      probs = { "ZONE-A": 1.0, "ZONE-B": 0.4, "ZONE-C": 0.3, "ZONE-D": 0.25 };
    }

    for (const slot of this.slots) {
      const occ = rand() < (probs[slot.zone_id] ?? 0.4);
      slot.occupied = occ;
      slot.confidence = Number((0.88 + rand() * 0.11).toFixed(3));
      slot.vehicle_class = occ ? VEHICLES[Math.floor(rand() * VEHICLES.length)] : null;
      slot.source = `demo:${scenario}`;
      slot.updated_at = now;
    }

    this._syncCameras(now);
    return this.getSnapshot();
  }

  toggleSlot(slotId) {
    const slot = this.slots.find((s) => s.id === slotId);
    if (!slot) return this.getSnapshot();
    const now = new Date().toISOString();
    slot.occupied = !slot.occupied;
    slot.confidence = 1.0;
    slot.vehicle_class = slot.occupied ? "car" : null;
    slot.source = "manual_override";
    slot.updated_at = now;
    this._syncCameras(now);
    return this.getSnapshot();
  }

  stepTraffic(transitions = 3) {
    const now = new Date().toISOString();
    for (let i = 0; i < transitions; i++) {
      const idx = Math.floor(Math.random() * this.slots.length);
      const slot = this.slots[idx];
      slot.occupied = !slot.occupied;
      slot.confidence = Number((0.87 + Math.random() * 0.12).toFixed(3));
      slot.vehicle_class = slot.occupied
        ? VEHICLES[Math.floor(Math.random() * VEHICLES.length)]
        : null;
      slot.source = "demo_live_sim";
      slot.updated_at = now;
    }
    this._syncCameras(now);
    return this.getSnapshot();
  }

  getSnapshot() {
    const now = new Date().toISOString();
    const zones = ZONES_META.map((z) => {
      const zSlots = this.slots.filter((s) => s.zone_id === z.id);
      const total = zSlots.length;
      const occupied = zSlots.filter((s) => s.occupied).length;
      const available = total - occupied;
      return {
        ...z,
        total_slots: total,
        occupied_slots: occupied,
        available_slots: available,
        occupancy_rate: Number((occupied / total).toFixed(4)),
        status: computeStatus(available, total),
      };
    });

    const zoneMap = Object.fromEntries(zones.map((z) => [z.id, z]));
    const total = this.slots.length;
    const occupied = this.slots.filter((s) => s.occupied).length;
    const available = total - occupied;

    const entrances = ENTRANCES_META.map((meta) => {
      const zCounts = meta.zones_displayed.map((zid) => {
        const z = zoneMap[zid];
        return {
          zone_id: z.id,
          code: z.code,
          name: z.name,
          available: z.available_slots,
          total: z.total_slots,
          status: z.status,
        };
      });
      const preferred = meta.recommended_zones
        .map((zid) => zoneMap[zid])
        .filter((z) => z && z.available_slots > 0);
      const openAll = zones.filter((z) => z.available_slots > 0);
      const pool = preferred.length > 0 ? preferred : openAll;
      const best =
        pool.length > 0
          ? pool.reduce((a, b) => (b.available_slots > a.available_slots ? b : a))
          : null;

      return {
        ...meta,
        total_slots: total,
        available_slots: available,
        occupied_slots: occupied,
        status: computeStatus(available, total),
        zones: zCounts,
        recommended_zone: best ? best.name : null,
        rs485_frame_hex: encodeEntranceFrameHex(
          meta.rs485_address,
          available,
          zCounts.map((zc) => zc.available),
          available > 0
        ),
        updated_at: now,
      };
    });

    const intersections = INTERSECTIONS_META.map((meta) => {
      const counts = { left: 0, straight: 0, right: 0 };
      const branches = meta.branches.map((br) => {
        const brTotal = br.zone_ids.reduce((acc, zid) => acc + zoneMap[zid].total_slots, 0);
        const brAvail = br.zone_ids.reduce((acc, zid) => acc + zoneMap[zid].available_slots, 0);
        counts[br.direction] = brAvail;
        return {
          ...br,
          available: brAvail,
          total: brTotal,
          status: computeStatus(brAvail, brTotal),
        };
      });
      return {
        ...meta,
        branches,
        rs485_frame_hex: encodeIntersectionFrameHex(
          meta.rs485_address,
          counts.left,
          counts.straight,
          counts.right
        ),
        updated_at: now,
      };
    });

    return {
      facility: {
        id: "FAC-MAIN-300",
        name: "SmartPark Central 300",
        total_slots: total,
        occupied_slots: occupied,
        available_slots: available,
        occupancy_rate: Number((occupied / total).toFixed(4)),
        status: computeStatus(available, total),
        cameras_online: this.cameras.filter((c) => c.online).length,
        cameras_total: this.cameras.length,
        updated_at: now,
      },
      zones,
      entrances,
      intersections,
      cameras: this.cameras.map((c) => ({ ...c })),
      slots: this.slots.map((s) => ({ ...s })),
    };
  }
}
