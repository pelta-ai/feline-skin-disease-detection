import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

df = pd.read_csv("group_ids.csv")
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

for fold_idx, (train_idx, test_idx) in enumerate(sgkf.split(df, df["label"], df["group_id"])):
    outer_train = df.iloc[train_idx]
    test_df = df.iloc[test_idx]

    sgkf2 = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=42)
    tr_i, va_i = next(sgkf2.split(outer_train, outer_train["label"], outer_train["group_id"]))
    train_df = outer_train.iloc[tr_i]
    val_df = outer_train.iloc[va_i]

    g_tr = set(train_df["group_id"])
    g_va = set(val_df["group_id"])
    g_te = set(test_df["group_id"])
    assert not (g_tr & g_te)
    assert not (g_va & g_te)
    assert not (g_tr & g_va)

    print(f"Fold {fold_idx}: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    print(f"  groups: train={len(g_tr)}, val={len(g_va)}, test={len(g_te)}")
    print(f"  val classes: {val_df['label'].value_counts().to_dict()}")