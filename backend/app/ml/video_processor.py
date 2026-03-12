"""Video deepfake detection by sampling frames and aggregating per-frame predictions."""
import logging
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from app.ml.image_processor import ImageProcessor, _detect_artifacts, _weighted_average
from app.ml.model_loader import model_loader
from app.ml.preprocessor import image_preprocessor

logger = logging.getLogger(__name__)

_MIN_FRAMES = 1


class VideoProcessor:
    """Samples *sample_frames* evenly from a video and runs image-level inference on each."""

    def __init__(self) -> None:
        self._image_processor = ImageProcessor()

    def process_video(self, video_path: str, sample_frames: int = 10) -> dict:
        """
        Analyse *video_path* by sampling frames and aggregating predictions.

        Returns
        -------
        {
            "ai_probability":    float,
            "confidence_score":  float,
            "detection_methods": str,
            "model_scores":      dict[str, float],
            "frame_results":     list[dict],
            "artifacts_found":   list[str],
            "processing_time_ms": int,
        }
        """
        t0 = time.perf_counter()

        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError(f"OpenCV could not open video: {video_path}")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames < _MIN_FRAMES:
                raise ValueError(f"Video too short: {total_frames} frames")

            # Clamp sample count to available frames
            n = min(sample_frames, total_frames)
            frame_indices = np.linspace(0, total_frames - 1, n, dtype=int).tolist()

            frame_results: list[dict] = []
            per_model_sums: dict[str, float] = {}
            per_model_counts: dict[str, int] = {}

            for frame_idx in frame_indices:
                frame_data = self._process_frame(cap, frame_idx)
                if frame_data is None:
                    continue

                frame_results.append({
                    "frame_num": frame_idx,
                    "ai_prob": frame_data["ai_probability"],
                    "confidence": frame_data["confidence_score"],
                })

                for model_id, prob in frame_data["model_scores"].items():
                    per_model_sums[model_id]   = per_model_sums.get(model_id, 0.0) + prob
                    per_model_counts[model_id] = per_model_counts.get(model_id, 0) + 1

        finally:
            cap.release()

        if not frame_results:
            raise RuntimeError("No frames could be processed from the video")

        # ── Aggregate ─────────────────────────────────────────────────────────
        avg_scores = {
            mid: round(per_model_sums[mid] / per_model_counts[mid], 4)
            for mid in per_model_sums
        }
        ai_probability, confidence_score = _weighted_average(avg_scores)

        # Conservative confidence: use the minimum across frames
        min_frame_confidence = min(f["confidence"] for f in frame_results)
        confidence_score = round(min(confidence_score, min_frame_confidence), 3)

        methods_str = ";".join(f"{mid}:{p:.4f}" for mid, p in avg_scores.items())

        # ── Video-specific artifact detection ─────────────────────────────────
        artifacts = _detect_artifacts(ai_probability, avg_scores)
        frame_probs = [f["ai_prob"] for f in frame_results]
        if len(frame_probs) > 1:
            std_dev = float(np.std(frame_probs))
            if std_dev > 0.25:
                artifacts.append("high_temporal_variance")

        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            "Video inference complete",
            extra={
                "path": video_path,
                "frames_processed": len(frame_results),
                "ai_probability": ai_probability,
                "ms": elapsed_ms,
            },
        )

        return {
            "ai_probability": ai_probability,
            "confidence_score": confidence_score,
            "detection_methods": methods_str,
            "model_scores": avg_scores,
            "frame_results": frame_results,
            "artifacts_found": artifacts,
            "processing_time_ms": elapsed_ms,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _process_frame(self, cap: cv2.VideoCapture, frame_idx: int) -> Optional[dict]:
        """Seek to *frame_idx*, read it, and run image-level inference."""
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, bgr_frame = cap.read()
        if not ret or bgr_frame is None:
            logger.warning("Could not read frame", extra={"frame_idx": frame_idx})
            return None

        try:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb)

            # Reuse image processor internals to avoid re-opening from disk
            from app.ml.image_processor import _infer, _weighted_average

            scores: dict[str, float] = {}

            efnet = model_loader.get_model("efficientnet_b4")
            if efnet is not None:
                tensor = image_preprocessor.preprocess_for_efficientnet(pil_image)
                scores["efficientnet_b4"] = _infer(efnet, tensor)

            xception = model_loader.get_model("xception")
            if xception is not None:
                tensor = image_preprocessor.preprocess_for_xception(pil_image)
                scores["xception"] = _infer(xception, tensor)

            if not scores:
                return None

            ai_probability, confidence_score = _weighted_average(scores)
            return {
                "ai_probability": ai_probability,
                "confidence_score": confidence_score,
                "model_scores": scores,
            }

        except Exception as exc:
            logger.warning(
                "Frame inference failed",
                extra={"frame_idx": frame_idx, "error": str(exc)},
            )
            return None


# Singleton
video_processor = VideoProcessor()
