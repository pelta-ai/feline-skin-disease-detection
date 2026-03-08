"""Factory for creating classifier instances by backbone name."""

from .mobile_net_v2_classifier import MobileNetV2Classifier


class ClassifierFactory:
    _registry = {
        "mobilenet_v2": MobileNetV2Classifier,
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
