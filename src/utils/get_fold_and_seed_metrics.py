"""Print the per-seed / per-fold accuracy breakdown for each (arch, strategy) run.

For every architecture + strategy there are 3 seeds x 5 folds = 15 accuracies.
This prints that 5x3 grid plus its margins:
  - per-seed  = mean over the 5 folds of one seed (SD across those folds)
  - per-fold  = mean over the 3 seeds of one fold (SD across those seeds)

Note: folds hold different numbers of images, so the unweighted per-seed mean is
not identical to the pooled seed accuracy in per_run_metrics.csv. Both are shown.
"""

import pandas as pd

METRICS_CSV = "model_performances/per_fold_metrics.csv"

architectures = [
    "convnext_tiny",
    "efficientnet_b0",
    "efficientnet_v2_b0",
    "mobilenet_v2",
    "mobilenet_v3_small",
    "nasnet_mobile",
    "resnet_50",
]
strategies = ["frozen", "finetuned"]

per_fold_metrics_df = pd.read_csv(METRICS_CSV)


def get_grid(df, arch, strategy, metric="accuracy"):
    """Return a folds x seeds table of `metric` for one arch/strategy."""
    rows = df.loc[(df["arch"] == arch) & (df["strategy"] == strategy)]
    return rows.pivot(index="fold", columns="seed", values=metric)


def fold_weights(df, arch, strategy):
    """n_images per fold, used for the pooled (image-weighted) seed accuracy."""
    rows = df.loc[(df["arch"] == arch) & (df["strategy"] == strategy)]
    return rows.groupby("fold")["n_images"].first()


def print_block(df, arch, strategy, metric="accuracy"):
    grid = get_grid(df, arch, strategy, metric)
    weights = fold_weights(df, arch, strategy)

    seeds = list(grid.columns)
    folds = list(grid.index)

    per_seed_mean = grid.mean(axis=0)          # over folds
    per_seed_sd = grid.std(axis=0, ddof=1)     # across folds, within a seed
    per_seed_pooled = grid.mul(weights, axis=0).sum(axis=0) / weights.sum()

    per_fold_mean = grid.mean(axis=1)          # over seeds
    per_fold_sd = grid.std(axis=1, ddof=1)     # across seeds, within a fold

    print(f"\n{'=' * 78}")
    print(f"{arch}  |  {strategy}  |  {metric}")
    print("=" * 78)

    header = "fold  n_img  " + "".join(f"seed {s:<7}" for s in seeds) + "  mean     sd"
    print(header)
    print("-" * len(header))
    for fold in folds:
        cells = "".join(f"{grid.loc[fold, s]:<12.4f}" for s in seeds)
        print(
            f"{fold:<6}{weights[fold]:<7}{cells}  "
            f"{per_fold_mean[fold]:.4f}   {per_fold_sd[fold]:.4f}"
        )
    print("-" * len(header))

    print("mean         " + "".join(f"{per_seed_mean[s]:<12.4f}" for s in seeds)
          + f"  {per_fold_mean.mean():.4f}   {per_fold_sd.mean():.4f}  <- mean of per-fold sds")
    print("sd           " + "".join(f"{per_seed_sd[s]:<12.4f}" for s in seeds)
          + f"  {per_seed_sd.mean():.4f}")
    print("             " + " " * (12 * len(seeds)) + "  ^ mean of per-seed sds")
    print("pooled       " + "".join(f"{per_seed_pooled[s]:<12.4f}" for s in seeds))

    print(
        f"\n  per-seed means : {[round(v, 4) for v in per_seed_mean]}"
        f"  -> mean {per_seed_mean.mean():.4f}, sd across seeds {per_seed_mean.std(ddof=1):.4f}"
    )
    print(
        f"  per-seed sds   : {[round(v, 4) for v in per_seed_sd]}"
        f"  -> mean {per_seed_sd.mean():.4f}   (avg fold-to-fold spread within a seed)"
    )
    print(
        f"  per-fold means : {[round(v, 4) for v in per_fold_mean]}"
        f"  -> mean {per_fold_mean.mean():.4f}, sd across folds {per_fold_mean.std(ddof=1):.4f}"
    )
    print(
        f"  per-fold sds   : {[round(v, 4) for v in per_fold_sd]}"
        f"  -> mean {per_fold_sd.mean():.4f}   (avg seed-to-seed spread within a fold)"
    )
    print(f"  all 15 runs    : mean {grid.values.mean():.4f}, "
          f"sd {pd.Series(grid.values.ravel()).std(ddof=1):.4f}")


def print_summary(df, metric="accuracy"):
    """One row per arch/strategy: overall mean and the two SD views."""
    print(f"\n{'=' * 78}")
    print(f"SUMMARY ({metric})")
    print("=" * 78)
    print("  mean sd/seed = avg over seeds of the sd across that seed's 5 folds")
    print("  mean sd/fold = avg over folds of the sd across that fold's 3 seeds\n")
    header = (
        f"{'arch':<20}{'strategy':<11}{'mean':<9}{'mean sd/seed':<14}"
        f"{'mean sd/fold':<14}{'sd(seed means)':<16}{'sd(fold means)':<16}{'sd(all 15)':<11}"
    )
    print(header)
    print("-" * len(header))
    for arch in architectures:
        for strategy in strategies:
            grid = get_grid(df, arch, strategy, metric)
            seed_means = grid.mean(axis=0)
            fold_means = grid.mean(axis=1)
            seed_sds = grid.std(axis=0, ddof=1)   # each seed, across its folds
            fold_sds = grid.std(axis=1, ddof=1)   # each fold, across its seeds
            print(
                f"{arch:<20}{strategy:<11}"
                f"{grid.values.mean():<9.4f}"
                f"{seed_sds.mean():<14.4f}"
                f"{fold_sds.mean():<14.4f}"
                f"{seed_means.std(ddof=1):<16.4f}"
                f"{fold_means.std(ddof=1):<16.4f}"
                f"{pd.Series(grid.values.ravel()).std(ddof=1):<11.4f}"
            )


def main(metric="accuracy"):
    for arch in architectures:
        for strategy in strategies:
            print_block(per_fold_metrics_df, arch, strategy, metric)
    print_summary(per_fold_metrics_df, metric)


if __name__ == "__main__":
    main()
