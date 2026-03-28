import os

from src.classifiers import ClassifierFactory
from src.utils import constants

models = [
    ("convnext_tiny", "convnexttiny_finetuned_seed_1.keras"),
    ("efficientnet_b0", "efficientnetb0_finetuned_seed_1.keras"),
    ("efficientnet_v2_b0", "efficientnetv2b0_finetuned_seed_3.keras"),
    ("mobilenet_v2", "mobilenetv2_finetuned_seed_2.keras"),
    ("mobilenet_v3_small", "mobilenetv3small_finetuned_seed_3.keras"),
    ("nasnet_mobile", "nasnetmobile_finetuned_seed_5.keras"),
    ("resnet50", "resnet50_finetuned_seed_5.keras"),
]

for backbone, filename in models:
    model_path = os.path.join(constants.TRAINED_MODELS_PATH, filename)
    cnn = ClassifierFactory.create(backbone)
    cnn.make_sub_datasets()
    result = cnn.evaluate(model_path=model_path, display_confusion_matrix=True)
    print(f"\n=== {backbone} ===")
    print(result)