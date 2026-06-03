"""Generate Grad-CAM heatmaps for the first seed of every architecture.

Iterates frozen models first, then fine-tuned models, and produces a
heatmap overlay for the first image in the `dermatitis` test class.
"""

import os
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import constants  # noqa: E402


ARCHITECTURES = [
    "convnexttiny",
    "efficientnetb0",
    "efficientnetv2b0",
    "mobilenetv2",
    "mobilenetv3small",
    "nasnetmobile",
    "resnet50",
]
APPROACHES = ["frozen", "finetuned"]
SEED = 1
TARGET_CLASS = "dermatitis"
OUTPUT_DIR = "gradcam_outputs_2"


def get_first_image_path(class_name: str) -> str:
    class_dir = os.path.join(constants.DATA_IMAGES_PATH, "test", class_name)
    files = sorted(
        f for f in os.listdir(class_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    if not files:
        raise FileNotFoundError(f"No images found in {class_dir}")
    return os.path.join(class_dir, files[4])


def load_image(img_path: str, img_size):
    bgr = cv2.imread(img_path, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(img_path)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, img_size)
    return resized.astype(np.float32), bgr


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


def build_model_path(architecture: str, approach: str, seed: int) -> str:
    filename = f"{architecture}_{approach}_seed_{seed}.keras"
    return os.path.join(constants.TRAINED_MODELS_PATH, filename)


def build_comparison_figure(original_bgr, results, out_path):
    """Build a grid: row 0 = frozen, row 1 = finetuned, col 0 = original."""
    n_cols = 1 + len(ARCHITECTURES)
    n_rows = len(APPROACHES)
    fig, axes = plt.subplots(
        n_rows, n_cols, figsize=(3.5 * n_cols, 4.5 * n_rows)
    )
    if n_rows == 1:
        axes = np.expand_dims(axes, 0)

    original_rgb = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB)

    for row, approach in enumerate(APPROACHES):
        axes[row, 0].imshow(original_rgb)
        axes[row, 0].set_title(f"original\n({approach})", fontsize=10,
                               pad=12)
        axes[row, 0].axis("off")

        for col, architecture in enumerate(ARCHITECTURES, start=1):
            ax = axes[row, col]
            entry = results.get((architecture, approach))
            if entry is None:
                ax.text(
                    0.5, 0.5, "missing",
                    ha="center", va="center", fontsize=10
                )
                ax.set_title(architecture, fontsize=9, pad=12)
                ax.axis("off")
                continue

            overlay_rgb = cv2.cvtColor(entry["overlay"], cv2.COLOR_BGR2RGB)
            ax.imshow(overlay_rgb)
            correct = "OK" if entry["predicted"] == TARGET_CLASS else "X"
            ax.set_title(
                f"{architecture}\n"
                f"pred: {entry['predicted']} ({entry['pred_prob']:.2f}) {correct}\n"
                f"{TARGET_CLASS}: {entry['target_prob']:.2f}",
                fontsize=8, pad=12,
            )
            ax.axis("off")

    fig.suptitle(
        f"Grad-CAM comparison on first {TARGET_CLASS} image (seed {SEED})",
        fontsize=14, y=0.98,
    )
    fig.subplots_adjust(hspace=0.45, wspace=0.3, top=0.90)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    train_dir = os.path.join(constants.DATA_IMAGES_PATH, "train")
    class_names = sorted(
        d for d in os.listdir(train_dir)
        if os.path.isdir(os.path.join(train_dir, d))
    )
    target_class_index = class_names.index(TARGET_CLASS)

    image_path = get_first_image_path(TARGET_CLASS)
    print(f"Using image: {image_path}")
    print(f"Target class: {TARGET_CLASS} (index {target_class_index})")
    print(f"Class order ({len(class_names)}): {class_names}")

    img_rgb_224, original_bgr = load_image(image_path, constants.IMG_SIZE)
    img_tensor = tf.convert_to_tensor(
        np.expand_dims(img_rgb_224, axis=0), dtype=tf.float32
    )

    results = {}
    for approach in APPROACHES:
        print(f"\n=== Approach: {approach} ===")
        for architecture in ARCHITECTURES:
            model_path = build_model_path(architecture, approach, SEED)
            if not os.path.exists(model_path):
                print(f"  [skip] {model_path} not found")
                continue

            print(f"  -> {architecture} ({approach}) seed {SEED}")
            model = keras.models.load_model(model_path, compile=False)

            heatmap, probs = compute_gradcam(
                model, img_tensor, class_index=target_class_index
            )
            if len(probs) != len(class_names):
                print(
                    f"     [warn] model outputs {len(probs)} classes "
                    f"but class_names has {len(class_names)}"
                )

            predicted_index = int(np.argmax(probs))
            predicted_name = (
                class_names[predicted_index]
                if predicted_index < len(class_names)
                else f"idx_{predicted_index}"
            )
            print(
                f"     predicted: {predicted_name} "
                f"({probs[predicted_index]:.3f}) | "
                f"{TARGET_CLASS} prob: {probs[target_class_index]:.3f}"
            )

            overlay = overlay_heatmap(original_bgr, heatmap)
            out_path = os.path.join(
                OUTPUT_DIR,
                f"{architecture}_{approach}_seed_{SEED}.jpg",
            )
            cv2.imwrite(out_path, overlay)
            print(f"     saved: {out_path}")

            results[(architecture, approach)] = {
                "overlay": overlay,
                "predicted": predicted_name,
                "pred_prob": float(probs[predicted_index]),
                "target_prob": float(probs[target_class_index]),
            }

            del model
            keras.backend.clear_session()

    comparison_path = os.path.join(OUTPUT_DIR, f"{TARGET_CLASS}_comparison.png")
    build_comparison_figure(original_bgr, results, comparison_path)
    print(f"\nComparison figure saved: {comparison_path}")


if __name__ == "__main__":
    main()
