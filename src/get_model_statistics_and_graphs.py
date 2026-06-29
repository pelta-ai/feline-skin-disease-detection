import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.classifiers import ClassifierFactory
from src.classifiers.base_classifier import BaseClassifier
from src.utils import constants

import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import ml_insights as mli
# Config
architectures = ["convnext_tiny", "efficientnet_b0", "efficientnet_v2_b0", "mobilenet_v2", "mobilenet_v3_small", "nasnet_mobile", "resnet50"]
approaches = ["frozen", "finetuned"]
seeds = range(1, 16)  # Seeds 1 through 15

for arch in architectures:
    for approach in approaches:
        all_cms, all_ps, all_rs, all_fs, all_eces_before, all_eces_after, all_y_true, all_y_prob, all_y_prob_cal = [], [], [], [], [], [], [], [], []
        
        print(f"\n--- Processing: {arch} ({approach}) ---")
        
        for seed in seeds:
            # Matches format: resnet50_finetuned_seed2.keras
            # Note: strip underscores from arch name if your filenames don't use them (e.g., resnet50)
            clean_arch = arch.replace("_", "") 
            filename = f"{clean_arch}_{approach}_seed_{seed}.keras"
            model_path = os.path.join(constants.TRAINED_MODELS_PATH, filename)
            
            if not os.path.exists(model_path):
                continue

            cnn = ClassifierFactory.create(arch)
            cnn.make_sub_datasets()
            result = cnn.calibrate_and_evaluate(model_path=model_path, show_plots=False)
            
            # Collect data
            all_cms.append(result['confusion_matrix'])
            all_ps.append(result['per_class_precision'])
            all_rs.append(result['per_class_recall'])
            all_fs.append(result['per_class_f1'])
            all_eces_before.append(result['expected_calibration_error_before_calibration'])
            all_eces_after.append(result['expected_calibration_error_after_calibration'])
            all_y_true.append(result['y_true'])
            all_y_prob.append(result['y_prob'])
            all_y_prob_cal.append(result['y_prob_cal'])

        if not all_cms:
            continue

        # 1. Aggregate
        mean_cm = np.mean(all_cms, axis=0)
        avg_p, avg_r, avg_f1, avg_ece_before, avg_ece_after = np.mean(all_ps, axis=0), np.mean(all_rs, axis=0), np.mean(all_fs, axis=0), np.mean(all_eces_before), np.mean(all_eces_after)
        yt = np.concatenate(all_y_true)
        yp = np.concatenate(all_y_prob)
        ypc = np.concatenate(all_y_prob_cal)
        correct = (yp.argmax(1) == BaseClassifier._to_int(yt)).astype(int)

        # 2. Metrics Table
        summary_df = pd.DataFrame({
            'Class': cnn.class_names,
            'Precision': avg_p, 'Recall': avg_r, 'F1-Score': avg_f1,
            'Expected Calibration Error Before Calibration': avg_ece_before,
            'Expected Calibration Error After Calibration': avg_ece_after,
        })
        print(summary_df.to_string(index=False))

        # 3. Display Graphs
        cm_title = (f'Overall CM: {arch} - {approach}\n(Mean of {len(all_cms)} seeds)')
        BaseClassifier.display_confusion_matrix(cm=mean_cm, class_names=cnn.class_names, title=cm_title)

        avg_rd_before_calib = mli.plot_reliability_diagram(correct, yp.max(1), show_histogram=True)
        rd_before_calib_title = (f'Overall RD Before Calibration: {arch} - {approach}\n(Pool of {len(all_eces_before)} seeds)')
        BaseClassifier.display_reliability_diagram(avg_rd_before_calib, rd_before_calib_title)

        avg_rd_after_calib = mli.plot_reliability_diagram(correct, ypc.max(1), show_histogram=True)
        rd_after_calib_title = (f'Overall RD After Calibration: {arch} - {approach}\n(Pool of {len(all_eces_after)} seeds)')
        BaseClassifier.display_reliability_diagram(avg_rd_after_calib, rd_after_calib_title)