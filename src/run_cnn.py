import numpy as np

from src.classifiers.classifier_factory import ClassifierFactory

seeds = [1, 2, 3, 4, 5]
all_results = []

cnn = ClassifierFactory.create("mobilenet_v2")
cnn.make_sub_datasets()

for s in seeds:
    save_name = f"mobilenetv2_frozen_seed_{s}.keras"

    model = cnn.train_one_run(
        seed=s,
        save_name=save_name,
        epochs=10,
        trainable_backbone=False,   # frozen feature extraction
        learning_rate=1e-3
    )

    result = cnn.evaluate(model=model)
    result["seed"] = s
    result["save_name"] = save_name
    all_results.append(result)

accs = np.array([r["accuracy"] for r in all_results])
f1s = np.array([r["macro_f1"] for r in all_results])

summary = {
    "accuracy_mean": float(accs.mean()),
    "accuracy_std": float(accs.std(ddof=1)) if len(accs) > 1 else 0.0,
    "macro_f1_mean": float(f1s.mean()),
    "macro_f1_std": float(f1s.std(ddof=1)) if len(f1s) > 1 else 0.0,
}

print("Summary:", summary)
