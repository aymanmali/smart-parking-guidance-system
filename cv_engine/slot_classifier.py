"""Lightweight PyTorch CNN classifier for cropped parking slot ROIs.

Used as a secondary refinement stage when YOLO bounding-box overlap with a slot
ROI is borderline (e.g., partial occlusion or steep camera angle).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn


class SlotOccupancyCNN(nn.Module):
    """Compact 3-block CNN classifying 64x64 RGB slot crops into [free, occupied]."""

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 32x32
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),  # 16x16
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(p=0.2),
            nn.Linear(64, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


class ROISlotClassifier:
    """Wrapper handling OpenCV crop extraction, normalization, and PyTorch inference."""

    def __init__(self, weights_path: Path | None = None, device: str | None = None) -> None:
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.model = SlotOccupancyCNN().to(self.device)
        self.weights_loaded = False

        if weights_path is not None and weights_path.exists():
            state = torch.load(weights_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state)
            self.weights_loaded = True

        self.model.eval()

    @staticmethod
    def crop_roi(frame: np.ndarray, polygon: np.ndarray, size: int = 64) -> np.ndarray:
        """Extract masked bounding-rect crop of a slot polygon resized to (size, size)."""
        h, w = frame.shape[:2]
        x1 = max(0, int(polygon[:, 0].min()))
        y1 = max(0, int(polygon[:, 1].min()))
        x2 = min(w, int(polygon[:, 0].max()))
        y2 = min(h, int(polygon[:, 1].max()))
        if x2 <= x1 or y2 <= y1:
            return np.zeros((size, size, 3), dtype=np.uint8)
        crop = frame[y1:y2, x1:x2]
        return cv2.resize(crop, (size, size), interpolation=cv2.INTER_AREA)

    @torch.inference_mode()
    def predict_occupied_prob(self, frame: np.ndarray, polygon: np.ndarray) -> float:
        """Return probability in [0, 1] that the cropped ROI is occupied."""
        crop = self.crop_roi(frame, polygon, size=64)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)
        return float(probs[0, 1].item())
