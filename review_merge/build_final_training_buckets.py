from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = WORKSPACE_ROOT / "review_merge"
OUTPUT_DIR = WORKSPACE_ROOT / "outputs" / "review_merge"

DATASET_FILES = {
    "synthea": "synthea_review_merge.csv",
    "official": "official_review_merge.csv",
    "nhanes": "nhanes_review_merge.csv",
    "gpt_expanded": "gpt_expanded_review_merge.csv",
    "mimic_eicu": "mimic_eicu_review_merge.csv",
}

QUEUE_FILES = {
    "synthea": "synthea_adjudication_queue.csv",
    "official": "official_adjudication_queue.csv",
    "nhanes": "nhanes_adjudication_queue.csv",
    "gpt_expanded": "gpt_expanded_adjudication_queue.csv",
    "mimic_eicu": "mimic_eicu_adjudication_queue.csv",
}

DATASET_LABELS = {
    "synthea": "Synthea",
    "official": "Official",
    "nhanes": "NHANES",
    "gpt_expanded": "GPT-expanded",
    "mimic_eicu": "MIMIC/eICU demo",
}

OUTPUT_COLUMNS = [
    "dataset",
    "pair_id_or_candidate_id",
    "reviewer_1_decision",
    "reviewer_2_decision",
    "merged_decision",
    "adjudication_needed",
    "disagreement_summary",
    "preliminary_training_bucket",
    "final_decision",
    "final_notes",
]


def normalize_dict(row: dict[str, str]) -> dict[str, str]:
    return {key.lstrip("\ufeff"): (value or "") for key, value in row.items()}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [normalize_dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str | None) -> str:
    return (value or "").strip()


def low(value: str | None) -> str:
    return norm(value).lower()


def infer_merged_decision(row: dict[str, str]) -> str:
    merged = low(row.get("merged_decision"))
    if merged:
        return merged
    reviewer_1 = low(row.get("reviewer_1_decision"))
    reviewer_2 = low(row.get("reviewer_2_decision"))
    if reviewer_1 and reviewer_1 == reviewer_2:
        return reviewer_1
    return ""


def get_explicit_final_decision(row: dict[str, str]) -> str:
    for key in ("final_decision", "final_adjudication_decision"):
        value = low(row.get(key))
        if value:
            return value
    return ""


def get_existing_notes(row: dict[str, str]) -> str:
    for key in ("final_notes", "final_adjudication_notes"):
        value = norm(row.get(key))
        if value:
            return value
    return ""


def get_identifier(row: dict[str, str]) -> str:
    return norm(row.get("pair_id")) or norm(row.get("candidate_id"))


def text_blob(row: dict[str, str]) -> str:
    parts = [
        row.get("disagreement_summary", ""),
        row.get("reviewer_1_comments", ""),
        row.get("reviewer_2_comments", ""),
        row.get("final_notes", ""),
        row.get("final_adjudication_notes", ""),
    ]
    return " ".join(part for part in parts if part).lower()


def has_severe_disagreement(dataset: str, row: dict[str, str]) -> bool:
    summary = low(row.get("disagreement_summary"))
    blob = text_blob(row)

    severe_summary_terms = [
        "unsupported_fact",
        "context_leakage",
        "clinically meaningful omission",
        "disagreement on omission",
    ]
    if any(term in summary for term in severe_summary_terms):
        return True

    severe_comment_terms = [
        "unsupported context",
        "unsupported extension",
        "unsupported fact",
        "unsupported facts",
        "unsupported field",
        "unsupported fields",
        "unsupported additions",
        "unsupported addition",
        "unsupported reference",
        "unsupported references",
        "context leakage",
        "hallucinated",
        "hallucination",
        "fabricated",
        "invents ",
        "identical hallucinations",
        "not supported by input",
    ]
    if any(term in blob for term in severe_comment_terms):
        return True

    # NHANES pending rows are known to be lighter-weight disposition disagreements,
    # so avoid escalating generic "unsupported" wording unless it is explicit.
    if dataset == "nhanes":
        return False

    return False


def is_minor_disposition_only(row: dict[str, str]) -> bool:
    summary = low(row.get("disagreement_summary"))
    return "disposition-only disagreement" in summary or "disposition only disagreement" in summary


def map_decision_to_bucket(decision: str) -> str:
    if decision == "keep":
        return "use_now"
    if decision == "revise":
        return "use_after_revision"
    if decision == "drop":
        return "exclude_for_now"
    return "use_after_revision"


def build_bucket_note(dataset: str, bucket: str, row: dict[str, str], final_decision: str) -> str:
    notes: list[str] = []
    existing = get_existing_notes(row)
    if existing:
        notes.append(existing)

    merged = infer_merged_decision(row)
    adjudication_needed = low(row.get("adjudication_needed")) == "yes"
    severe = has_severe_disagreement(dataset, row)
    disposition_only = is_minor_disposition_only(row)

    if dataset == "synthea":
        if bucket == "use_now":
            notes.append("Synthea policy: agreed clean row is ready for immediate formal training use.")
        elif bucket == "use_after_revision":
            notes.append("Synthea policy: hold only for targeted repair or adjudication before use.")
    elif dataset == "nhanes":
        if bucket == "use_now":
            notes.append("NHANES policy: clean non-pending row may enter training now.")
        elif bucket == "use_after_revision":
            notes.append("NHANES policy: pending row is repairable and should be resolved in targeted adjudication.")
        else:
            notes.append("NHANES policy: keep out for now because disagreement appears materially substantive.")
    elif dataset == "official":
        if bucket == "use_after_revision":
            notes.append("Official policy: conserve for targeted revision/adjudication before any broader use.")
        else:
            notes.append("Official policy: unresolved unsupported or leakage concerns keep this row out of training for now.")
    elif dataset == "gpt_expanded":
        if bucket == "use_now":
            notes.append("Row-level keep is clean, but GPT-expanded as a dataset line is still not backbone-ready.")
        elif bucket == "use_after_revision":
            notes.append("GPT-expanded policy: unresolved row is only tentatively salvageable and needs explicit adjudication before use.")
        else:
            notes.append("GPT-expanded policy: default conservative exclusion until much more of the pending queue is resolved.")
    elif dataset == "mimic_eicu":
        notes.append("MIMIC/eICU policy: demo_only_low_weight_candidate at most; exclude from formal training for now.")

    if adjudication_needed and not final_decision:
        if severe:
            notes.append("No adjudication outcome recorded; preliminarily bucketed conservatively due to unsupported/context-leakage/omission risk.")
        elif disposition_only:
            notes.append("No adjudication outcome recorded; preliminarily bucketed as repairable because disagreement is disposition-only.")
        else:
            notes.append("No adjudication outcome recorded; preliminarily bucketed conservatively pending human adjudication.")
    elif final_decision:
        if low(final_decision) == merged and merged:
            notes.append(f"Final decision carried from merged_decision={merged}.")
        else:
            notes.append(f"Final decision resolved as {final_decision}.")

    return " ".join(note for note in notes if note)


def assign_bucket(dataset: str, row: dict[str, str]) -> tuple[str, str]:
    explicit_final = get_explicit_final_decision(row)
    merged = infer_merged_decision(row)
    adjudication_needed = low(row.get("adjudication_needed")) == "yes"
    severe = has_severe_disagreement(dataset, row)
    disposition_only = is_minor_disposition_only(row)

    if dataset == "mimic_eicu":
        final_decision = explicit_final or (merged if not adjudication_needed and merged not in {"", "pending_adjudication"} else "")
        return "exclude_for_now", final_decision

    if explicit_final:
        return map_decision_to_bucket(explicit_final), explicit_final

    if not adjudication_needed:
        resolved_decision = merged
        if not resolved_decision:
            reviewer_1 = low(row.get("reviewer_1_decision"))
            reviewer_2 = low(row.get("reviewer_2_decision"))
            if reviewer_1 and reviewer_1 == reviewer_2:
                resolved_decision = reviewer_1
        return map_decision_to_bucket(resolved_decision), resolved_decision

    if dataset == "synthea":
        return ("exclude_for_now" if severe else "use_after_revision"), ""

    if dataset == "nhanes":
        if severe and not disposition_only:
            return "exclude_for_now", ""
        return "use_after_revision", ""

    if dataset == "official":
        if severe:
            return "exclude_for_now", ""
        return "use_after_revision", ""

    if dataset == "gpt_expanded":
        if severe:
            return "exclude_for_now", ""
        if disposition_only:
            return "use_after_revision", ""
        return "exclude_for_now", ""

    return "exclude_for_now", ""


def load_agreement_master() -> dict[str, dict[str, str]]:
    rows = read_csv_rows(INPUT_DIR / "reviewer_agreement_master.csv")
    agreement = {}
    for row in rows:
        agreement[low(row.get("dataset"))] = row
    return agreement


def queue_counts() -> dict[str, int]:
    counts: dict[str, int] = {}
    for dataset, filename in QUEUE_FILES.items():
        counts[dataset] = len(read_csv_rows(INPUT_DIR / filename))
    return counts


def build_master_rows() -> list[dict[str, str]]:
    master_rows: list[dict[str, str]] = []
    for dataset, filename in DATASET_FILES.items():
        for row in read_csv_rows(INPUT_DIR / filename):
            merged = infer_merged_decision(row)
            bucket, final_decision = assign_bucket(dataset, row)
            master_row = {
                "dataset": dataset,
                "pair_id_or_candidate_id": get_identifier(row),
                "reviewer_1_decision": norm(row.get("reviewer_1_decision")),
                "reviewer_2_decision": norm(row.get("reviewer_2_decision")),
                "merged_decision": merged or norm(row.get("merged_decision")),
                "adjudication_needed": norm(row.get("adjudication_needed")),
                "disagreement_summary": norm(row.get("disagreement_summary")),
                "preliminary_training_bucket": bucket,
                "final_decision": final_decision,
                "final_notes": build_bucket_note(dataset, bucket, row, final_decision),
            }
            master_rows.append(master_row)
    return master_rows


def build_bucket_summary(master_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in master_rows:
        dataset = row["dataset"]
        counters[dataset][row["preliminary_training_bucket"]] += 1
        counters[dataset]["total_reviewed_rows"] += 1

    summary_rows: list[dict[str, str]] = []
    for dataset in DATASET_FILES:
        counter = counters[dataset]
        summary_rows.append(
            {
                "dataset": dataset,
                "use_now_count": str(counter["use_now"]),
                "use_after_revision_count": str(counter["use_after_revision"]),
                "exclude_for_now_count": str(counter["exclude_for_now"]),
                "total_reviewed_rows": str(counter["total_reviewed_rows"]),
            }
        )
    return summary_rows


def write_priority_plan(summary_rows: list[dict[str, str]], agreement: dict[str, dict[str, str]], queues: dict[str, int]) -> None:
    by_dataset = {row["dataset"]: row for row in summary_rows}

    lines = [
        "# Adjudication Priority Plan",
        "",
        "## Queue Ranking",
        "",
        f"1. **NHANES** ({queues['nhanes']} rows pending): resolve first. It has the lightest remaining adjudication burden among the non-empty queues, most unresolved rows are disposition-only, and finishing it quickly unlocks a mostly clean dataset line for formal training.",
        f"2. **Official** ({queues['official']} rows pending): resolve second. It is important reference material, but its unresolved rows carry more unsupported-fact and leakage concerns than NHANES, so the cleanup cost per usable row is higher.",
        f"3. **GPT-expanded** ({queues['gpt_expanded']} rows pending): defer until the cleaner sources are finalized. The queue is large and noisy, so adjudicating it early would consume attention before the higher-confidence sources are stabilized.",
        "",
        "NHANES should likely be resolved before Official or GPT-expanded because the remaining queue is smaller, the disagreement pattern is mostly targeted and disposition-only, and the expected yield of quickly promotable training rows is higher.",
        "",
        "GPT-expanded should be deferred until Synthea and NHANES are finalized, and until a meaningful share of Official is adjudicated. Even where some GPT-expanded rows look individually clean, the dataset line as a whole is still too adjudication-heavy to serve as a backbone source.",
        "",
        "Synthea is ready for immediate training use now. Its reviewed rows are already stable enough to populate the first formal bucket without additional reviewer-agreement work.",
        "",
        "MIMIC/eICU should remain demo-only or, at most, a very small low-weight realism subset. It should not be promoted into the backbone formal training mix at this stage.",
        "",
        "## Operational Read",
        "",
        f"- `Synthea`: immediate use now ({by_dataset['synthea']['use_now_count']} rows in `use_now`).",
        f"- `NHANES`: targeted adjudication next ({by_dataset['nhanes']['use_after_revision_count']} rows in `use_after_revision`).",
        f"- `Official`: hold broader use until heavier adjudication is completed ({by_dataset['official']['exclude_for_now_count']} rows already conservatively excluded).",
        f"- `GPT-expanded`: defer broad training use while the large pending queue remains unresolved.",
        f"- `MIMIC/eICU demo`: keep out of formal training despite clean review agreement.",
        "",
        "Reviewer-agreement metrics above are reused from the existing master summary and are not recomputed here.",
    ]
    (OUTPUT_DIR / "adjudication_priority_plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_training_readiness_summary(summary_rows: list[dict[str, str]], agreement: dict[str, dict[str, str]]) -> None:
    by_dataset = {row["dataset"]: row for row in summary_rows}

    synthea = by_dataset["synthea"]
    nhanes = by_dataset["nhanes"]
    official = by_dataset["official"]
    gptx = by_dataset["gpt_expanded"]
    mimic = by_dataset["mimic_eicu"]

    lines = [
        "# Final Training Readiness Summary",
        "",
        "## Ready Now",
        "",
        f"- **Synthea**: ready now. All {synthea['use_now_count']} reviewed rows land in `use_now`, matching the policy that clean Synthea rows should enter formal training immediately.",
        f"- **NHANES clean subset**: {nhanes['use_now_count']} rows are already usable now, while the remaining pending rows stay out of the immediate bucket until targeted adjudication is finished.",
        "",
        "## Targeted Adjudication Needed",
        "",
        f"- **NHANES**: {nhanes['use_after_revision_count']} rows belong in `use_after_revision`. This is the best next adjudication target because the queue is small and mostly repairable.",
        f"- **Official**: {official['use_after_revision_count']} rows are potentially salvageable after revision or adjudication, but the source still has a much heavier unresolved burden than NHANES.",
        f"- **GPT-expanded**: {gptx['use_after_revision_count']} rows are only tentatively salvageable. They should not be promoted until cleaner sources are finalized and the larger pending queue is materially reduced.",
        "",
        "## Do Not Use Yet",
        "",
        f"- **Official**: {official['exclude_for_now_count']} rows remain excluded for now because unresolved disagreements frequently involve unsupported facts or leakage-like concerns.",
        f"- **GPT-expanded**: {gptx['exclude_for_now_count']} rows are excluded for now under the conservative policy for large pending disagreement queues.",
        f"- **MIMIC/eICU demo**: all {mimic['exclude_for_now_count']} reviewed rows remain out of formal training. Even though agreement is clean, this source stays demo-only or very low-weight only.",
        "",
        "## Operational Recommendation",
        "",
        "Use Synthea immediately as the first formal training source. Add the clean NHANES subset now if you want a second source, but prioritize adjudicating the remaining NHANES queue before spending reviewer effort on Official or GPT-expanded.",
        "",
        "Keep Official in a controlled revision lane rather than broad deployment. Treat GPT-expanded as deferred source material: a few rows are individually clean, but the dataset line should not yet be treated as training-ready while so many pending rows remain unresolved.",
        "",
        "Do not use MIMIC/eICU as backbone training material; at most, reserve it for demo-only evaluation or a tiny low-weight realism subset under separate policy.",
        "",
        "This summary translates the existing agreement and adjudication outputs into an operational training recommendation without recomputing reviewer-agreement metrics.",
    ]
    (OUTPUT_DIR / "final_training_readiness_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    agreement = load_agreement_master()
    queues = queue_counts()
    master_rows = build_master_rows()

    write_csv(OUTPUT_DIR / "final_adjudication_master.csv", master_rows, OUTPUT_COLUMNS)

    for bucket_name, filename in [
        ("use_now", "training_use_now.csv"),
        ("use_after_revision", "training_use_after_revision.csv"),
        ("exclude_for_now", "training_exclude_for_now.csv"),
    ]:
        bucket_rows = [row for row in master_rows if row["preliminary_training_bucket"] == bucket_name]
        write_csv(OUTPUT_DIR / filename, bucket_rows, OUTPUT_COLUMNS)

    summary_rows = build_bucket_summary(master_rows)
    write_csv(
        OUTPUT_DIR / "training_bucket_summary.csv",
        summary_rows,
        ["dataset", "use_now_count", "use_after_revision_count", "exclude_for_now_count", "total_reviewed_rows"],
    )

    write_priority_plan(summary_rows, agreement, queues)
    write_training_readiness_summary(summary_rows, agreement)


if __name__ == "__main__":
    main()
