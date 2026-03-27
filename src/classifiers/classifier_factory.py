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
        "mobilenet_v2": MobileNetV2Classifier,
        "mobilenet_v3_small": MobileNetV3SmallClassifier,
        "resnet50": ResNet50Classifier,
        "efficientnet_b0": EfficientNetB0Classifier,
        "efficientnet_v2_b0": EfficientNetV2B0Classifier,
        "nasnet_mobile": NASNetMobileClassifier,
        "convnext_tiny": ConvNeXtTinyClassifier,
    }

    @classmethod
    def create(cls, backbone_name: str, **kwargs):
        if backbone_name not in cls._registry:
            available = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unknown backbone '{backbone_name}'. Available: {available}"
            )
        return cls._registry[backbone_name](**kwargs)

    @classmethod
    def register(cls, name: str, classifier_cls):
        cls._registry[name] = classifier_cls

    @classmethod
    def available(cls):
        return list(cls._registry.keys())
