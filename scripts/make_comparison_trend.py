from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(".")
OUT_DIR = BASE / "comparison-trend"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_DIRS = {
    "Qwen 0.8B": BASE / "eval_qwen35_08b_v1",
    "Qwen 2B": BASE / "eval_qwen35_2b_v2",
    "Qwen 4B": BASE / "eval_qwen35_4b_v1",
}
MODEL_ORDER = ["Qwen 0.8B", "Qwen 2B", "Qwen 4B"]

def load_csv_for_all(filename):
    frames = []
    for model in MODEL_ORDER:
        path = MODEL_DIRS[model] / filename
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

def plot_train_line(df, y_col, title, ylabel, stem):
    fig = plt.figure(figsize=(10, 6))
    for model in MODEL_ORDER:
        sub = df[df["model"] == model].copy()
        if y_col in sub.columns:
            sub = sub.dropna(subset=[y_col]).sort_values("step")
            if len(sub):
                plt.plot(sub["step"], sub[y_col], marker="o", label=model)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    save_plot(fig, stem)

def plot_nested_grouped_bars_with_trend(
    df,
    category_col,
    metrics,
    title,
    ylabel,
    stem,
    category_order=None
):
    if category_order is None:
        category_order = list(dict.fromkeys(df[category_col].tolist()))

    n_cat = len(category_order)
    n_metric = len(metrics)
    n_model = len(MODEL_ORDER)

    group_width = 0.84
    bar_width = group_width / (n_metric * n_model)

    fig = plt.figure(figsize=(13, 6))

    for cat_i, cat in enumerate(category_order):
        base_x = cat_i

        for met_i, (metric_col, metric_name) in enumerate(metrics):
            trend_x = []
            trend_y = []

            for mod_i, model in enumerate(MODEL_ORDER):
                xpos = (
                    base_x
                    - group_width / 2
                    + (met_i * n_model + mod_i + 0.5) * bar_width
                )

                sub = df[(df[category_col] == cat) & (df["model"] == model)]
                value = None
                if len(sub) and metric_col in sub.columns:
                    value = sub.iloc[0][metric_col]

                bar_label = None
                if cat_i == 0:
                    bar_label = f"{metric_name} - {model}"

                if pd.notna(value):
                    plt.bar(xpos, value, width=bar_width, label=bar_label)
                    trend_x.append(xpos)
                    trend_y.append(value)

            if len(trend_x) >= 2:
                line_label = None
                if cat_i == 0:
                    line_label = f"{metric_name} trend (0.8B→2B→4B)"
                plt.plot(trend_x, trend_y, marker="o", linewidth=1.2, linestyle="--", label=line_label)

    plt.xticks(range(n_cat), category_order, rotation=20 if n_cat > 4 else 0)
    plt.ylim(0, 1.05)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(fontsize=8, ncol=3)
    plt.grid(axis="y")
    save_plot(fig, stem)

# 1) train loss only
train_curve = load_csv_for_all("train_curve_points.csv")
plot_train_line(
    train_curve,
    "train_loss",
    "Train Loss Comparison Across Qwen 0.8B, 2B, and 4B",
    "Loss",
    "comparison_trend_train_loss_only"
)

# 2) train token accuracy only
plot_train_line(
    train_curve,
    "train_token_accuracy",
    "Train Token Accuracy Comparison Across Qwen 0.8B, 2B, and 4B",
    "Token accuracy",
    "comparison_trend_train_token_accuracy_only"
)

# 3) split-level structured metrics
split_df = load_csv_for_all("split_level_summary.csv")
split_order = [x for x in ["final_val", "test", "robustness"] if x in split_df["split"].unique()]
plot_nested_grouped_bars_with_trend(
    split_df,
    "split",
    [
        ("json_validity_rate", "JSON validity"),
        ("resource_type_match_rate", "resourceType match"),
        ("exact_string_match_rate", "Exact string match"),
    ],
    "Split-level Structured Output Metrics Comparison with Model Trends",
    "Rate",
    "comparison_trend_split_level_structured_metrics",
    split_order,
)

# 4) metrics by resource type
resource_df = load_csv_for_all("metrics_by_resource_type.csv")
resource_order = [x for x in ["Patient", "Condition", "Observation"] if x in resource_df["resource_type"].unique()]
if not resource_order:
    resource_order = list(dict.fromkeys(resource_df["resource_type"].tolist()))

plot_nested_grouped_bars_with_trend(
    resource_df,
    "resource_type",
    [
        ("json_validity_rate", "JSON validity"),
        ("resource_type_match_rate", "resourceType match"),
        ("exact_string_match_rate", "Exact string match"),
    ],
    "Metrics by Resource Type Comparison with Model Trends",
    "Rate",
    "comparison_trend_metrics_by_resource_type",
    resource_order,
)

# 5) metrics by source dataset
dataset_df = load_csv_for_all("metrics_by_source_dataset.csv")
dataset_order = list(dict.fromkeys(dataset_df["source_dataset"].tolist()))

plot_nested_grouped_bars_with_trend(
    dataset_df,
    "source_dataset",
    [
        ("json_validity_rate", "JSON validity"),
        ("resource_type_match_rate", "resourceType match"),
        ("exact_string_match_rate", "Exact string match"),
    ],
    "Metrics by Source Dataset Comparison with Model Trends",
    "Rate",
    "comparison_trend_metrics_by_source_dataset",
    dataset_order,
)

# 6) observation metrics by split
plot_nested_grouped_bars_with_trend(
    split_df,
    "split",
    [
        ("observation_value_exact_match_rate", "Value exact match"),
        ("observation_unit_exact_match_rate", "Unit exact match"),
    ],
    "Observation Metrics by Split Comparison with Model Trends",
    "Rate",
    "comparison_trend_observation_metrics_by_split",
    split_order,
)

readme = OUT_DIR / "README.md"
readme.write_text(
    "\n".join([
        "# Comparison Trend Outputs",
        "",
        "Source folders:",
        "- eval_qwen35_08b_v1",
        "- eval_qwen35_2b_v2",
        "- eval_qwen35_4b_v1",
        "",
        "Generated figures:",
        "- comparison_trend_train_loss_only",
        "- comparison_trend_train_token_accuracy_only",
        "- comparison_trend_split_level_structured_metrics",
        "- comparison_trend_metrics_by_resource_type",
        "- comparison_trend_metrics_by_source_dataset",
        "- comparison_trend_observation_metrics_by_split",
        "",
        "Bar charts include model trend lines across 0.8B → 2B → 4B.",
    ]),
    encoding="utf-8"
)

print("Done. Generated comparison-trend figures in:", OUT_DIR)
for p in sorted(OUT_DIR.iterdir()):
    if p.is_file():
        print(p.name)
