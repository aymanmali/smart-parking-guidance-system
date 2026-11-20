"""Core 300-slot state manager and guidance routing engine."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime
from pathlib import Path

from backend.database import AnalyticsStore
from backend.models import (
    CameraBatchUpdate,
    CameraHealth,
    DisplayStatus,
    EntranceDisplayState,
    EntranceZoneCount,
    FacilitySnapshot,
    FacilitySummary,
    IntersectionBranchState,
    IntersectionDisplayState,
    MapPosition,
    SlotState,
    ZoneSummary,
)
from backend.protocol import encode_entrance_frame, encode_intersection_frame


def _compute_status(available: int, total: int) -> DisplayStatus:
    if available <= 0:
        return "FULL"
    if total > 0 and (available / total) <= 0.12:
        return "LIMITED"
    return "OPEN"


class ParkingStateManager:
    """Maintains live occupancy for all 300 slots and computes signage displays."""

    def __init__(self, topology_path: Path, analytics: AnalyticsStore | None = None) -> None:
        raw = json.loads(topology_path.read_text(encoding="utf-8"))
        self.facility_meta = raw["facility"]
        self.zones_meta: dict[str, dict] = {z["id"]: z for z in raw["zones"]}
        self.entrances_meta: list[dict] = raw["entrances"]
        self.intersections_meta: list[dict] = raw["intersections"]
        self.analytics = analytics

        now = datetime.now(UTC)
        self.slots: dict[str, SlotState] = {}
        for s in raw["slots"]:
            self.slots[s["id"]] = SlotState(
                id=s["id"],
                zone_id=s["zone_id"],
                camera_id=s["camera_id"],
                aisle=s["aisle"],
                slot_type=s.get("slot_type", "standard"),
                map_pos=MapPosition(**s["map_pos"]),
                occupied=False,
                confidence=1.0,
                vehicle_class=None,
                source="init",
                updated_at=now,
            )

        self.cameras: dict[str, CameraHealth] = {}
        for c in raw["cameras"]:
            self.cameras[c["id"]] = CameraHealth(
                id=c["id"],
                name=c["name"],
                zone_id=c["zone_id"],
                rtsp_url=c["rtsp_url"],
                resolution=c["resolution"],
                fps=float(c.get("fps", 15)),
                online=True,
                slot_count=len(c["slot_ids"]),
                occupied_count=0,
                inference_ms=11.5,
                last_frame_at=now,
            )

        # Initialize with a realistic ~42% balanced occupancy so dashboards look alive immediately
        self.apply_scenario("balanced", seed=42)

    def apply_camera_batch(self, batch: CameraBatchUpdate) -> int:
        """Apply occupancy observations from one edge camera; return number of changed slots."""
        now = datetime.now(UTC)
        changed_events: list[tuple[str, str, bool, str]] = []

        for obs in batch.observations:
            slot = self.slots.get(obs.slot_id)
            if slot is None:
                continue
            prev = slot.occupied
            slot.occupied = obs.occupied
            slot.confidence = obs.confidence
            slot.vehicle_class = obs.vehicle_class if obs.occupied else None
            slot.source = batch.camera_id
            slot.updated_at = now
            if prev != obs.occupied:
                changed_events.append((slot.id, slot.zone_id, obs.occupied, batch.camera_id))

        cam = self.cameras.get(batch.camera_id)
        if cam is not None:
            cam.online = True
            cam.fps = batch.fps
            cam.inference_ms = batch.inference_ms
            cam.last_frame_at = now
            cam.occupied_count = sum(
                1 for s in self.slots.values() if s.camera_id == cam.id and s.occupied
            )

        if self.analytics and changed_events:
            self.analytics.record_slot_events(changed_events)
            self._record_analytics_snapshot()

        return len(changed_events)

    def set_slot_override(self, slot_id: str, occupied: bool, vehicle_class: str | None = "car") -> SlotState:
        slot = self.slots.get(slot_id)
        if slot is None:
            raise KeyError(f"Unknown slot_id: {slot_id}")

        now = datetime.now(UTC)
        prev = slot.occupied
        slot.occupied = occupied
        slot.confidence = 1.0
        slot.vehicle_class = vehicle_class if occupied else None
        slot.source = "manual_override"
        slot.updated_at = now

        cam = self.cameras.get(slot.camera_id)
        if cam is not None:
            cam.occupied_count = sum(
                1 for s in self.slots.values() if s.camera_id == cam.id and s.occupied
            )

        if self.analytics and prev != occupied:
            self.analytics.record_slot_events([(slot.id, slot.zone_id, occupied, "manual_override")])
            self._record_analytics_snapshot()

        return slot

    def apply_scenario(self, scenario: str, seed: int | None = None) -> None:
        """Apply a preset occupancy scenario across all 300 slots."""
        rng = random.Random(seed)
        now = datetime.now(UTC)

        zone_probs: dict[str, float] = {
            "ZONE-A": 0.45,
            "ZONE-B": 0.35,
            "ZONE-C": 0.50,
            "ZONE-D": 0.38,
        }
        if scenario == "empty":
            zone_probs = {z: 0.0 for z in zone_probs}
        elif scenario == "morning_rush":
            zone_probs = {"ZONE-A": 0.92, "ZONE-B": 0.84, "ZONE-C": 0.65, "ZONE-D": 0.48}
        elif scenario == "peak_full":
            zone_probs = {"ZONE-A": 1.0, "ZONE-B": 1.0, "ZONE-C": 0.98, "ZONE-D": 0.96}
        elif scenario == "zone_a_full":
            zone_probs = {"ZONE-A": 1.0, "ZONE-B": 0.40, "ZONE-C": 0.30, "ZONE-D": 0.25}

        vehicles = ["car", "car", "car", "suv", "truck", "motorcycle"]
        for slot in self.slots.values():
            prob = zone_probs.get(slot.zone_id, 0.4)
            occ = rng.random() < prob
            slot.occupied = occ
            slot.confidence = round(rng.uniform(0.88, 0.99), 3) if occ else round(rng.uniform(0.92, 0.99), 3)
            slot.vehicle_class = rng.choice(vehicles) if occ else None
            slot.source = f"scenario:{scenario}"
            slot.updated_at = now

        for cam in self.cameras.values():
            cam.occupied_count = sum(
                1 for s in self.slots.values() if s.camera_id == cam.id and s.occupied
            )
            cam.last_frame_at = now

        if self.analytics:
            self._record_analytics_snapshot()

    def step_random_traffic(self, transitions: int = 3) -> int:
        """Simulate natural arrivals/departures across random slots."""
        if transitions <= 0:
            return 0
        now = datetime.now(UTC)
        slot_list = list(self.slots.values())
        chosen = random.sample(slot_list, k=min(transitions, len(slot_list)))
        events: list[tuple[str, str, bool, str]] = []
        vehicles = ["car", "car", "car", "suv", "truck", "motorcycle"]

        for slot in chosen:
            slot.occupied = not slot.occupied
            slot.confidence = round(random.uniform(0.87, 0.99), 3)
            slot.vehicle_class = random.choice(vehicles) if slot.occupied else None
            slot.source = "live_sim"
            slot.updated_at = now
            events.append((slot.id, slot.zone_id, slot.occupied, "live_sim"))

        for cam in self.cameras.values():
            cam.occupied_count = sum(
                1 for s in self.slots.values() if s.camera_id == cam.id and s.occupied
            )
            cam.last_frame_at = now

        if self.analytics and events:
            self.analytics.record_slot_events(events)
            self._record_analytics_snapshot()

        return len(events)

    def _record_analytics_snapshot(self) -> None:
        if not self.analytics:
            return
        total = len(self.slots)
        occupied = sum(1 for s in self.slots.values() if s.occupied)
        available = total - occupied
        rate = occupied / total if total else 0.0
        self.analytics.record_snapshot(total, occupied, available, rate)

    def get_zones(self) -> list[ZoneSummary]:
        summaries: list[ZoneSummary] = []
        for zid, meta in self.zones_meta.items():
            zone_slots = [s for s in self.slots.values() if s.zone_id == zid]
            total = len(zone_slots)
            occupied = sum(1 for s in zone_slots if s.occupied)
            available = total - occupied
            summaries.append(
                ZoneSummary(
                    id=zid,
                    code=meta["code"],
                    name=meta["name"],
                    color=meta["color"],
                    total_slots=total,
                    occupied_slots=occupied,
                    available_slots=available,
                    occupancy_rate=round(occupied / total, 4) if total else 0.0,
                    status=_compute_status(available, total),
                )
            )
        return summaries

    def get_entrances(self, zones: list[ZoneSummary] | None = None) -> list[EntranceDisplayState]:
        zones = zones or self.get_zones()
        zone_map = {z.id: z for z in zones}
        total = sum(z.total_slots for z in zones)
        occupied = sum(z.occupied_slots for z in zones)
        available = total - occupied
        now = datetime.now(UTC)
        out: list[EntranceDisplayState] = []

        for meta in self.entrances_meta:
            z_counts = [
                EntranceZoneCount(
                    zone_id=zid,
                    code=zone_map[zid].code,
                    name=zone_map[zid].name,
                    available=zone_map[zid].available_slots,
                    total=zone_map[zid].total_slots,
                    status=zone_map[zid].status,
                )
                for zid in meta["zones_displayed"]
                if zid in zone_map
            ]
            # Recommend the nearest open zone with most available slots
            preferred = [zone_map[zid] for zid in meta["recommended_zones"] if zid in zone_map and zone_map[zid].available_slots > 0]
            fallback = [z for z in zones if z.available_slots > 0]
            best = max(preferred, key=lambda z: z.available_slots) if preferred else (
                max(fallback, key=lambda z: z.available_slots) if fallback else None
            )

            status = _compute_status(available, total)
            frame = encode_entrance_frame(
                addr=meta["rs485_address"],
                total_free=available,
                zone_free=[z.available for z in z_counts],
                is_open=(available > 0),
            )
            out.append(
                EntranceDisplayState(
                    id=meta["id"],
                    name=meta["name"],
                    display_node_id=meta["display_node_id"],
                    rs485_address=meta["rs485_address"],
                    mqtt_topic=meta["mqtt_topic"],
                    total_slots=total,
                    available_slots=available,
                    occupied_slots=occupied,
                    status=status,
                    zones=z_counts,
                    recommended_zone=best.name if best else None,
                    rs485_frame_hex=frame.hex(),
                    updated_at=now,
                )
            )
        return out

    def get_intersections(self, zones: list[ZoneSummary] | None = None) -> list[IntersectionDisplayState]:
        zones = zones or self.get_zones()
        zone_map = {z.id: z for z in zones}
        now = datetime.now(UTC)
        out: list[IntersectionDisplayState] = []

        for meta in self.intersections_meta:
            branches: list[IntersectionBranchState] = []
            counts_by_dir = {"left": 0, "straight": 0, "right": 0}
            for br in meta["branches"]:
                br_total = sum(zone_map[zid].total_slots for zid in br["zone_ids"] if zid in zone_map)
                br_avail = sum(zone_map[zid].available_slots for zid in br["zone_ids"] if zid in zone_map)
                counts_by_dir[br["direction"]] = br_avail
                branches.append(
                    IntersectionBranchState(
                        direction=br["direction"],
                        label=br["label"],
                        zone_ids=br["zone_ids"],
                        available=br_avail,
                        total=br_total,
                        status=_compute_status(br_avail, br_total),
                    )
                )
            frame = encode_intersection_frame(
                addr=meta["rs485_address"],
                left_free=counts_by_dir["left"],
                straight_free=counts_by_dir["straight"],
                right_free=counts_by_dir["right"],
            )
            out.append(
                IntersectionDisplayState(
                    id=meta["id"],
                    name=meta["name"],
                    display_node_id=meta["display_node_id"],
                    rs485_address=meta["rs485_address"],
                    mqtt_topic=meta["mqtt_topic"],
                    branches=branches,
                    rs485_frame_hex=frame.hex(),
                    updated_at=now,
                )
            )
        return out

    def get_snapshot(self) -> FacilitySnapshot:
        zones = self.get_zones()
        entrances = self.get_entrances(zones)
        intersections = self.get_intersections(zones)
        total = len(self.slots)
        occupied = sum(1 for s in self.slots.values() if s.occupied)
        available = total - occupied
        now = datetime.now(UTC)
        cameras = list(self.cameras.values())

        return FacilitySnapshot(
            facility=FacilitySummary(
                id=self.facility_meta["id"],
                name=self.facility_meta["name"],
                total_slots=total,
                occupied_slots=occupied,
                available_slots=available,
                occupancy_rate=round(occupied / total, 4) if total else 0.0,
                status=_compute_status(available, total),
                cameras_online=sum(1 for c in cameras if c.online),
                cameras_total=len(cameras),
                updated_at=now,
            ),
            zones=zones,
            entrances=entrances,
            intersections=intersections,
            cameras=cameras,
            slots=list(self.slots.values()),
        )
