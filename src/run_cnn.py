import os

from src.classifiers import ClassifierFactory
from src.utils import constants

models = [
    ("convnext_tiny", "convnexttiny_frozen_seed_5.keras"),
    ("efficientnet_b0", "efficientnetb0_frozen_seed_3.keras"),
    ("efficientnet_v2_b0", "efficientnetv2b0_frozen_seed_4.keras"),
    ("mobilenet_v2", "mobilenetv2_frozen_seed_1.keras"),
    ("mobilenet_v3_small", "mobilenetv3small_frozen_seed_2.keras"),
    ("nasnet_mobile", "nasnetmobile_frozen_seed_1.keras"),
    ("resnet50", "resnet50_frozen_seed_4.keras"),
]

for backbone, filename in models:
    model_path = os.path.join(constants.TRAINED_MODELS_PATH, filename)
    cnn = ClassifierFactory.create(backbone)
    cnn.make_sub_datasets()
    result = cnn.evaluate(model_path=model_path, display_confusion_matrix=True)
    print(f"\n=== {backbone} ===")
    print(result)

# seeds = [1, 2, 3, 4, 5]
# all_results = []

# cnn = ClassifierFactory.create("mobilenet_v2")
# cnn.make_sub_datasets()

# for s in seeds:
#     save_name = f"mobilenetv2_frozen_seed_{s}.keras"

#     model = cnn.train_one_run(
#         seed=s,
#         save_name=save_name,
#         epochs=10,
#         trainable_backbone=False,   # frozen feature extraction
#         learning_rate=1e-3
#     )

#     result = cnn.evaluate(model=model)
#     result["seed"] = s
#     result["save_name"] = save_name
#     all_results.append(result)

# accs = np.array([r["accuracy"] for r in all_results])
# f1s = np.array([r["macro_f1"] for r in all_results])

# summary = {
#     "accuracy_mean": float(accs.mean()),
#     "accuracy_std": float(accs.std(ddof=1)) if len(accs) > 1 else 0.0,
#     "macro_f1_mean": float(f1s.mean()),
#     "macro_f1_std": float(f1s.std(ddof=1)) if len(f1s) > 1 else 0.0,
# }

# print("Summary:", summary)
