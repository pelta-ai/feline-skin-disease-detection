"""Generate Grad-CAM heatmaps from the cross-validation prediction files.

The CV sweep (`src/colab_notebooks/colab_training_2.ipynb`) writes, per run:

    preds_<arch>_<strategy>_f<fold>_s<seed>.npy   test probabilities, in row order
    testset_f<fold>.csv                           that fold's test rows, same order

and keeps weights for exactly one (fold, seed) per arch x strategy - by default
fold 0 / seed 1 - which is the only run Grad-CAM can be run on.

Both the image and the numbers printed beside each heatmap come out of those
saved probabilities rather than from a fresh `model.predict` over a folder, so
the panel shows what the scored run actually predicted. The weights are needed
only for the heatmap itself.

Examples:
    python src/generate_gradcam.py --probs-dir cv_run
    python src/generate_gradcam.py --probs-dir cv_run --class dermatitis --select worst
    python src/generate_gradcam.py --probs-dir cv_run --image foo.rf.abc123.jpg
"""

import argparse
import glob
import os
import re
import sys

# TensorFlow has to be imported before pandas and cv2 on Windows. Their Cython
# extensions take enough static TLS slots that TensorFlow's native library then
# fails to initialise ("DLL load failed while importing
# _pywrap_tensorflow_internal"). Keep these two lines first - a formatter that
# re-sorts them alphabetically will bring the crash back.
import tensorflow as tf
from tensorflow import keras

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import constants  # noqa: E402


STRATEGIES = ["frozen", "finetuned"]
# The sweep's KEEP_FOLD / KEEP_SEED - the only run whose weights were kept.
DEFAULT_FOLD = 0
DEFAULT_SEED = 1
DEFAULT_CLASS = "dermatitis"
DEFAULT_OUTPUT_DIR = "gradcam_outputs_preds"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_FOLD_CSV = os.path.join(
    PROJECT_ROOT, constants.DUPLICATE_AUDIT_PATH, "fold_assignments.csv"
)


# ── inputs ──────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--probs-dir", default=constants.MODEL_PROBS_PATH,
                        help="folder holding preds_*.npy and testset_f*.csv "
                             f"(default: {constants.MODEL_PROBS_PATH})")
    parser.add_argument("--models-dir", default=constants.TRAINED_MODELS_PATH,
                        help="folder holding <arch>_<strategy>_f<fold>_s<seed>.keras "
                             f"(default: {constants.TRAINED_MODELS_PATH})")
    parser.add_argument("--fold", type=int, default=DEFAULT_FOLD,
                        help=f"fold whose predictions to read (default: {DEFAULT_FOLD})")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help=f"seed whose predictions to read (default: {DEFAULT_SEED})")
    parser.add_argument("--class", dest="target_class", default=DEFAULT_CLASS,
                        help=f"true class to draw the image from (default: {DEFAULT_CLASS})")
    parser.add_argument("--select", choices=["index", "best", "worst", "split"],
                        default="index",
                        help="how to pick the image among that class's test rows: "
                             "index = the --index'th row; best/worst = highest/lowest "
                             "mean probability for the true class across the runs; "
                             "split = where the runs disagree most (default: index)")
    parser.add_argument("--index", type=int, default=0,
                        help="row to use when --select index (default: 0)")
    parser.add_argument("--image", default=None,
                        help="pick a specific test image by filename (or any unique "
                             "substring of its path); overrides --select and --class")
    parser.add_argument("--explain", choices=["true", "predicted"], default="true",
                        help="class the heatmap is computed for: the true label, or "
                             "each run's own predicted class (default: true)")
    parser.add_argument("--archs", nargs="+", default=None,
                        help="architectures to include (default: whatever prediction "
                             "files exist for this fold/seed)")
    parser.add_argument("--strategies", nargs="+", default=STRATEGIES,
                        help=f"strategies to include (default: {' '.join(STRATEGIES)})")
    parser.add_argument("--out-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"where to write the overlays (default: {DEFAULT_OUTPUT_DIR})")
    return parser.parse_args()


def load_class_names(probs_dir):
    """Class order used at training time: sorted labels over the whole fold file.

    `set_class_names` sorted the labels of the *full* dataframe, so a fold's own
    test rows are not a safe substitute - a fold need not contain every class.
    Prefer the copy parked next to the probabilities; it is the one that matches.
    """
    candidates = [os.path.join(probs_dir, "fold_assignments.csv"), REPO_FOLD_CSV]
    fold_csv = next((p for p in candidates if os.path.exists(p)), None)
    if fold_csv is None:
        raise FileNotFoundError(
            f"fold_assignments.csv not found. Looked in: {candidates}"
        )
    def _key(path):
        return os.path.normcase(os.path.abspath(path))

    if _key(os.path.dirname(fold_csv)) != _key(probs_dir):
        print(f"[warn] using {fold_csv}, not the copy inside {probs_dir}; if the "
              "folds were regenerated since training, the class order may differ")
    return sorted(pd.read_csv(fold_csv)["label"].unique()), fold_csv


def load_testset(probs_dir, fold):
    """The fold's test rows, in the same order as every preds_*.npy for that fold."""
    path = os.path.join(probs_dir, f"testset_f{fold}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found - point --probs-dir at the folder the sweep wrote "
            "(the one holding preds_*.npy and testset_f*.csv)."
        )
    # Positional order is the contract with the .npy files, so drop any index.
    return pd.read_csv(path).reset_index(drop=True)


def discover_archs(probs_dir, strategies, fold, seed):
    """Architecture names taken from the prediction filenames themselves.

    Saves keeping a hardcoded list in sync with whatever `name=` the sweep used.
    """
    found = set()
    for strategy in strategies:
        pattern = os.path.join(probs_dir, f"preds_*_{strategy}_f{fold}_s{seed}.npy")
        for path in glob.glob(pattern):
            name = os.path.basename(path)
            match = re.fullmatch(
                rf"preds_(.+)_{strategy}_f{fold}_s{seed}\.npy", name
            )
            if match and not name.startswith("preds_val_"):
                found.add(match.group(1))
    return sorted(found)


def load_run_probs(probs_dir, archs, strategies, fold, seed, n_rows, n_classes):
    """{(arch, strategy): probs} for every run that has a prediction file."""
    probs = {}
    for arch in archs:
        for strategy in strategies:
            path = os.path.join(
                probs_dir, f"preds_{arch}_{strategy}_f{fold}_s{seed}.npy"
            )
            if not os.path.exists(path):
                print(f"  [skip] {path} not found")
                continue

            run_probs = np.load(path)
            if run_probs.shape != (n_rows, n_classes):
                raise ValueError(
                    f"{os.path.basename(path)} has shape {run_probs.shape}, expected "
                    f"({n_rows}, {n_classes}) - these probabilities were not written "
                    f"for testset_f{fold}.csv as it stands now."
                )
            probs[(arch, strategy)] = run_probs
    return probs


# ── picking the image out of the predictions ────────────────────────


def select_row(test_df, run_probs, class_names, args):
    """Return the positional index into testset_f<fold>.csv to explain."""
    if args.image:
        matches = test_df.index[
            test_df["path"].str.replace("\\", "/", regex=False)
                           .str.contains(args.image.replace("\\", "/"), regex=False)
        ]
        if len(matches) == 0:
            raise ValueError(f"no test row in this fold matches '{args.image}'")
        if len(matches) > 1:
            raise ValueError(
                f"'{args.image}' matches {len(matches)} rows, e.g. "
                + ", ".join(test_df.loc[matches[:3], "path"])
            )
        return int(matches[0])

    rows = test_df.index[test_df["label"] == args.target_class]
    if len(rows) == 0:
        raise ValueError(
            f"class '{args.target_class}' has no test rows in fold {args.fold}. "
            f"Present: {sorted(test_df['label'].unique())}"
        )

    if args.select == "index":
        if not -len(rows) <= args.index < len(rows):
            raise IndexError(
                f"--index {args.index} out of range: fold {args.fold} has "
                f"{len(rows)} {args.target_class} test images"
            )
        return int(rows[args.index])

    if not run_probs:
        raise ValueError(f"--select {args.select} needs at least one preds_*.npy")

    class_index = class_names.index(args.target_class)
    # Mean probability the runs gave the true class, one value per candidate row.
    stacked = np.stack([p[rows, class_index] for p in run_probs.values()])
    if args.select == "best":
        return int(rows[int(np.argmax(stacked.mean(axis=0)))])
    if args.select == "worst":
        return int(rows[int(np.argmin(stacked.mean(axis=0)))])
    # split: the runs disagree the most about this image
    return int(rows[int(np.argmax(stacked.max(axis=0) - stacked.min(axis=0)))])


def resolve_image_path(row):
    """Absolute path to the image, whatever cwd the sweep ran under.

    `path` was written by the sweep and is relative to the repo root it used;
    `relpath` (split/class/filename) is the portable fallback.
    """
    candidates = []
    if isinstance(row.get("path"), str):
        candidates += [row["path"], os.path.join(PROJECT_ROOT, row["path"])]
    if isinstance(row.get("relpath"), str):
        parts = row["relpath"].split("/")
        candidates.append(os.path.join(PROJECT_ROOT, constants.DATA_PATH, *parts))
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "test image not found on this machine. Tried:\n  " + "\n  ".join(candidates)
    )


# ── images ──────────────────────────────────────────────────────────


def load_model_input(img_path, img_size):
    """Decode exactly as `make_dataset_from_df` did, so the forward pass here
    matches the one that produced the saved probabilities."""
    img = tf.io.read_file(img_path)
    img = tf.io.decode_image(img, channels=3, expand_animations=False)
    img = tf.image.resize(img, img_size)
    return tf.expand_dims(tf.cast(img, tf.float32), axis=0)


def load_display_image(img_path):
    """Full-resolution BGR copy for the overlay (imdecode handles non-ASCII paths)."""
    bgr = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError(f"could not decode {img_path}")
    return bgr


# ── Grad-CAM ────────────────────────────────────────────────────────


def find_backbone(model):
    for layer in model.layers:
        if isinstance(layer, keras.Model) and not isinstance(layer, keras.Sequential):
            return layer
    raise ValueError("No nested backbone model found")


def find_last_conv_layer_name(backbone):
    for layer in reversed(backbone.layers):
        try:
            shape = layer.output.shape
        except AttributeError:
            continue
        if len(shape) == 4:
            return layer.name
    raise ValueError("No 4D output layer found in backbone")


def compute_gradcam(model, img_tensor, class_index):
    backbone = find_backbone(model)
    last_conv_name = find_last_conv_layer_name(backbone)
    last_conv_layer = backbone.get_layer(last_conv_name)

    captured = {}
    tape_holder = {}
    original_call = last_conv_layer.call

    def hooked_call(*args, **kwargs):
        out = original_call(*args, **kwargs)
        tape = tape_holder.get("tape")
        if tape is not None:
            tape.watch(out)
        captured["conv"] = out
        return out

    last_conv_layer.call = hooked_call
    try:
        with tf.GradientTape() as tape:
            tape_holder["tape"] = tape
            predictions = model(img_tensor, training=False)
            loss = predictions[:, class_index]
        conv_out = captured["conv"]
        grads = tape.gradient(loss, conv_out)
    finally:
        last_conv_layer.call = original_call

    if grads is None:
        raise RuntimeError(
            f"Gradient flow broken at layer '{last_conv_name}'"
        )
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).numpy()
    conv_out_np = conv_out[0].numpy()

    for i in range(pooled_grads.shape[-1]):
        conv_out_np[:, :, i] *= pooled_grads[i]

    heatmap = np.mean(conv_out_np, axis=-1)
    heatmap = np.maximum(heatmap, 0)
    max_val = heatmap.max()
    if max_val > 0:
        heatmap /= max_val
    return heatmap, predictions.numpy()[0]


def overlay_heatmap(original_bgr, heatmap, alpha=0.4):
    h, w = original_bgr.shape[:2]
    heatmap_resized = cv2.resize(heatmap, (w, h))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
    return cv2.addWeighted(original_bgr, alpha, heatmap_color, 1 - alpha, 0)


# ── output ──────────────────────────────────────────────────────────


def build_model_path(models_dir, arch, strategy, fold, seed):
    return os.path.join(models_dir, f"{arch}_{strategy}_f{fold}_s{seed}.keras")


def build_comparison_figure(original_bgr, results, archs, strategies,
                            true_class, fold, seed, out_path):
    """Grid: one row per strategy, column 0 = original, then one column per arch."""
    n_cols = 1 + len(archs)
    n_rows = len(strategies)
    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(3.5 * n_cols, 4.5 * n_rows), squeeze=False
    )

    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

    for row, strategy in enumerate(strategies):
        axes[row][0].imshow(original_rgb)
        axes[row][0].set_title(f"original\n({strategy})", fontsize=10, pad=12)
        axes[row][0].axis("off")

        for col, arch in enumerate(archs, start=1):
            ax = axes[row][col]
            entry = results.get((arch, strategy))
            if entry is None:
                ax.text(0.5, 0.5, "missing", ha="center", va="center", fontsize=10)
                ax.set_title(arch, fontsize=9, pad=12)
                ax.axis("off")
                continue

            ax.imshow(cv2.cvtColor(entry["overlay"], cv2.COLOR_BGR2RGB))
            correct = "OK" if entry["predicted"] == true_class else "X"
            ax.set_title(
                f"{arch}\n"
                f"pred: {entry['predicted']} ({entry['pred_prob']:.2f}) {correct}\n"
                f"{true_class}: {entry['true_prob']:.2f}",
                fontsize=8, pad=12,
            )
            ax.axis("off")

    fig.suptitle(
        f"Grad-CAM on a {true_class} test image (fold {fold}, seed {seed})\n"
        "predictions read from the saved run probabilities",
        fontsize=14, y=0.99,
    )
    fig.subplots_adjust(hspace=0.45, wspace=0.3, top=0.88)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    class_names, fold_csv = load_class_names(args.probs_dir)
    test_df = load_testset(args.probs_dir, args.fold)

    archs = args.archs or discover_archs(
        args.probs_dir, args.strategies, args.fold, args.seed
    )
    if not archs:
        raise FileNotFoundError(
            f"no preds_*_f{args.fold}_s{args.seed}.npy files in {args.probs_dir}"
        )

    run_probs = load_run_probs(args.probs_dir, archs, args.strategies,
                               args.fold, args.seed, len(test_df), len(class_names))

    row_index = select_row(test_df, run_probs, class_names, args)
    row = test_df.iloc[row_index]
    true_class = row["label"]
    true_index = class_names.index(true_class)
    image_path = resolve_image_path(row)

    print(f"Classes from : {fold_csv}")
    print(f"Test rows    : {args.probs_dir}/testset_f{args.fold}.csv ({len(test_df)} rows)")
    print(f"Image        : {image_path}")
    print(f"Row          : {row_index} (selection: "
          f"{args.image or args.select})")
    print(f"True class   : {true_class} (index {true_index})")
    print(f"Class order  : {class_names}")
    explained = ("each run's predicted class" if args.explain == "predicted"
                 else true_class)
    print(f"Explaining   : {explained}")

    img_tensor = load_model_input(image_path, constants.IMG_SIZE)
    original_bgr = load_display_image(image_path)

    results = {}
    for strategy in args.strategies:
        print(f"\n=== {strategy} ===")
        for arch in archs:
            probs = run_probs.get((arch, strategy))
            if probs is None:
                continue

            saved = probs[row_index]
            predicted_index = int(np.argmax(saved))
            predicted_name = class_names[predicted_index]
            print(f"  -> {arch} ({strategy}) f{args.fold} s{args.seed}")
            print(f"     saved preds: {predicted_name} ({saved[predicted_index]:.3f}) | "
                  f"{true_class}: {saved[true_index]:.3f}")

            model_path = build_model_path(args.models_dir, arch, strategy,
                                          args.fold, args.seed)
            if not os.path.exists(model_path):
                # Weights were kept for one (fold, seed) only; the numbers above
                # still stand, there is just nothing to backprop through.
                print(f"     [skip heatmap] {model_path} not found")
                continue

            model = keras.models.load_model(model_path, compile=False)
            class_index = predicted_index if args.explain == "predicted" else true_index
            heatmap, live_probs = compute_gradcam(model, img_tensor, class_index)

            # The forward pass here should reproduce the saved row. A visible gap
            # means the .npy and the .keras are not from the same run.
            drift = float(np.abs(live_probs - saved).max())
            if drift > 0.05:
                print(f"     [warn] live probabilities differ from the saved ones "
                      f"by up to {drift:.3f} - mismatched files?")

            overlay = overlay_heatmap(original_bgr, heatmap)
            out_path = os.path.join(
                args.out_dir,
                f"{arch}_{strategy}_f{args.fold}_s{args.seed}.jpg",
            )
            cv2.imencode(".jpg", overlay)[1].tofile(out_path)
            print(f"     saved: {out_path}")

            results[(arch, strategy)] = {
                "overlay": overlay,
                "predicted": predicted_name,
                "pred_prob": float(saved[predicted_index]),
                "true_prob": float(saved[true_index]),
            }

            del model
            keras.backend.clear_session()

    if not results:
        print(f"\nNo heatmaps produced - no matching .keras files in {args.models_dir}. "
              f"Weights are kept for one (fold, seed) per arch x strategy "
              f"(the sweep's default is fold {DEFAULT_FOLD} / seed {DEFAULT_SEED}).")
        return

    comparison_path = os.path.join(
        args.out_dir, f"{true_class}_row{row_index}_comparison.png"
    )
    build_comparison_figure(original_bgr, results, archs, args.strategies,
                            true_class, args.fold, args.seed, comparison_path)
    print(f"\nComparison figure saved: {comparison_path}")


if __name__ == "__main__":
    main()
