"""Factory for creating classifier instances by backbone name."""

from .mobile_net_v2_classifier import MobileNetV2Classifier
from .mobile_net_v3_small_classifier import MobileNetV3SmallClassifier
from .resnet_50_classifier import ResNet50Classifier
from .efficient_net_b0_classifier import EfficientNetB0Classifier
from .efficient_net_v2_b0_classifier import EfficientNetV2B0Classifier
from .nasnet_mobile_classifier import NASNetMobileClassifier
from .convnext_tiny_classifier import ConvNeXtTinyClassifier


class ClassifierFactory:
    _registry = {
        "mobilenetv2": MobileNetV2Classifier,
        "mobilenetv3small": MobileNetV3SmallClassifier,
        "resnet50": ResNet50Classifier,
        "efficientnetb0": EfficientNetB0Classifier,
        "efficientnetv2b0": EfficientNetV2B0Classifier,
        "nasnetmobile": NASNetMobileClassifier,
        "convnexttiny": ConvNeXtTinyClassifier,
    }

    @staticmethod
    def _normalize(name: str) -> str:
        """Allow underscore-separated names (e.g. 'mobilenet_v2') to resolve."""
        return name.replace("_", "").lower()

    @classmethod
    def create(cls, backbone_name: str, **kwargs):
        key = cls._normalize(backbone_name)
        if key not in cls._registry:
            available = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unknown backbone '{backbone_name}'. Available: {available}"
            )
        return cls._registry[key](**kwargs)

    @classmethod
    def register(cls, name: str, classifier_cls):
        cls._registry[name] = classifier_cls

    @classmethod
    def available(cls):
        return list(cls._registry.keys())
