from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(".")
OUT_DIR = BASE / "comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIRS = {
    "Qwen 0.8B": BASE / "eval_qwen35_08b_v1",
    "Qwen 2B": BASE / "eval_qwen35_2b_v2",
    "Qwen 4B": BASE / "eval_qwen35_4b_v1",
}
MODEL_ORDER = ["Qwen 0.8B", "Qwen 2B", "Qwen 4B"]

def save_plot(fig, stem):
    fig.savefig(OUT_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{stem}.jpg", dpi=300, bbox_inches="tight")
    plt.close(fig)

fig, ax1 = plt.subplots(figsize=(11, 7))
ax2 = ax1.twinx()

handles = []
labels = []

for model in MODEL_ORDER:
    path = MODEL_DIRS[model] / "train_curve_points.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path).sort_values("step")

    # 左轴：train loss
    if "train_loss" in df.columns:
        df_loss = df.dropna(subset=["train_loss"])
        if len(df_loss):
            line1, = ax1.plot(
                df_loss["step"],
                df_loss["train_loss"],
                marker="o",
                linestyle="-",
                label=f"{model} - Train loss",
            )
            handles.append(line1)
            labels.append(f"{model} - Train loss")

    # 右轴：train token accuracy
    if "train_token_accuracy" in df.columns:
        df_acc = df.dropna(subset=["train_token_accuracy"])
        if len(df_acc):
            line2, = ax2.plot(
                df_acc["step"],
                df_acc["train_token_accuracy"],
                marker="o",
                linestyle="--",
                label=f"{model} - Train token accuracy",
            )
            handles.append(line2)
            labels.append(f"{model} - Train token accuracy")

ax1.set_xlabel("Step")
ax1.set_ylabel("Train loss")
ax2.set_ylabel("Train token accuracy")
ax1.set_title("Train Loss and Train Token Accuracy Comparison Across Qwen 0.8B, 2B, and 4B")

ax1.grid(True)
ax1.legend(handles, labels, loc="best", fontsize=9)

save_plot(fig, "comparison_train_loss_and_token_accuracy_combined")
print("Saved combined plot to:", OUT_DIR)
