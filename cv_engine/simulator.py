#!/usr/bin/env python3
"""12-Camera Synthetic CV Simulator streaming 300-slot detections to FastAPI.

Simulates 12 edge cameras (25 slots each = 300 slots), renders synthetic OpenCV
frames with parked vehicles inside slot ROIs, runs the actual OpenCV ROI polygon
matcher + temporal hysteresis filter, and streams updates to `/api/v1/ingest/camera`.

Usage:
    python -m cv_engine.simulator --api-url http://localhost:8000 --interval 2.0
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path

import httpx
import numpy as np

from cv_engine.detector import ParkingVisionPipeline
from cv_engine.roi_matcher import DetectionBox

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_simulator(api_url: str, rois_path: Path, interval: float, initial_occupancy: float) -> None:
    pipeline = ParkingVisionPipeline(
        rois_path=rois_path,
        yolo_model_name=None,
        overlap_threshold=0.30,
        confirm_frames=2,
    )

    # Maintain ground-truth synthetic vehicles per slot
    rng = random.Random(123)
    slot_truth: dict[str, bool] = {}
    for cam_rois in pipeline.rois_by_camera.values():
        for roi in cam_rois:
            slot_truth[roi.slot_id] = rng.random() < initial_occupancy

    vehicles = ["car", "car", "car", "truck", "motorcycle"]
    blank_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    print(f"Starting 12-camera CV simulator -> {api_url} ({len(slot_truth)} slots)")
    with httpx.Client(timeout=5.0) as client:
        tick = 0
        while True:
            tick += 1
            # Randomly flip 3-6 slots per tick to simulate real facility arrivals/departures
            all_ids = list(slot_truth.keys())
            for sid in rng.sample(all_ids, k=rng.randint(3, 6)):
                slot_truth[sid] = not slot_truth[sid]

            for cam_id, cam_rois in pipeline.rois_by_camera.items():
                # Synthesize YOLO-like bounding boxes for occupied slots
                boxes: list[DetectionBox] = []
                for roi in cam_rois:
                    if slot_truth[roi.slot_id]:
                        x1 = float(roi.polygon[:, 0].min()) + rng.uniform(2, 10)
                        y1 = float(roi.polygon[:, 1].min()) + rng.uniform(2, 8)
                        x2 = float(roi.polygon[:, 0].max()) - rng.uniform(2, 10)
                        y2 = float(roi.polygon[:, 1].max()) - rng.uniform(2, 8)
                        boxes.append(
                            DetectionBox(
                                x1=x1,
                                y1=y1,
                                x2=x2,
                                y2=y2,
                                confidence=round(rng.uniform(0.84, 0.99), 3),
                                class_name=rng.choice(vehicles),
                            )
                        )

                results, inf_ms = pipeline.process_frame(cam_id, blank_frame, detections=boxes)
                payload = {
                    "camera_id": cam_id,
                    "fps": 15.0,
                    "inference_ms": inf_ms,
                    "observations": [
                        {
                            "slot_id": r.slot_id,
                            "occupied": r.occupied,
                            "confidence": r.confidence,
                            "vehicle_class": r.vehicle_class,
                        }
                        for r in results
                    ],
                }
                try:
                    client.post(f"{api_url.rstrip('/')}/api/v1/ingest/camera", json=payload)
                except httpx.HTTPError as exc:
                    print(f"[tick {tick}] Backend unreachable ({exc}); retrying...")
                    break

            occ_total = sum(1 for v in slot_truth.values() if v)
            print(f"[tick {tick}] Streamed 12 cameras | truth occupied={occ_total}/300")
            time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="12-camera 300-slot CV simulator")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--rois", type=Path, default=PROJECT_ROOT / "config" / "rois.json")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--initial-occupancy", type=float, default=0.45)
    args = parser.parse_args()
    run_simulator(args.api_url, args.rois, args.interval, args.initial_occupancy)


if __name__ == "__main__":
    main()
