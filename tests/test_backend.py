"""Tests for FastAPI backend, 300-slot routing engine, and WebSocket streaming."""

from fastapi.testclient import TestClient

from backend.main import app, state_manager


def test_health_and_300_slots():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["total_slots"] == 300
    assert body["cameras"] == 12


def test_zone_a_full_routes_intersection_displays():
    client = TestClient(app)
    res = client.post("/api/v1/simulation/scenario", json={"scenario": "zone_a_full"})
    assert res.status_code == 200
    snap = res.json()

    zone_a = next(z for z in snap["zones"] if z["id"] == "ZONE-A")
    assert zone_a["available_slots"] == 0
    assert zone_a["status"] == "FULL"

    # INT-1 left branch points to Zone A -> must show 0 FULL
    int1 = next(i for i in snap["intersections"] if i["id"] == "INT-1")
    left_branch = next(b for b in int1["branches"] if b["direction"] == "left")
    assert left_branch["available"] == 0
    assert left_branch["status"] == "FULL"
    assert len(int1["rs485_frame_hex"]) > 0


def test_camera_batch_ingestion_and_manual_override():
    client = TestClient(app)
    client.post("/api/v1/simulation/scenario", json={"scenario": "empty"})

    batch = {
        "camera_id": "CAM-01",
        "fps": 15.0,
        "inference_ms": 9.4,
        "observations": [
            {"slot_id": "A-001", "occupied": True, "confidence": 0.96, "vehicle_class": "car"},
            {"slot_id": "A-002", "occupied": True, "confidence": 0.91, "vehicle_class": "truck"},
        ],
    }
    res = client.post("/api/v1/ingest/camera", json=batch)
    assert res.status_code == 200
    assert res.json()["changed"] == 2

    # Entrances should report 298 available out of 300
    ent = client.get("/api/v1/entrances/ENT-NORTH").json()
    assert ent["available_slots"] == 298
    assert ent["occupied_slots"] == 2

    # Manual override flips A-001 back to free
    ov = client.patch("/api/v1/slots/A-001", json={"occupied": False})
    assert ov.status_code == 200
    assert ov.json()["occupied"] is False
    assert state_manager.slots["A-001"].occupied is False


def test_websocket_live_receives_initial_snapshot():
    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        data = ws.receive_json()
        assert data["facility"]["total_slots"] == 300
        assert len(data["entrances"]) == 2
        assert len(data["intersections"]) == 4
