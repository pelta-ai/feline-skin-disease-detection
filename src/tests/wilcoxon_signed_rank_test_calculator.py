import pandas as pd, numpy as np
from scipy.stats import wilcoxon 
from statsmodels.stats.multitest import multipletests


pf = pd.read_csv("model_performances/per_fold_metrics.csv")

rows = []
for arch in sorted(pf.arch.unique()):
    fr = pf[(pf.arch == arch) & (pf.strategy == "frozen")].sort_values(["fold", "seed"]).reset_index(drop=True)
    ft = pf[(pf.arch == arch) & (pf.strategy == "finetuned")].sort_values(["fold", "seed"]).reset_index(drop=True)

    assert (fr.fold.values == ft.fold.values).all(), f"{arch}: folds misaligned"
    assert (fr.seed.values == ft.seed.values).all(), f"{arch}: seeds misaligned"

    diff = ft.accuracy.values - fr.accuracy.values
    W, p = wilcoxon(ft.accuracy.values, fr.accuracy.values, alternative="two-sided")
    rows.append(dict(arch=arch, n=len(diff), mean_delta=diff.mean(),
                     n_positive=int((diff > 0).sum()), W=W, p=p))

res = pd.DataFrame(rows)
reject, p_holm, _, _ = multipletests(res.p.values, alpha=0.05, method="holm")
res["p_holm"] = p_holm
res["significant"] = reject
print(res.to_string(index=False))