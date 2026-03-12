"""Image-level deepfake detection using the ensemble models."""
import logging
import time
from pathlib import Path

import torch
from PIL import Image, UnidentifiedImageError

from app.ml.model_loader import DEVICE, model_loader
from app.ml.preprocessor import image_preprocessor

logger = logging.getLogger(__name__)

# Artifact heuristics based on ensemble probability
_ARTIFACT_THRESHOLD_HIGH = 0.80
_ARTIFACT_THRESHOLD_MED  = 0.50


def _infer(model: torch.nn.Module, tensor: torch.Tensor) -> float:
    """Run a single forward pass and return a sigmoid probability."""
    try:
        with torch.no_grad():
            output = model(tensor)
        return image_preprocessor.postprocess_prediction(output)
    except RuntimeError:
        # MPS may not support every op — fall back to CPU for this call
        logger.warning("MPS forward failed, retrying on CPU")
        cpu_model  = model.cpu()
        cpu_tensor = tensor.cpu()
        with torch.no_grad():
            output = cpu_model(cpu_tensor)
        prob = image_preprocessor.postprocess_prediction(output)
        # Return model to original device
        model.to(DEVICE)
        return prob


class ImageProcessor:
    """Runs EfficientNet-B4 and Xception over a single image and fuses results."""

    def process_image(self, image_path: str) -> dict:
        """
        Analyse *image_path* and return a detection result dict.

        Returns
        -------
        {
            "ai_probability":    float,          # 0-1 (higher = more likely AI)
            "confidence_score":  float,          # 0-1 (model agreement)
            "detection_methods": str,            # "efnet:0.xx;xception:0.xx"
            "model_scores":      dict[str,float],
            "artifacts_found":   list[str],
            "processing_time_ms": int,
        }
        """
        t0 = time.perf_counter()

        # ── Load image ────────────────────────────────────────────────────────
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            pil_image = Image.open(path)
            pil_image.load()            # force decode so we catch corrupt files early
        except (UnidentifiedImageError, OSError) as exc:
            logger.error("Could not open image", extra={"path": image_path, "error": str(exc)})
            raise

        # ── EfficientNet-B4 ───────────────────────────────────────────────────
        scores: dict[str, float] = {}

        efnet = model_loader.get_model("efficientnet_b4")
        if efnet is not None:
            tensor = image_preprocessor.preprocess_for_efficientnet(pil_image)
            scores["efficientnet_b4"] = _infer(efnet, tensor)

        # ── Xception ──────────────────────────────────────────────────────────
        xception = model_loader.get_model("xception")
        if xception is not None:
            tensor = image_preprocessor.preprocess_for_xception(pil_image)
            scores["xception"] = _infer(xception, tensor)

        if not scores:
            raise RuntimeError("No models available for inference")

        # ── Fuse ──────────────────────────────────────────────────────────────
        ai_probability, confidence_score = _weighted_average(scores)

        # ── Artifact heuristics ───────────────────────────────────────────────
        artifacts = _detect_artifacts(ai_probability, scores)

        methods_str = ";".join(f"{mid}:{p:.4f}" for mid, p in scores.items())
        elapsed_ms = round((time.perf_counter() - t0) * 1000)

        logger.info(
            "Image inference complete",
            extra={"path": image_path, "ai_probability": ai_probability, "ms": elapsed_ms},
        )

        return {
            "ai_probability": ai_probability,
            "confidence_score": confidence_score,
            "detection_methods": methods_str,
            "model_scores": scores,
            "artifacts_found": artifacts,
            "processing_time_ms": elapsed_ms,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _weighted_average(scores: dict[str, float]) -> tuple[float, float]:
    """Weighted average of model scores; confidence based on inter-model agreement."""
    from app.ml.model_registry import MODELS

    total_weight = 0.0
    weighted_sum = 0.0
    for model_id, prob in scores.items():
        w = MODELS[model_id].ensemble_weight if model_id in MODELS else 1.0
        weighted_sum += prob * w
        total_weight  += w

    ai_probability = round(weighted_sum / total_weight, 4) if total_weight else 0.5

    if len(scores) > 1:
        values = list(scores.values())
        mean = ai_probability
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        confidence = round(max(0.0, 1.0 - std_dev * 2), 3)
    else:
        confidence = 0.9

    return ai_probability, confidence


def _detect_artifacts(ai_probability: float, scores: dict[str, float]) -> list[str]:
    """Return a list of descriptive artifact labels based on probability thresholds."""
    artifacts: list[str] = []
    if ai_probability >= _ARTIFACT_THRESHOLD_HIGH:
        artifacts.append("potential_deepfake")
    if ai_probability >= _ARTIFACT_THRESHOLD_MED:
        artifacts.append("synthetic_texture_detected")
    # High inter-model disagreement
    if len(scores) > 1:
        values = list(scores.values())
        spread = max(values) - min(values)
        if spread > 0.3:
            artifacts.append("model_disagreement")
    return artifacts


# Singleton
image_processor = ImageProcessor()
