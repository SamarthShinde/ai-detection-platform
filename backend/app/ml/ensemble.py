"""Detection ensemble — orchestrates multiple models and fuses their predictions."""
import logging
from dataclasses import dataclass, field

from app.ml.model_registry import ENSEMBLE_MODELS

logger = logging.getLogger(__name__)


@dataclass
class EnsembleResult:
    """Result returned by DetectionEnsemble.predict()."""

    ai_probability: float
    confidence_score: float
    detection_methods: str          # "model_id:prob;model_id:prob"
    model_scores: dict[str, float] = field(default_factory=dict)
    artifacts_found: list[str] = field(default_factory=list)
    processing_time_ms: int = 0


class DetectionEnsemble:
    """Weighted voting ensemble over EfficientNet-B4 and Xception."""

    def __init__(self) -> None:
        self._models_config = ENSEMBLE_MODELS

    # ── Public API ────────────────────────────────────────────────────────────

    def predict_image(self, image_path: str) -> EnsembleResult:
        """Run real inference on a single image file."""
        from app.ml.image_processor import image_processor

        result = image_processor.process_image(image_path)
        return EnsembleResult(
            ai_probability=result["ai_probability"],
            confidence_score=result["confidence_score"],
            detection_methods=result["detection_methods"],
            model_scores=result["model_scores"],
            artifacts_found=result["artifacts_found"],
            processing_time_ms=result["processing_time_ms"],
        )

    def predict_video(self, video_path: str, max_frames: int = 10) -> EnsembleResult:
        """Run real inference on a video by sampling frames."""
        from app.ml.video_processor import video_processor

        result = video_processor.process_video(video_path, sample_frames=max_frames)
        return EnsembleResult(
            ai_probability=result["ai_probability"],
            confidence_score=result["confidence_score"],
            detection_methods=result["detection_methods"],
            model_scores=result["model_scores"],
            artifacts_found=result["artifacts_found"],
            processing_time_ms=result["processing_time_ms"],
        )

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

    def _weighted_average(self, scores: dict[str, float]) -> tuple[float, float]:
        """Return (ai_probability, confidence_score) from per-model scores."""
        total_weight = sum(
            m.ensemble_weight for m in self._models_config if m.model_id in scores
        )
        if total_weight == 0:
            return 0.5, 0.0

        weighted_sum = sum(
            scores[m.model_id] * m.ensemble_weight
            for m in self._models_config
            if m.model_id in scores
        )
        ai_probability = round(weighted_sum / total_weight, 4)

        values = list(scores.values())
        if len(values) > 1:
            mean = ai_probability
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = variance ** 0.5
            confidence = round(max(0.0, 1.0 - std_dev * 2), 3)
        else:
            confidence = 0.9

        return ai_probability, confidence


# ── Global singleton ─────────────────────────────────────────────────────────
detection_ensemble = DetectionEnsemble()
