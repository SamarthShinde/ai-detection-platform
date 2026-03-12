"""Image preprocessing utilities — converts PIL images to model-ready tensors."""
import logging

import torch
import torchvision.transforms as T
from PIL import Image

from app.ml.model_loader import DEVICE

logger = logging.getLogger(__name__)

_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]


def _build_transform(size: int) -> T.Compose:
    return T.Compose([
        T.Resize((size, size)),
        T.ToTensor(),                               # (C, H, W), values in [0, 1]
        T.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
    ])


# Pre-built transforms (avoid rebuilding on every call)
_TRANSFORM_380 = _build_transform(380)   # EfficientNet-B4
_TRANSFORM_299 = _build_transform(299)   # Xception


class ImagePreprocessor:
    """Converts PIL images into normalised tensors for each model architecture."""

    def preprocess_for_efficientnet(self, image: Image.Image) -> torch.Tensor:
        """Return a (1, 3, 380, 380) tensor ready for EfficientNet-B4."""
        rgb = image.convert("RGB")
        tensor = _TRANSFORM_380(rgb).unsqueeze(0)   # add batch dim
        return tensor.to(DEVICE)

    def preprocess_for_xception(self, image: Image.Image) -> torch.Tensor:
        """Return a (1, 3, 299, 299) tensor ready for Xception."""
        rgb = image.convert("RGB")
        tensor = _TRANSFORM_299(rgb).unsqueeze(0)
        return tensor.to(DEVICE)

    @staticmethod
    def postprocess_prediction(model_output: torch.Tensor) -> float:
        """
        Apply sigmoid to raw logits and return a probability in [0, 1].

        The models are loaded with num_classes=1 so output shape is (batch, 1).
        """
        prob = torch.sigmoid(model_output).squeeze().item()
        return float(prob)


# Singleton
image_preprocessor = ImagePreprocessor()
