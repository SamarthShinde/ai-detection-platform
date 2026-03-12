"""Detection ensemble — orchestrates multiple models and fuses their predictions.

Day 8: Stub implementation returns placeholder predictions.
Day 9-10: Real image/video preprocessing and model inference replace the stubs.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from app.ml.model_registry import ENSEMBLE_MODELS

logger = logging.getLogger(__name__)


@dataclass
class EnsembleResult:
    """Result returned by DetectionEnsemble.predict()."""

    # Weighted average probability that the media is AI-generated (0–1)
    ai_probability: float

    # How confident the ensemble is in its prediction (0–1)
    confidence_score: float

    # Semicolon-separated list of "model_id:probability" contributions
    detection_methods: str

    # Per-model breakdown
    model_scores: dict[str, float] = field(default_factory=dict)

    # Detected artifact descriptions (populated by processors in Day 10)
    artifacts_found: list[str] = field(default_factory=list)

    # Wall-clock time for the full ensemble run (ms)
    processing_time_ms: int = 0


class DetectionEnsemble:
    """
    Weighted voting ensemble over multiple deepfake detection models.

    Current state (Day 8):
    - Stub: returns a placeholder prediction without real inference.
    - Real inference (Days 9-10): image/video preprocessing feeds actual
      PyTorch tensors into each model and the probabilities are fused.
    """

    def __init__(self) -> None:
        self._models_config = ENSEMBLE_MODELS

    # ── Public API ────────────────────────────────────────────────────────────

    def predict_image(self, image_path: str) -> EnsembleResult:
        """
        Run the ensemble on a single image file.

        Day 8 stub — returns placeholder result.
        Day 10 real: loads image → preprocesses per model → fuses predictions.
        """
        logger.info("Ensemble predict_image (stub)", extra={"path": image_path})
        return self._stub_result()

    def predict_video(self, video_path: str, max_frames: int = 20) -> EnsembleResult:
        """
        Run the ensemble on a video file by sampling frames.

        Day 8 stub — returns placeholder result.
        Day 10 real: extracts frames → runs face detection → processes each frame.
        """
        logger.info("Ensemble predict_video (stub)", extra={"path": video_path, "max_frames": max_frames})
        return self._stub_result()

    def get_model_info(self) -> list[dict]:
        """Return info about the configured ensemble models."""
        return [
            {
                "model_id": m.model_id,
                "description": m.description,
                "weight": m.ensemble_weight,
                "enabled": m.enabled,
            }
            for m in self._models_config
        ]

    # ── Internal (stub + future real impl) ────────────────────────────────────

    def _stub_result(self) -> EnsembleResult:
        """
        Placeholder result used before real ML inference is wired in (Day 9-10).
        Returns a deterministic low-probability 'not AI' prediction.
        """
        stub_scores = {m.model_id: 0.12 for m in self._models_config}
        methods = ";".join(f"{mid}:{score:.3f}" for mid, score in stub_scores.items())
        return EnsembleResult(
            ai_probability=0.12,
            confidence_score=0.91,
            detection_methods=f"stub_ensemble:{methods}",
            model_scores=stub_scores,
            artifacts_found=[],
            processing_time_ms=0,
        )

    def _weighted_average(self, scores: dict[str, float]) -> tuple[float, float]:
        """
        Compute weighted average probability and confidence from per-model scores.

        Returns (ai_probability, confidence_score).
        """
        total_weight = sum(m.ensemble_weight for m in self._models_config if m.model_id in scores)
        if total_weight == 0:
            return 0.5, 0.0

        weighted_sum = sum(
            scores[m.model_id] * m.ensemble_weight
            for m in self._models_config
            if m.model_id in scores
        )
        ai_probability = weighted_sum / total_weight

        # Confidence: how much models agree (1 - std dev of scores)
        values = list(scores.values())
        if len(values) > 1:
            mean = ai_probability
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5
            confidence = round(max(0.0, 1.0 - std_dev * 2), 3)
        else:
            confidence = 0.9

        return round(ai_probability, 4), confidence


# ── Global singleton ─────────────────────────────────────────────────────────
detection_ensemble = DetectionEnsemble()
