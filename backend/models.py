"""Pydantic data models for parking state, signage displays, and CV ingestion."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DisplayStatus = Literal["OPEN", "LIMITED", "FULL"]
Direction = Literal["left", "straight", "right"]


class MapPosition(BaseModel):
    x: int
    y: int


class SlotState(BaseModel):
    id: str
    zone_id: str
    camera_id: str
    aisle: str
    slot_type: str = "standard"
    map_pos: MapPosition
    occupied: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    vehicle_class: str | None = None
    source: str = "init"
    updated_at: datetime


class ZoneSummary(BaseModel):
    id: str
    code: str
    name: str
    color: str
    total_slots: int
    occupied_slots: int
    available_slots: int
    occupancy_rate: float
    status: DisplayStatus


class EntranceZoneCount(BaseModel):
    zone_id: str
    code: str
    name: str
    available: int
    total: int
    status: DisplayStatus


class EntranceDisplayState(BaseModel):
    id: str
    name: str
    display_node_id: str
    rs485_address: int
    mqtt_topic: str
    total_slots: int
    available_slots: int
    occupied_slots: int
    status: DisplayStatus
    zones: list[EntranceZoneCount]
    recommended_zone: str | None = None
    rs485_frame_hex: str = ""
    updated_at: datetime


class IntersectionBranchState(BaseModel):
    direction: Direction
    label: str
    zone_ids: list[str]
    available: int
    total: int
    status: DisplayStatus


class IntersectionDisplayState(BaseModel):
    id: str
    name: str
    display_node_id: str
    rs485_address: int
    mqtt_topic: str
    branches: list[IntersectionBranchState]
    rs485_frame_hex: str = ""
    updated_at: datetime


class CameraHealth(BaseModel):
    id: str
    name: str
    zone_id: str
    rtsp_url: str
    resolution: list[int]
    fps: float
    online: bool = True
    slot_count: int
    occupied_count: int = 0
    inference_ms: float = 0.0
    last_frame_at: datetime | None = None


class FacilitySummary(BaseModel):
    id: str
    name: str
    total_slots: int
    occupied_slots: int
    available_slots: int
    occupancy_rate: float
    status: DisplayStatus
    cameras_online: int
    cameras_total: int
    updated_at: datetime


class FacilitySnapshot(BaseModel):
    facility: FacilitySummary
    zones: list[ZoneSummary]
    entrances: list[EntranceDisplayState]
    intersections: list[IntersectionDisplayState]
    cameras: list[CameraHealth]
    slots: list[SlotState]


class SlotObservation(BaseModel):
    slot_id: str
    occupied: bool
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    vehicle_class: str | None = "car"


class CameraBatchUpdate(BaseModel):
    camera_id: str
    fps: float = 15.0
    inference_ms: float = 12.0
    observations: list[SlotObservation]


class ManualSlotOverride(BaseModel):
    occupied: bool
    vehicle_class: str | None = "car"


class ScenarioRequest(BaseModel):
    scenario: Literal["empty", "morning_rush", "peak_full", "zone_a_full", "balanced"]
