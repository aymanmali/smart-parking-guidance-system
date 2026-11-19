#!/usr/bin/env python3
"""Generate deterministic 300-slot facility topology and camera ROI polygons.

Facility Layout (Single-Level, 4 Zones, 300 Slots):
- 4 Zones: Zone A, Zone B, Zone C, Zone D (75 slots each = 300 slots)
- 12 Edge Cameras: CAM-01..CAM-12 (3 cameras per zone, 25 slots per camera)
- 2 Facility Entrances: ENT-NORTH (North Entrance), ENT-SOUTH (South Entrance)
- 4 Internal Intersections: INT-1..INT-4 with directional guidance branches (left, straight, right)
"""

from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent

ZONES = [
    {"id": "ZONE-A", "code": "A", "name": "Zone A — North-West", "color": "#22c55e"},
    {"id": "ZONE-B", "code": "B", "name": "Zone B — North-East", "color": "#3b82f6"},
    {"id": "ZONE-C", "code": "C", "name": "Zone C — South-West", "color": "#a855f7"},
    {"id": "ZONE-D", "code": "D", "name": "Zone D — South-East", "color": "#f59e0b"},
]

CAMERAS_PER_ZONE = 3
SLOTS_PER_CAMERA = 25  # 3 * 25 = 75 slots/zone; 4 * 75 = 300 slots total


def build_topology() -> dict:
    zones_out = []
    cameras_out = []
    slots_out = []

    cam_index = 1
    for z_idx, z in enumerate(ZONES):
        zone_slot_ids: list[str] = []
        zone_cam_ids: list[str] = []
        slot_num = 1

        for local_cam in range(CAMERAS_PER_ZONE):
            cam_id = f"CAM-{cam_index:02d}"
            zone_cam_ids.append(cam_id)
            cam_slot_ids: list[str] = []

            # 25 slots per camera laid out in 5 rows x 5 cols in camera perspective
            for row in range(5):
                for col in range(5):
                    slot_id = f"{z['code']}-{slot_num:03d}"
                    # Assign accessible / EV / standard types realistically
                    if slot_num <= 4:
                        slot_type = "accessible"
                    elif slot_num <= 10:
                        slot_type = "ev_charging"
                    else:
                        slot_type = "standard"

                    # Global 2D map coordinates for dashboard visualization
                    # Zones laid out in 2x2 grid: A (top-left), B (top-right), C (bottom-left), D (bottom-right)
                    quad_x = (z_idx % 2) * 16
                    quad_y = (z_idx // 2) * 6
                    map_x = quad_x + local_cam * 5 + col
                    map_y = quad_y + row

                    slots_out.append(
                        {
                            "id": slot_id,
                            "zone_id": z["id"],
                            "camera_id": cam_id,
                            "aisle": f"{z['code']}{local_cam + 1}",
                            "slot_type": slot_type,
                            "map_pos": {"x": map_x, "y": map_y},
                        }
                    )
                    zone_slot_ids.append(slot_id)
                    cam_slot_ids.append(slot_id)
                    slot_num += 1

            cameras_out.append(
                {
                    "id": cam_id,
                    "name": f"{z['code']}-Aisle-{local_cam + 1} Edge Cam",
                    "zone_id": z["id"],
                    "rtsp_url": f"rtsp://edge-cam-{cam_index:02d}.parking.local:554/stream1",
                    "resolution": [1280, 720],
                    "fps": 15,
                    "slot_ids": cam_slot_ids,
                }
            )
            cam_index += 1

        zones_out.append(
            {
                "id": z["id"],
                "code": z["code"],
                "name": z["name"],
                "color": z["color"],
                "total_slots": len(zone_slot_ids),
                "camera_ids": zone_cam_ids,
            }
        )

    entrances = [
        {
            "id": "ENT-NORTH",
            "name": "North Main Entrance",
            "display_node_id": "SIGN-ENT-01",
            "rs485_address": 1,
            "mqtt_topic": "parking/displays/entrance/ENT-NORTH",
            "zones_displayed": ["ZONE-A", "ZONE-B", "ZONE-C", "ZONE-D"],
            "recommended_zones": ["ZONE-A", "ZONE-B"],
        },
        {
            "id": "ENT-SOUTH",
            "name": "South Main Entrance",
            "display_node_id": "SIGN-ENT-02",
            "rs485_address": 2,
            "mqtt_topic": "parking/displays/entrance/ENT-SOUTH",
            "zones_displayed": ["ZONE-C", "ZONE-D", "ZONE-A", "ZONE-B"],
            "recommended_zones": ["ZONE-C", "ZONE-D"],
        },
    ]

    intersections = [
        {
            "id": "INT-1",
            "name": "North Entry Junction",
            "display_node_id": "SIGN-INT-01",
            "rs485_address": 11,
            "mqtt_topic": "parking/displays/intersection/INT-1",
            "branches": [
                {"direction": "left", "label": "Zone A (NW)", "zone_ids": ["ZONE-A"]},
                {"direction": "straight", "label": "South Zones (C & D)", "zone_ids": ["ZONE-C", "ZONE-D"]},
                {"direction": "right", "label": "Zone B (NE)", "zone_ids": ["ZONE-B"]},
            ],
        },
        {
            "id": "INT-2",
            "name": "Central West Spine",
            "display_node_id": "SIGN-INT-02",
            "rs485_address": 12,
            "mqtt_topic": "parking/displays/intersection/INT-2",
            "branches": [
                {"direction": "left", "label": "Zone A (NW)", "zone_ids": ["ZONE-A"]},
                {"direction": "straight", "label": "Zone B & D (East)", "zone_ids": ["ZONE-B", "ZONE-D"]},
                {"direction": "right", "label": "Zone C (SW)", "zone_ids": ["ZONE-C"]},
            ],
        },
        {
            "id": "INT-3",
            "name": "Central East Spine",
            "display_node_id": "SIGN-INT-03",
            "rs485_address": 13,
            "mqtt_topic": "parking/displays/intersection/INT-3",
            "branches": [
                {"direction": "left", "label": "Zone D (SE)", "zone_ids": ["ZONE-D"]},
                {"direction": "straight", "label": "Zone A & C (West)", "zone_ids": ["ZONE-A", "ZONE-C"]},
                {"direction": "right", "label": "Zone B (NE)", "zone_ids": ["ZONE-B"]},
            ],
        },
        {
            "id": "INT-4",
            "name": "South Entry Junction",
            "display_node_id": "SIGN-INT-04",
            "rs485_address": 14,
            "mqtt_topic": "parking/displays/intersection/INT-4",
            "branches": [
                {"direction": "left", "label": "Zone D (SE)", "zone_ids": ["ZONE-D"]},
                {"direction": "straight", "label": "North Zones (A & B)", "zone_ids": ["ZONE-A", "ZONE-B"]},
                {"direction": "right", "label": "Zone C (SW)", "zone_ids": ["ZONE-C"]},
            ],
        },
    ]

    return {
        "facility": {
            "id": "FAC-MAIN-300",
            "name": "SmartPark Central 300",
            "total_slots": len(slots_out),
            "layout": "single_level_multi_zone",
        },
        "zones": zones_out,
        "cameras": cameras_out,
        "entrances": entrances,
        "intersections": intersections,
        "slots": slots_out,
    }


def build_rois(topology: dict) -> dict:
    """Generate calibrated normalized (0.0..1.0) polygon ROIs for every slot per camera.

    Each 1280x720 camera view covers 25 slots arranged in a 5x5 slightly trapezoidal
    parking-lot perspective grid.
    """
    rois_by_camera: dict[str, dict] = {}
    for cam in topology["cameras"]:
        width, height = cam["resolution"]
        cam_rois = []
        for idx, slot_id in enumerate(cam["slot_ids"]):
            row = idx // 5
            col = idx % 5
            # Leave 8% margin and subtle perspective slant
            x0 = 0.06 + col * 0.178
            y0 = 0.10 + row * 0.165
            w = 0.155
            h = 0.135
            slant = 0.008 * (2 - col)
            polygon = [
                [round((x0 + slant) * width), round(y0 * height)],
                [round((x0 + w + slant) * width), round(y0 * height)],
                [round((x0 + w) * width), round((y0 + h) * height)],
                [round(x0 * width), round((y0 + h) * height)],
            ]
            cam_rois.append({"slot_id": slot_id, "polygon": polygon})
        rois_by_camera[cam["id"]] = {
            "resolution": cam["resolution"],
            "slots": cam_rois,
        }
    return rois_by_camera


def main() -> None:
    topology = build_topology()
    rois = build_rois(topology)

    (CONFIG_DIR / "facility_topology.json").write_text(
        json.dumps(topology, indent=2) + "\n", encoding="utf-8"
    )
    (CONFIG_DIR / "rois.json").write_text(
        json.dumps(rois, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Generated facility_topology.json ({topology['facility']['total_slots']} slots, "
        f"{len(topology['cameras'])} cameras, {len(topology['entrances'])} entrances, "
        f"{len(topology['intersections'])} intersections) and rois.json"
    )


if __name__ == "__main__":
    main()
