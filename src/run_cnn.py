import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.classifiers import ClassifierFactory
from src.utils import constants

import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# Config
architectures = ["new_mobilenetv2"]
approaches = ["frozen"]
seeds = range(1, 6)  # Seeds 1 through 15

for arch in architectures:
    for approach in approaches:
        all_cms, all_ps, all_rs, all_fs = [], [], [], []
        
        print(f"\n--- Processing: {arch} ({approach}) ---")
        
        for seed in seeds:
            # Matches format: resnet50_finetuned_seed2.keras
            # Note: strip underscores from arch name if your filenames don't use them (e.g., resnet50)
            clean_arch = arch.replace("_", "") 
            filename = f"{arch}_{approach}_seed_{seed}.keras"
            model_path = os.path.join(constants.TRAINED_MODELS_PATH, filename)
            
            if not os.path.exists(model_path):
                continue

            cnn = ClassifierFactory.create("resnet50")
            cnn.make_sub_datasets()
            result = cnn.evaluate(model_path=model_path, display_confusion_matrix=False)
            
            # Collect data
            all_cms.append(result['confusion_matrix'])
            all_ps.append(result['per_class_precision'])
            all_rs.append(result['per_class_recall'])
            all_fs.append(result['per_class_f1'])

        if not all_cms:
            continue

        # 1. Aggregate
        mean_cm = np.mean(all_cms, axis=0)
        avg_p, avg_r, avg_f1 = np.mean(all_ps, axis=0), np.mean(all_rs, axis=0), np.mean(all_fs, axis=0)

        # 2. Metrics Table
        summary_df = pd.DataFrame({
            'Class': cnn.class_names,
            'Precision': avg_p, 'Recall': avg_r, 'F1-Score': avg_f1
        })
        print(summary_df.to_string(index=False))

        # 3. Heatmap
        plt.figure(figsize=(8, 6))
        sns.heatmap(mean_cm, annot=True, fmt='.1f', cmap='Blues', 
                    xticklabels=cnn.class_names, yticklabels=cnn.class_names)
        plt.title(f'Overall CM: {arch} - {approach}\n(Mean of {len(all_cms)} seeds)')
        plt.tight_layout()
        plt.savefig(f"{arch}_{approach}_overall_cm.png")
        plt.show()
