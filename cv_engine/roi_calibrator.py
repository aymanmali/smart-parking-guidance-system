#!/usr/bin/env python3
"""Interactive OpenCV ROI Polygon Calibrator.

Click 4 corners around each parking slot on a camera snapshot or RTSP frame to
export calibrated slot polygons to `config/rois.json`.

Usage:
    python -m cv_engine.roi_calibrator --camera CAM-01 --source frame.jpg --prefix A --start 1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def run_calibrator(camera_id: str, source: str, prefix: str, start_idx: int, output: Path) -> None:
    cap = cv2.VideoCapture(source)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read frame from {source}")

    h, w = frame.shape[:2]
    slots: list[dict] = []
    current_pts: list[list[int]] = []
    slot_num = start_idx

    def on_mouse(event: int, x: int, y: int, _flags: int, _param: object) -> None:
        nonlocal slot_num
        if event == cv2.EVENT_LBUTTONDOWN:
            current_pts.append([x, y])
            if len(current_pts) == 4:
                slot_id = f"{prefix}-{slot_num:03d}"
                slots.append({"slot_id": slot_id, "polygon": list(current_pts)})
                print(f"Saved {slot_id}: {current_pts}")
                current_pts.clear()
                slot_num += 1

    win = f"ROI Calibrator — {camera_id} (Click 4 corners/slot, 'u'=undo, 's'=save, 'q'=quit)"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)

    while True:
        display = frame.copy()
        for entry in slots:
            poly = np.array(entry["polygon"], dtype=np.int32)
            cv2.polylines(display, [poly], True, (0, 220, 0), 2)
            cx, cy = int(poly[:, 0].mean()), int(poly[:, 1].mean())
            cv2.putText(display, entry["slot_id"], (cx - 22, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 0), 1)
        for pt in current_pts:
            cv2.circle(display, tuple(pt), 4, (0, 180, 255), -1)

        cv2.imshow(win, display)
        key = cv2.waitKey(20) & 0xFF
        if key == ord("u"):
            if current_pts:
                current_pts.pop()
            elif slots:
                slots.pop()
                slot_num = max(start_idx, slot_num - 1)
        elif key == ord("s"):
            data = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {}
            data[camera_id] = {"resolution": [w, h], "slots": slots}
            output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote {len(slots)} ROIs for {camera_id} to {output}")
        elif key == ord("q"):
            break

    cv2.destroyAllWindows()


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive OpenCV parking slot ROI calibrator")
    parser.add_argument("--camera", required=True, help="Camera ID, e.g., CAM-01")
    parser.add_argument("--source", required=True, help="Image path, video file, or RTSP URL")
    parser.add_argument("--prefix", default="A", help="Zone code prefix (A, B, C, D)")
    parser.add_argument("--start", type=int, default=1, help="Starting slot number")
    parser.add_argument("--output", type=Path, default=Path("config/rois.json"))
    args = parser.parse_args()
    run_calibrator(args.camera, args.source, args.prefix, args.start, args.output)


if __name__ == "__main__":
    main()
