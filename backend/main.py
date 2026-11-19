"""FastAPI entrypoint for Smart Parking Guidance & Management System."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.bridge import HardwareBridge
from backend.config import settings
from backend.database import AnalyticsStore
from backend.models import (
    CameraBatchUpdate,
    CameraHealth,
    EntranceDisplayState,
    FacilitySnapshot,
    IntersectionDisplayState,
    ManualSlotOverride,
    ScenarioRequest,
    SlotState,
    ZoneSummary,
)
from backend.state import ParkingStateManager
from backend.ws_manager import WebSocketManager

analytics_store = AnalyticsStore(settings.sqlite_path)
state_manager = ParkingStateManager(settings.topology_path, analytics=analytics_store)
hardware_bridge = HardwareBridge(settings)
ws_manager = WebSocketManager()

_sim_running = False
_sim_task: asyncio.Task | None = None


async def _broadcast_and_publish() -> FacilitySnapshot:
    snapshot = state_manager.get_snapshot()
    hardware_bridge.publish_displays(snapshot.entrances, snapshot.intersections)
    await ws_manager.broadcast_json(snapshot.model_dump(mode="json"))
    return snapshot


async def _background_simulator_loop() -> None:
    global _sim_running
    while _sim_running:
        state_manager.step_random_traffic(transitions=3)
        await _broadcast_and_publish()
        await asyncio.sleep(2.0)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    global _sim_running, _sim_task
    _sim_running = False
    if _sim_task is not None:
        _sim_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _sim_task
    hardware_bridge.close()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "total_slots": len(state_manager.slots),
        "cameras": len(state_manager.cameras),
        "ws_clients": ws_manager.active_count,
        "simulator_running": _sim_running,
        "hardware_frames_published": hardware_bridge.published_count,
    }


@app.get("/api/v1/snapshot", response_model=FacilitySnapshot)
async def get_snapshot() -> FacilitySnapshot:
    return state_manager.get_snapshot()


@app.get("/api/v1/zones", response_model=list[ZoneSummary])
async def get_zones() -> list[ZoneSummary]:
    return state_manager.get_zones()


@app.get("/api/v1/slots", response_model=list[SlotState])
async def get_slots(zone_id: str | None = None, occupied: bool | None = None) -> list[SlotState]:
    slots = list(state_manager.slots.values())
    if zone_id is not None:
        slots = [s for s in slots if s.zone_id == zone_id]
    if occupied is not None:
        slots = [s for s in slots if s.occupied == occupied]
    return slots


@app.get("/api/v1/entrances", response_model=list[EntranceDisplayState])
async def get_entrances() -> list[EntranceDisplayState]:
    return state_manager.get_entrances()


@app.get("/api/v1/entrances/{entrance_id}", response_model=EntranceDisplayState)
async def get_entrance(entrance_id: str) -> EntranceDisplayState:
    for ent in state_manager.get_entrances():
        if ent.id == entrance_id:
            return ent
    raise HTTPException(status_code=404, detail=f"Entrance {entrance_id} not found")


@app.get("/api/v1/intersections", response_model=list[IntersectionDisplayState])
async def get_intersections() -> list[IntersectionDisplayState]:
    return state_manager.get_intersections()


@app.get("/api/v1/intersections/{intersection_id}", response_model=IntersectionDisplayState)
async def get_intersection(intersection_id: str) -> IntersectionDisplayState:
    for inter in state_manager.get_intersections():
        if inter.id == intersection_id:
            return inter
    raise HTTPException(status_code=404, detail=f"Intersection {intersection_id} not found")


@app.get("/api/v1/cameras", response_model=list[CameraHealth])
async def get_cameras() -> list[CameraHealth]:
    return list(state_manager.cameras.values())


@app.post("/api/v1/ingest/camera")
async def ingest_camera_batch(batch: CameraBatchUpdate) -> dict:
    changed = state_manager.apply_camera_batch(batch)
    await _broadcast_and_publish()
    return {"camera_id": batch.camera_id, "processed": len(batch.observations), "changed": changed}


@app.patch("/api/v1/slots/{slot_id}", response_model=SlotState)
async def override_slot(slot_id: str, body: ManualSlotOverride) -> SlotState:
    try:
        slot = state_manager.set_slot_override(slot_id, body.occupied, body.vehicle_class)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await _broadcast_and_publish()
    return slot


@app.post("/api/v1/simulation/scenario", response_model=FacilitySnapshot)
async def apply_scenario(req: ScenarioRequest) -> FacilitySnapshot:
    state_manager.apply_scenario(req.scenario)
    return await _broadcast_and_publish()


@app.post("/api/v1/simulation/toggle")
async def toggle_simulation(running: bool) -> dict:
    global _sim_running, _sim_task
    if running and not _sim_running:
        _sim_running = True
        _sim_task = asyncio.create_task(_background_simulator_loop())
    elif not running and _sim_running:
        _sim_running = False
        if _sim_task is not None:
            _sim_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await _sim_task
            _sim_task = None
    return {"simulator_running": _sim_running}


@app.get("/api/v1/analytics")
async def get_analytics(limit: int = 60) -> dict:
    return {
        "snapshots": analytics_store.get_recent_snapshots(limit=limit),
        "recent_events": analytics_store.get_recent_events(limit=min(limit, 50)),
    }


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    await ws_manager.connect(ws)
    try:
        # Send immediate initial state on connect
        await ws.send_json(state_manager.get_snapshot().model_dump(mode="json"))
        while True:
            # Keep socket alive; ignore client pings/messages
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)
