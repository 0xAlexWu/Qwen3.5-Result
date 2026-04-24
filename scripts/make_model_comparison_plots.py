from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(".")
OUT_DIR = BASE / "comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIRS = {
    "Qwen 0.8B": BASE / "eval_qwen35_08b_v1",
    "Qwen 2B": BASE / "2b_final",
    "Qwen 4B": BASE / "eval_qwen35_4b_v1",
}

def load_table(filename):
    frames = []
    for model, folder in MODEL_DIRS.items():
        path = folder / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")
        df = pd.read_csv(path)
        df["model"] = model
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def save_plot(fig, stem):
    fig.savefig(OUT_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT_DIR / f"{stem}.jpg", dpi=300, bbox_inches="tight")
    plt.close(fig)

def plot_grouped_bar(df, category_col, value_col, title, ylabel, stem, category_order=None):
    plot_df = df[[category_col, "model", value_col]].copy()
    if category_order is None:
        category_order = list(dict.fromkeys(plot_df[category_col].tolist()))
    pivot = plot_df.pivot(index=category_col, columns="model", values=value_col)
    pivot = pivot.reindex(category_order)

    models = list(pivot.columns)
    x = list(range(len(pivot.index)))
    width = 0.8 / max(len(models), 1)

    fig = plt.figure(figsize=(10, 6))
    for i, model in enumerate(models):
        xpos = [v - 0.4 + width/2 + i * width for v in x]
        plt.bar(xpos, pivot[model], width=width, label=model)

    plt.xticks(x, pivot.index, rotation=20 if len(pivot.index) > 4 else 0)
    plt.ylim(0, 1.05)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(axis="y")
    save_plot(fig, stem)

def plot_line_compare(df, x_col, y_col, title, ylabel, stem):
    fig = plt.figure(figsize=(10, 6))
    for model in df["model"].drop_duplicates():
        sub = df[df["model"] == model].sort_values(x_col)
        if y_col in sub.columns and sub[y_col].notna().any():
            plt.plot(sub[x_col], sub[y_col], marker="o", label=model)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    save_plot(fig, stem)

# -------------------------
# Load tables
# -------------------------
split_df = load_table("split_level_summary.csv")
resource_df = load_table("metrics_by_resource_type.csv")
dataset_df = load_table("metrics_by_source_dataset.csv")
train_curve_df = load_table("train_curve_points.csv")
eval_curve_df = load_table("eval_curve_points.csv")

# Save merged CSVs
split_df.to_csv(OUT_DIR / "comparison_split_level_summary.csv", index=False)
resource_df.to_csv(OUT_DIR / "comparison_metrics_by_resource_type.csv", index=False)
dataset_df.to_csv(OUT_DIR / "comparison_metrics_by_source_dataset.csv", index=False)
train_curve_df.to_csv(OUT_DIR / "comparison_train_curve_points.csv", index=False)
eval_curve_df.to_csv(OUT_DIR / "comparison_eval_curve_points.csv", index=False)

# -------------------------
# Curves
# -------------------------
plot_line_compare(
    train_curve_df, "step", "train_loss",
    "Train Loss Comparison Across Models",
    "Loss",
    "comparison_train_loss"
)

plot_line_compare(
    eval_curve_df, "step", "eval_loss",
    "Eval Loss Comparison Across Models",
    "Loss",
    "comparison_eval_loss"
)

plot_line_compare(
    train_curve_df, "step", "train_token_accuracy",
    "Train Token Accuracy Comparison Across Models",
    "Token accuracy",
    "comparison_train_token_accuracy"
)

plot_line_compare(
    eval_curve_df, "step", "eval_token_accuracy",
    "Eval Token Accuracy Comparison Across Models",
    "Token accuracy",
    "comparison_eval_token_accuracy"
)

# -------------------------
# Split-level metrics
# -------------------------
split_order = [x for x in ["final_val", "test", "robustness"] if x in split_df["split"].unique()]

plot_grouped_bar(
    split_df, "split", "json_validity_rate",
    "JSON Validity by Split",
    "Rate",
    "comparison_split_json_validity",
    split_order
)

plot_grouped_bar(
    split_df, "split", "resource_type_match_rate",
    "resourceType Match by Split",
    "Rate",
    "comparison_split_resource_type_match",
    split_order
)

plot_grouped_bar(
    split_df, "split", "exact_string_match_rate",
    "Exact String Match by Split",
    "Rate",
    "comparison_split_exact_string_match",
    split_order
)

if "observation_value_exact_match_rate" in split_df.columns:
    plot_grouped_bar(
        split_df, "split", "observation_value_exact_match_rate",
        "Observation Value Exact Match by Split",
        "Rate",
        "comparison_split_observation_value_exact_match",
        split_order
    )

if "observation_unit_exact_match_rate" in split_df.columns:
    plot_grouped_bar(
        split_df, "split", "observation_unit_exact_match_rate",
        "Observation Unit Exact Match by Split",
        "Rate",
        "comparison_split_observation_unit_exact_match",
        split_order
    )

# -------------------------
# Resource-type metrics
# -------------------------
resource_order = [x for x in ["Patient", "Condition", "Observation"] if x in resource_df["resource_type"].unique()]
if not resource_order:
    resource_order = list(dict.fromkeys(resource_df["resource_type"].tolist()))

plot_grouped_bar(
    resource_df, "resource_type", "json_validity_rate",
    "JSON Validity by Resource Type",
    "Rate",
    "comparison_resource_json_validity",
    resource_order
)

plot_grouped_bar(
    resource_df, "resource_type", "resource_type_match_rate",
    "resourceType Match by Resource Type",
    "Rate",
    "comparison_resource_resource_type_match",
    resource_order
)

plot_grouped_bar(
    resource_df, "resource_type", "exact_string_match_rate",
    "Exact String Match by Resource Type",
    "Rate",
    "comparison_resource_exact_string_match",
    resource_order
)

# -------------------------
# Source-dataset metrics
# -------------------------
dataset_order = list(dict.fromkeys(dataset_df["source_dataset"].tolist()))

plot_grouped_bar(
    dataset_df, "source_dataset", "json_validity_rate",
    "JSON Validity by Source Dataset",
    "Rate",
    "comparison_dataset_json_validity",
    dataset_order
)

plot_grouped_bar(
    dataset_df, "source_dataset", "resource_type_match_rate",
    "resourceType Match by Source Dataset",
    "Rate",
    "comparison_dataset_resource_type_match",
    dataset_order
)

plot_grouped_bar(
    dataset_df, "source_dataset", "exact_string_match_rate",
    "Exact String Match by Source Dataset",
    "Rate",
    "comparison_dataset_exact_string_match",
    dataset_order
)

# Markdown summary
summary_lines = [
    "# Model Comparison Outputs",
    "",
    "Compared model result folders:",
    "- eval_qwen35_08b_v1  -> Qwen 0.8B",
    "- 2b_final            -> Qwen 2B",
    "- eval_qwen35_4b_v1   -> Qwen 4B",
    "",
    "Generated merged CSV files:",
    "- comparison_split_level_summary.csv",
    "- comparison_metrics_by_resource_type.csv",
    "- comparison_metrics_by_source_dataset.csv",
    "- comparison_train_curve_points.csv",
    "- comparison_eval_curve_points.csv",
    "",
    "Generated plots:",
]
for p in sorted(OUT_DIR.glob("comparison_*.png")):
    summary_lines.append(f"- {p.name}")
(OUT_DIR / "README.md").write_text("\n".join(summary_lines), encoding="utf-8")

print("Done. Generated files in:", OUT_DIR)
for p in sorted(OUT_DIR.iterdir()):
    if p.is_file():
        print(p.name)
