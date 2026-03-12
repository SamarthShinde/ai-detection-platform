"""Lazy-loading, in-memory model cache for all detection models.

Models are downloaded automatically by timm from HuggingFace on first load.
Subsequent calls return the cached instance (no re-download).
"""
import logging
import threading
import time
from typing import Optional

import torch
import torch.nn as nn

from app.ml.model_registry import ENSEMBLE_MODELS, ModelConfig, get_model

logger = logging.getLogger(__name__)


def _get_device() -> torch.device:
    """Return the best available PyTorch device (MPS on M1, then CUDA, then CPU)."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


DEVICE = _get_device()


class ModelLoader:
    """Thread-safe singleton that lazily loads and caches detection models."""

    def __init__(self) -> None:
        self._cache: dict[str, nn.Module] = {}
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_model(self, model_id: str) -> Optional[nn.Module]:
        """
        Return the loaded model for *model_id*, loading it if not yet cached.

        Returns None if the model_id is unknown.
        """
        config = get_model(model_id)
        if config is None:
            logger.warning("Unknown model_id requested", extra={"model_id": model_id})
            return None

        if model_id not in self._cache:
            with self._lock:
                # Double-check after acquiring lock
                if model_id not in self._cache:
                    self._load(config)

        return self._cache.get(model_id)

    def preload_all(self) -> dict[str, bool]:
        """
        Load all enabled ensemble models into the cache.

        Returns {model_id: success} dict.
        """
        results: dict[str, bool] = {}
        for config in ENSEMBLE_MODELS:
            try:
                self.get_model(config.model_id)
                results[config.model_id] = True
            except Exception as exc:
                logger.error(
                    "Failed to preload model",
                    extra={"model_id": config.model_id, "error": str(exc)},
                )
                results[config.model_id] = False
        return results

    def is_loaded(self, model_id: str) -> bool:
        """Return True if the model is already in the cache."""
        return model_id in self._cache

    def get_loaded_models(self) -> list[str]:
        """Return model_ids of all currently loaded models."""
        return list(self._cache.keys())

    def get_device(self) -> str:
        """Return the active device string."""
        return str(DEVICE)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self, config: ModelConfig) -> None:
        """Download (if needed) and load a timm model into eval mode on DEVICE."""
        import timm

        logger.info(
            "Loading model",
            extra={"model_id": config.model_id, "timm_name": config.timm_name, "device": str(DEVICE)},
        )
        t0 = time.perf_counter()

        try:
            # pretrained=True triggers automatic download to ~/.cache/huggingface/hub/
            model: nn.Module = timm.create_model(config.timm_name, pretrained=True, num_classes=1)
            model = model.to(DEVICE)
            model.eval()

            elapsed_ms = round((time.perf_counter() - t0) * 1000)
            self._cache[config.model_id] = model
            logger.info(
                "Model loaded",
                extra={"model_id": config.model_id, "device": str(DEVICE), "load_ms": elapsed_ms},
            )
        except Exception as exc:
            logger.error(
                "Model load failed",
                extra={"model_id": config.model_id, "error": str(exc)},
            )
            raise


# ── Global singleton ─────────────────────────────────────────────────────────
model_loader = ModelLoader()
