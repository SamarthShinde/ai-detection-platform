"""Model registry — defines all available deepfake detection models and their configs."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ModelConfig:
    """Immutable configuration for a single detection model."""

    # Unique internal identifier
    model_id: str

    # timm model name (used to download weights automatically from HuggingFace)
    timm_name: str

    # Input image size expected by the model
    input_size: int

    # Whether this model is enabled in the ensemble
    enabled: bool

    # Weight in the weighted voting ensemble (higher = more trusted)
    ensemble_weight: float

    # Description for logging / docs
    description: str

    # Expected inference time on M1 CPU (ms), for health checks
    expected_ms: int = 200

    # Optional: local cache path override (None = use timm default cache)
    cache_path: Optional[str] = None


# ── Model definitions ─────────────────────────────────────────────────────────

MODELS: dict[str, ModelConfig] = {
    "efficientnet_b4": ModelConfig(
        model_id="efficientnet_b4",
        timm_name="efficientnet_b4",
        input_size=380,
        enabled=True,
        ensemble_weight=0.5,
        description="EfficientNet-B4 — general deepfake detection backbone",
        expected_ms=150,
    ),
    "xception": ModelConfig(
        model_id="xception",
        timm_name="xception",
        input_size=299,
        enabled=True,
        ensemble_weight=0.5,
        description="Xception — FaceForensics++ style deepfake detector",
        expected_ms=200,
    ),
}

# Default ensemble: all enabled models
ENSEMBLE_MODELS = [m for m in MODELS.values() if m.enabled]


def get_model(model_id: str) -> Optional[ModelConfig]:
    """Return ModelConfig for *model_id*, or None if not found."""
    return MODELS.get(model_id)


# Alias for scripts/tests that expect MODEL_REGISTRY
MODEL_REGISTRY = MODELS


def list_models() -> list[dict]:
    """Return a list of model info dicts (for health/status endpoints)."""
    return [
        {
            "model_id": m.model_id,
            "description": m.description,
            "input_size": m.input_size,
            "ensemble_weight": m.ensemble_weight,
            "enabled": m.enabled,
        }
        for m in MODELS.values()
    ]
