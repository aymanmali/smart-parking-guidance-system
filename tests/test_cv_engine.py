"""Tests for OpenCV ROI matcher, temporal hysteresis, PyTorch CNN, and CV pipeline."""

from pathlib import Path

import numpy as np

from cv_engine.detector import ParkingVisionPipeline
from cv_engine.roi_matcher import DetectionBox, SlotTemporalFilter, compute_box_polygon_overlap
from cv_engine.slot_classifier import ROISlotClassifier

ROIS_PATH = Path(__file__).resolve().parent.parent / "config" / "rois.json"


def test_box_polygon_overlap():
    poly = np.array([[100, 100], [200, 100], [200, 200], [100, 200]], dtype=np.int32)
    full_box = DetectionBox(95, 95, 205, 205, 0.95, "car")
    half_box = DetectionBox(150, 100, 200, 200, 0.90, "car")
    miss_box = DetectionBox(300, 300, 400, 400, 0.90, "car")

    assert compute_box_polygon_overlap(full_box, poly) > 0.98
    assert 0.45 <= compute_box_polygon_overlap(half_box, poly) <= 0.55
    assert compute_box_polygon_overlap(miss_box, poly) == 0.0


def test_temporal_hysteresis_prevents_flicker():
    tf = SlotTemporalFilter(confirm_frames=3)
    assert tf.update("A-001", False) is False
    # Transient car passing across slot for 2 frames should NOT flip committed state
    assert tf.update("A-001", True) is False
    assert tf.update("A-001", True) is False
    # 3rd consecutive frame commits occupied
    assert tf.update("A-001", True) is True
    # 1 dropped detection frame should NOT flicker back to free
    assert tf.update("A-001", False) is True


def test_pytorch_slot_classifier_forward():
    clf = ROISlotClassifier(weights_path=None, device="cpu")
    frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    poly = np.array([[100, 100], [220, 100], [220, 190], [100, 190]], dtype=np.int32)
    prob = clf.predict_occupied_prob(frame, poly)
    assert 0.0 <= prob <= 1.0


def test_vision_pipeline_cam01_and_annotation():
    pipeline = ParkingVisionPipeline(rois_path=ROIS_PATH, yolo_model_name=None, confirm_frames=1)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    cam01_first_roi = pipeline.rois_by_camera["CAM-01"][0]
    x1, y1 = float(cam01_first_roi.polygon[:, 0].min()), float(cam01_first_roi.polygon[:, 1].min())
    x2, y2 = float(cam01_first_roi.polygon[:, 0].max()), float(cam01_first_roi.polygon[:, 1].max())

    detections = [DetectionBox(x1, y1, x2, y2, 0.94, "car")]
    results, inf_ms = pipeline.process_frame("CAM-01", frame, detections=detections)

    assert len(results) == 25
    assert results[0].slot_id == "A-001"
    assert results[0].occupied is True
    assert results[1].occupied is False
    assert inf_ms >= 0.0

    annotated = pipeline.annotate_frame("CAM-01", frame, results, detections=detections)
    assert annotated.shape == frame.shape
