"""
Confusion-matrix analysis for the Results section.

Reads the per-architecture confusion matrices, sums them within each training
strategy, and reports:
  1. errors made and errors received per class, with percentages
  2. the full off-diagonal grid (which class gets mistaken for which)
  3. the largest confusion pairs, with their reverse direction
  4. what changes between strategies
  5. consistency checks

Run from the folder holding confusion_matrix_*.csv and per_class_metrics.csv.
"""

import glob
import numpy as np
import pandas as pd

CLASSES = ["demodicosis", "dermatitis", "flea_allergy", "fungus", "ringworm", "scabies"]
SHORT = {"demodicosis": "demo", "dermatitis": "derm", "flea_allergy": "flea",
         "fungus": "fung", "ringworm": "ring", "scabies": "scab"}
STRATEGIES = ["frozen", "finetuned"]

pd.set_option("display.width", 200)


def load_summed(strategy):
    """Sum the confusion matrices of every architecture under one strategy."""
    files = sorted(glob.glob(f"model_performances/confusion_matrix_*_{strategy}.csv"))
    if not files:
        raise FileNotFoundError(f"no confusion_matrix_*_{strategy}.csv found")
    total = None
    for f in files:
        m = pd.read_csv(f, index_col=0).reindex(index=CLASSES, columns=CLASSES)
        total = m.copy() if total is None else total + m
    return total, len(files)


def off_diagonal(total):
    """Same matrix with correct predictions zeroed out, so only errors remain."""
    off = total.values.copy()          # .copy() because read_csv gives a read-only view
    np.fill_diagonal(off, 0)
    return pd.DataFrame(off, index=CLASSES, columns=CLASSES)


results = {}

for strategy in STRATEGIES:
    total, n_arch = load_summed(strategy)
    off = off_diagonal(total)

    made = off.sum(axis=1)      # row sums: true class predicted as something else
    received = off.sum(axis=0)  # column sums: other classes predicted as this one
    support = total.sum(axis=1)

    results[strategy] = dict(total=total, off=off, made=made,
                             received=received, support=support, n_arch=n_arch)

    # ── 1. errors made and received ───────────────────────────────────────
    print("=" * 78)
    print(f"{strategy.upper()}  ({n_arch} architectures summed)")
    print("=" * 78)
    summary = pd.DataFrame({
        "support": support.round(0).astype(int),
        "made": made.round(0).astype(int),
        "% missed": (100 * made / support).round(1),
        "received": received.round(0).astype(int),
    }).sort_values("% missed")
    print(summary.to_string())
    print(f"\ntotal errors: {made.sum():.0f} of {support.sum():.0f} "
          f"({100 * made.sum() / support.sum():.1f}%)\n")

    # ── 2. full off-diagonal grid ─────────────────────────────────────────
    print("off-diagonal counts (rows = true class, columns = predicted class)")
    grid = off.round(0).astype(int)
    grid.index = [SHORT[c] for c in grid.index]
    grid.columns = [SHORT[c] for c in grid.columns]
    print(grid.to_string())
    print()

    # ── 3. largest confusion pairs, with the reverse direction ────────────
    pairs = sorted(
        ((off.loc[a, b], a, b) for a in CLASSES for b in CLASSES if a != b),
        reverse=True,
    )
    print("largest confusion pairs")
    for count, true_c, pred_c in pairs[:8]:
        reverse = off.loc[pred_c, true_c]
        pct = 100 * count / support[true_c]
        flag = "  (asymmetric)" if count > 1.5 * reverse else ""
        print(f"  true {true_c:13s} -> predicted {pred_c:13s} "
              f"{count:6.0f}  ({pct:4.1f}% of class)   reverse {reverse:5.0f}{flag}")
    print()

    # ── 5a. consistency check: rows must equal support ────────────────────
    row_ok = np.allclose(total.sum(axis=1), support)
    sum_ok = np.isclose(made.sum(), received.sum())
    print(f"check  rows sum to support: {row_ok}   "
          f"total made == total received: {sum_ok}\n")


# ── 4. what changes between strategies ────────────────────────────────────
print("=" * 78)
print("CHANGE FROM FROZEN TO FINE-TUNED")
print("=" * 78)

fr, ft = results["frozen"], results["finetuned"]

delta = pd.DataFrame({
    "made frozen": fr["made"].round(0).astype(int),
    "made finetuned": ft["made"].round(0).astype(int),
    "made delta": (ft["made"] - fr["made"]).round(0).astype(int),
    "recv frozen": fr["received"].round(0).astype(int),
    "recv finetuned": ft["received"].round(0).astype(int),
    "recv delta": (ft["received"] - fr["received"]).round(0).astype(int),
})
print(delta.to_string())
print()

cell_delta = (ft["off"] - fr["off"])
shifts = sorted(
    ((cell_delta.loc[a, b], a, b) for a in CLASSES for b in CLASSES if a != b),
    key=lambda x: -abs(x[0]),
)
print("largest per-cell shifts")
for d, true_c, pred_c in shifts[:6]:
    print(f"  true {true_c:13s} -> predicted {pred_c:13s} "
          f"{fr['off'].loc[true_c, pred_c]:6.0f} -> {ft['off'].loc[true_c, pred_c]:6.0f}  "
          f"({d:+.0f})")
print()

# ── 5b. cross-check % missed against recall from a separate file ──────────
try:
    pc = pd.read_csv("per_class_metrics.csv")
    print("=" * 78)
    print("CROSS-CHECK: % missed from confusion matrices vs (1 - recall)")
    print("=" * 78)
    for strategy in STRATEGIES:
        r = results[strategy]
        print(f"\n{strategy}")
        for c in CLASSES:
            from_cm = 100 * r["made"][c] / r["support"][c]
            recall = pc[(pc.strategy == strategy) & (pc["class"] == c)].recall_mean.mean()
            from_recall = 100 * (1 - recall)
            print(f"  {c:14s} {from_cm:6.2f}%  vs  {from_recall:6.2f}%   "
                  f"diff {from_cm - from_recall:+.3f}")
except FileNotFoundError:
    print("per_class_metrics.csv not found, skipping cross-check")