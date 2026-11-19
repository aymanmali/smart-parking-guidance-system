"""Hybrid YOLO + OpenCV ROI + PyTorch CNN parking slot occupancy pipeline."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from cv_engine.roi_matcher import (
    DetectionBox,
    SlotROI,
    SlotTemporalFilter,
    compute_box_polygon_overlap,
)
from cv_engine.slot_classifier import ROISlotClassifier

# COCO vehicle class IDs in YOLOv8/YOLOv11
VEHICLE_CLASS_MAP: dict[int, str] = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


@dataclass
class SlotInferenceResult:
    slot_id: str
    occupied: bool
    confidence: float
    vehicle_class: str | None
    overlap_ratio: float


class ParkingVisionPipeline:
    """Monitors all slots visible to a camera using YOLO + ROI polygons + temporal smoothing."""

    def __init__(
        self,
        rois_path: Path,
        yolo_model_name: str | None = None,
        overlap_threshold: float = 0.30,
        confirm_frames: int = 3,
        use_cnn_refinement: bool = False,
        cnn_weights_path: Path | None = None,
    ) -> None:
        self.rois_by_camera = self._load_rois(rois_path)
        self.overlap_threshold = overlap_threshold
        self.temporal_filter = SlotTemporalFilter(confirm_frames=confirm_frames)
        self.yolo_model = None
        self.cnn_classifier = (
            ROISlotClassifier(weights_path=cnn_weights_path) if use_cnn_refinement else None
        )

        if yolo_model_name:
            from ultralytics import YOLO

            self.yolo_model = YOLO(yolo_model_name)

    @staticmethod
    def _load_rois(rois_path: Path) -> dict[str, list[SlotROI]]:
        raw = json.loads(rois_path.read_text(encoding="utf-8"))
        out: dict[str, list[SlotROI]] = {}
        for cam_id, cam_data in raw.items():
            out[cam_id] = [
                SlotROI(
                    slot_id=entry["slot_id"],
                    polygon=np.array(entry["polygon"], dtype=np.int32),
                )
                for entry in cam_data["slots"]
            ]
        return out

    def detect_vehicles(self, frame: np.ndarray, conf: float = 0.25) -> list[DetectionBox]:
        """Run YOLO inference on a BGR frame and return filtered vehicle bounding boxes."""
        if self.yolo_model is None:
            return []

        results = self.yolo_model.predict(
            source=frame,
            conf=conf,
            classes=list(VEHICLE_CLASS_MAP.keys()),
            verbose=False,
        )
        boxes: list[DetectionBox] = []
        for res in results:
            if res.boxes is None:
                continue
            for b in res.boxes:
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                cls_id = int(b.cls[0].item())
                score = float(b.conf[0].item())
                boxes.append(
                    DetectionBox(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=score,
                        class_name=VEHICLE_CLASS_MAP.get(cls_id, "car"),
                    )
                )
        return boxes

    def process_frame(
        self,
        camera_id: str,
        frame: np.ndarray,
        detections: list[DetectionBox] | None = None,
    ) -> tuple[list[SlotInferenceResult], float]:
        """Classify all ROIs for `camera_id` on `frame`. Returns (results, inference_ms)."""
        t0 = time.perf_counter()
        slot_rois = self.rois_by_camera.get(camera_id, [])
        if detections is None:
            detections = self.detect_vehicles(frame)

        frame_shape = (frame.shape[0], frame.shape[1])
        results: list[SlotInferenceResult] = []

        for roi in slot_rois:
            best_overlap = 0.0
            best_box: DetectionBox | None = None
            for box in detections:
                overlap = compute_box_polygon_overlap(box, roi.polygon, frame_shape=frame_shape)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_box = box

            raw_occupied = best_overlap >= self.overlap_threshold
            confidence = best_box.confidence if (raw_occupied and best_box) else (1.0 - best_overlap)

            # Optional PyTorch CNN refinement on ambiguous overlaps
            if (
                self.cnn_classifier is not None
                and self.cnn_classifier.weights_loaded
                and 0.15 <= best_overlap < 0.45
            ):
                cnn_prob = self.cnn_classifier.predict_occupied_prob(frame, roi.polygon)
                raw_occupied = cnn_prob >= 0.5
                confidence = cnn_prob if raw_occupied else (1.0 - cnn_prob)

            committed = self.temporal_filter.update(roi.slot_id, raw_occupied)
            results.append(
                SlotInferenceResult(
                    slot_id=roi.slot_id,
                    occupied=committed,
                    confidence=round(min(max(confidence, 0.0), 1.0), 3),
                    vehicle_class=(best_box.class_name if (committed and best_box) else None),
                    overlap_ratio=round(best_overlap, 3),
                )
            )

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return results, elapsed_ms

    def annotate_frame(
        self,
        camera_id: str,
        frame: np.ndarray,
        results: list[SlotInferenceResult],
        detections: list[DetectionBox] | None = None,
    ) -> np.ndarray:
        """Render slot ROI overlays (green=free, red=occupied) and vehicle boxes."""
        canvas = frame.copy()
        res_map = {r.slot_id: r for r in results}

        for roi in self.rois_by_camera.get(camera_id, []):
            r = res_map.get(roi.slot_id)
            occupied = r.occupied if r else False
            color = (48, 59, 255) if occupied else (80, 220, 100)  # BGR red / green
            cv2.polylines(canvas, [roi.polygon], isClosed=True, color=color, thickness=2)
            cx = int(roi.polygon[:, 0].mean())
            cy = int(roi.polygon[:, 1].mean())
            cv2.putText(
                canvas,
                roi.slot_id,
                (cx - 24, cy + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                color,
                1,
                cv2.LINE_AA,
            )

        if detections:
            for box in detections:
                cv2.rectangle(
                    canvas,
                    (int(box.x1), int(box.y1)),
                    (int(box.x2), int(box.y2)),
                    (255, 200, 0),
                    2,
                )
        return canvas
