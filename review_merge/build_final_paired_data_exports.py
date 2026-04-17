from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "outputs" / "review_merge"
FINAL_DIR = ROOT / "outputs" / "final_paired_data"
UPSTREAM_ROOT = ROOT / "upstream_repos"

DATASET_CONFIG = {
    "synthea": {
        "csv_paths": [
            UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_pilot50_pair_candidates.csv",
            UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_remaining70_pair_candidates.csv",
        ],
        "jsonl_paths": [
            UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_pilot50_pair_candidates.jsonl",
            UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_remaining70_pair_candidates.jsonl",
        ],
        "prompt_glob": UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "reviewer_batch_prompts",
        "default_source_status": "",
        "repo_name": "FHIR-Synthea-Seeds",
    },
    "official": {
        "csv_paths": [
            UPSTREAM_ROOT / "FHIR-Official-Seeds" / "outputs" / "official" / "official_pilot12_pair_candidates.csv",
        ],
        "jsonl_paths": [
            UPSTREAM_ROOT / "FHIR-Official-Seeds" / "outputs" / "official" / "official_pilot12_pair_candidates.jsonl",
        ],
        "prompt_glob": UPSTREAM_ROOT / "FHIR-Official-Seeds" / "outputs" / "reviewer_batch_prompts",
        "default_source_status": "",
        "repo_name": "FHIR-Official-Seeds",
    },
    "nhanes": {
        "csv_paths": [
            UPSTREAM_ROOT / "FHIR-NHANES-Seeds" / "outputs" / "nhanes" / "nhanes_pilot15_pair_candidates.csv",
        ],
        "jsonl_paths": [
            UPSTREAM_ROOT / "FHIR-NHANES-Seeds" / "outputs" / "nhanes" / "nhanes_pilot15_pair_candidates.jsonl",
        ],
        "prompt_glob": None,
        "default_source_status": "",
        "repo_name": "FHIR-NHANES-Seeds",
    },
    "gpt_expanded": {
        "csv_paths": [
            UPSTREAM_ROOT / "FHIR-GPT-Seeds" / "outputs" / "gpt_expanded" / "gpt_expanded_pair_candidates.csv",
        ],
        "jsonl_paths": [
            UPSTREAM_ROOT / "FHIR-GPT-Seeds" / "outputs" / "gpt_expanded" / "gpt_expanded_pair_candidates.jsonl",
        ],
        "prompt_glob": None,
        "default_source_status": "",
        "repo_name": "FHIR-GPT-Seeds",
    },
    "mimic_eicu": {
        "csv_paths": [
            UPSTREAM_ROOT / "MIMIC-eICU-Seeds" / "outputs" / "mimic_eicu" / "demo_pair_pilot" / "demo_pair_candidates.csv",
        ],
        "jsonl_paths": [
            UPSTREAM_ROOT / "MIMIC-eICU-Seeds" / "outputs" / "mimic_eicu" / "demo_pair_pilot" / "demo_pair_candidates.jsonl",
        ],
        "prompt_glob": None,
        "default_source_status": "demo_only",
        "repo_name": "MIMIC-eICU-Seeds",
    },
}

FINAL_COLUMNS = [
    "dataset",
    "pair_id",
    "candidate_id",
    "seed_id",
    "canonical_seed_id",
    "source_origin",
    "source_file",
    "resource_type",
    "input_style",
    "input_text",
    "target_fhir_json",
    "target_seed_file",
    "review_status",
    "notes",
    "final_status",
    "final_decision",
    "final_notes",
    "source_status",
]

SUMMARY_COLUMNS = [
    "dataset",
    "total_original_pairs",
    "use_now_count",
    "use_after_revision_count",
    "exclude_for_now_count",
    "unreviewed_clean_candidate_count",
]

UNMATCHED_REVIEW_COLUMNS = [
    "dataset",
    "pair_id_or_candidate_id",
    "preliminary_training_bucket",
    "final_decision",
    "final_notes",
    "match_reason",
]


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).lstrip("\ufeff"): (value or "") for key, value in row.items()}


def norm(value: str | None) -> str:
    return (value or "").strip()


def low(value: str | None) -> str:
    return norm(value).lower()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


def read_jsonl_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            normalized: dict[str, str] = {}
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    normalized[key] = json.dumps(value, ensure_ascii=False, indent=2)
                elif value is None:
                    normalized[key] = ""
                else:
                    normalized[key] = str(value)
            rows.append(normalize_row(normalized))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = {field: row.get(field, "") for field in fieldnames}
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")


def first_identifier(row: dict[str, str]) -> str:
    return norm(row.get("pair_id")) or norm(row.get("candidate_id"))


def parse_reviewer_prompt_file(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict[str, str]] = []
    cursor = 0

    while True:
        pair_idx = text.find("pair_id:", cursor)
        if pair_idx == -1:
            break
        resource_idx = text.find("\nresource_type:", pair_idx)
        style_idx = text.find("\ninput_style:", resource_idx)
        input_marker = text.find("\ninput_text:\n", style_idx)
        target_marker = text.find("\ntarget_fhir_json:\n", input_marker)
        if min(resource_idx, style_idx, input_marker, target_marker) == -1:
            break

        pair_id = text[pair_idx + len("pair_id:"):resource_idx].strip()
        resource_type = text[resource_idx + len("\nresource_type:"):style_idx].strip()
        input_style = text[style_idx + len("\ninput_style:"):input_marker].strip()
        input_text = text[input_marker + len("\ninput_text:\n"):target_marker].strip()

        trailing = text[target_marker + len("\ntarget_fhir_json:\n"):]
        stripped = trailing.lstrip()
        leading_ws = len(trailing) - len(stripped)
        _, end_idx = decoder.raw_decode(stripped)
        target_text = stripped[:end_idx]

        rows.append(
            {
                "pair_id": pair_id,
                "resource_type": resource_type,
                "input_style": input_style,
                "input_text": input_text,
                "target_fhir_json": target_text,
            }
        )
        cursor = target_marker + len("\ntarget_fhir_json:\n") + leading_ws + end_idx

    return rows


def merge_rows(base: dict[str, str], incoming: dict[str, str]) -> None:
    for key, value in incoming.items():
        if key not in base or not norm(base.get(key)):
            base[key] = value
        elif key == "target_fhir_json" and norm(value):
            base[key] = value


def load_upstream_dataset_rows(dataset: str) -> tuple[list[dict[str, str]], list[str]]:
    config = DATASET_CONFIG[dataset]
    merged: dict[str, dict[str, str]] = {}
    sources: list[str] = []

    for path in config["csv_paths"]:
        if not path.exists():
            continue
        sources.append(str(path.relative_to(ROOT)))
        for row in read_csv_rows(path):
            identifier = first_identifier(row)
            if not identifier:
                continue
            row["source_file"] = str(path.relative_to(ROOT))
            if "source_status" not in row:
                row["source_status"] = config["default_source_status"]
            merge_rows(merged.setdefault(identifier, {}), row)

    for path in config["jsonl_paths"]:
        if not path.exists():
            continue
        sources.append(str(path.relative_to(ROOT)))
        for row in read_jsonl_rows(path):
            identifier = first_identifier(row)
            if not identifier:
                continue
            row.setdefault("source_file", str(path.relative_to(ROOT)))
            if "source_status" not in row:
                row["source_status"] = config["default_source_status"]
            merge_rows(merged.setdefault(identifier, {}), row)

    prompt_glob = config["prompt_glob"]
    if prompt_glob:
        prompt_dir = Path(prompt_glob)
        prompt_pattern = "*.txt"
        prompt_files = sorted(prompt_dir.glob(prompt_pattern))
        used_prompt_source = False
        for path in prompt_files:
            parsed_rows = parse_reviewer_prompt_file(path)
            if parsed_rows and not used_prompt_source:
                sources.append(str((prompt_dir / prompt_pattern).relative_to(ROOT)))
                used_prompt_source = True
            for row in parsed_rows:
                identifier = first_identifier(row)
                if not identifier:
                    continue
                merge_rows(merged.setdefault(identifier, {}), row)

    ordered_rows = [merged[key] for key in sorted(merged)]
    return ordered_rows, sources


def load_review_layer() -> tuple[dict[tuple[str, str], dict[str, str]], dict[tuple[str, str], str], list[dict[str, str]]]:
    bucket_map: dict[tuple[str, str], str] = {}
    review_union: dict[tuple[str, str], dict[str, str]] = {}

    for filename, status in [
        ("training_use_now.csv", "use_now"),
        ("training_use_after_revision.csv", "use_after_revision"),
        ("training_exclude_for_now.csv", "exclude_for_now"),
    ]:
        rows = read_csv_rows(REVIEW_DIR / filename)
        for row in rows:
            key = (low(row.get("dataset")), norm(row.get("pair_id_or_candidate_id")))
            bucket_map[key] = status
            review_union[key] = row

    final_master = read_csv_rows(REVIEW_DIR / "final_adjudication_master.csv")
    final_master_map = {
        (low(row.get("dataset")), norm(row.get("pair_id_or_candidate_id"))): row for row in final_master
    }
    return final_master_map, bucket_map, final_master


def build_final_rows_for_dataset(
    dataset: str,
    upstream_rows: list[dict[str, str]],
    final_master_map: dict[tuple[str, str], dict[str, str]],
    bucket_map: dict[tuple[str, str], str],
) -> list[dict[str, str]]:
    final_rows: list[dict[str, str]] = []

    for row in upstream_rows:
        pair_id = norm(row.get("pair_id"))
        candidate_id = norm(row.get("candidate_id"))
        identifier = pair_id or candidate_id
        review_key = (dataset, identifier)
        final_status = bucket_map.get(review_key, "unreviewed_clean_candidate")
        review_row = final_master_map.get(review_key, {})

        final_rows.append(
            {
                "dataset": dataset,
                "pair_id": pair_id,
                "candidate_id": candidate_id,
                "seed_id": norm(row.get("seed_id")),
                "canonical_seed_id": norm(row.get("canonical_seed_id")),
                "source_origin": norm(row.get("source_origin") or row.get("source_dataset")),
                "source_file": norm(row.get("source_file")),
                "resource_type": norm(row.get("resource_type")),
                "input_style": norm(row.get("input_style")),
                "input_text": row.get("input_text", ""),
                "target_fhir_json": row.get("target_fhir_json", ""),
                "target_seed_file": norm(row.get("target_seed_file")),
                "review_status": norm(row.get("review_status")),
                "notes": row.get("notes", ""),
                "final_status": final_status,
                "final_decision": norm(review_row.get("final_decision")),
                "final_notes": review_row.get("final_notes", ""),
                "source_status": norm(row.get("source_status") or DATASET_CONFIG[dataset]["default_source_status"]),
            }
        )

    return final_rows


def build_unmatched_review_rows(
    final_master_rows: list[dict[str, str]],
    upstream_indices: dict[str, set[str]],
) -> list[dict[str, str]]:
    unmatched: list[dict[str, str]] = []
    for row in final_master_rows:
        dataset = low(row.get("dataset"))
        identifier = norm(row.get("pair_id_or_candidate_id"))
        if identifier not in upstream_indices.get(dataset, set()):
            unmatched.append(
                {
                    "dataset": dataset,
                    "pair_id_or_candidate_id": identifier,
                    "preliminary_training_bucket": norm(row.get("preliminary_training_bucket")),
                    "final_decision": norm(row.get("final_decision")),
                    "final_notes": row.get("final_notes", ""),
                    "match_reason": "review row not found in upstream paired-candidate tables",
                }
            )
    return unmatched


def subset_rows(rows: list[dict[str, str]], status: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("final_status") == status]


def write_dataset_outputs(dataset: str, rows: list[dict[str, str]]) -> None:
    frozen_rows = [row for row in rows if row.get("final_status") != "use_after_revision"]
    write_csv(FINAL_DIR / f"{dataset}_final_paired_data.csv", frozen_rows, FINAL_COLUMNS)
    write_jsonl(FINAL_DIR / f"{dataset}_final_paired_data.jsonl", frozen_rows, FINAL_COLUMNS)

    for status in ["use_now", "use_after_revision", "exclude_for_now", "unreviewed_clean_candidate"]:
        subset = subset_rows(rows, status)
        write_csv(FINAL_DIR / f"{dataset}_{status}.csv", subset, FINAL_COLUMNS)


def build_summary_rows(dataset_rows: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for dataset in DATASET_CONFIG:
        entries = dataset_rows[dataset]
        counter = Counter(row["final_status"] for row in entries)
        rows.append(
            {
                "dataset": dataset,
                "total_original_pairs": str(len(entries)),
                "use_now_count": str(counter["use_now"]),
                "use_after_revision_count": str(counter["use_after_revision"]),
                "exclude_for_now_count": str(counter["exclude_for_now"]),
                "unreviewed_clean_candidate_count": str(counter["unreviewed_clean_candidate"]),
            }
        )
    return rows


def write_summary_markdown(
    summary_rows: list[dict[str, str]],
    upstream_sources: dict[str, list[str]],
    unmatched_review_rows: list[dict[str, str]],
) -> None:
    lines = [
        "# Final Paired Data Summary",
        "",
        "These exports reconcile the original upstream paired-candidate repositories with the downstream post-review governance decisions from `summary-human-judgement`.",
        "",
        "## Source Repositories",
        "",
    ]

    for dataset in DATASET_CONFIG:
        repo_name = DATASET_CONFIG[dataset]["repo_name"]
        sources = upstream_sources.get(dataset) or []
        source_text = ", ".join(f"`{source}`" for source in sources) if sources else "`not found`"
        lines.append(f"- `{dataset}` paired candidates came from `{repo_name}` via {source_text}.")

    lines.extend(
        [
            "",
            "## Review Reconciliation",
            "",
            "- `summary-human-judgement` supplied the post-review bucket files and final adjudication table.",
            "- Rows appearing in `training_use_now.csv` were labeled `use_now`.",
            "- Rows appearing in `training_use_after_revision.csv` were labeled `use_after_revision`.",
            "- Rows appearing in `training_exclude_for_now.csv` were labeled `exclude_for_now`.",
            "- Any original upstream paired candidate absent from all review bucket files was labeled `unreviewed_clean_candidate`.",
            "- Counts in these final dataset exports are reported at unique upstream paired-candidate granularity. If multiple review rows point to the same `dataset + pair_id`, they reconcile onto one frozen upstream pair row rather than being duplicated.",
            "- The main `*_final_paired_data.csv/.jsonl` exports intentionally exclude `use_after_revision` rows; those rows remain available only in the separate `*_use_after_revision.csv` subsets.",
            "",
            "## Operational Meaning",
            "",
            "- `use_now` rows are the currently frozen training-ready subset.",
            "- `use_after_revision` rows remain potentially salvageable after adjudication or targeted cleanup, but are held out of the frozen main dataset exports.",
            "- `exclude_for_now` rows are outside the current formal training set.",
            "- `unreviewed_clean_candidate` rows were not part of the reviewed anomaly subset and remain outside the reviewed frozen subset unless explicitly promoted later.",
            "- `mimic_eicu` remains demo-only even where rows appear clean; the exports preserve `source_status = demo_only` rather than upgrading them into a backbone source.",
            "",
            "## Counts",
            "",
            "| Dataset | Total original pairs | use_now | use_after_revision | exclude_for_now | unreviewed_clean_candidate |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for row in summary_rows:
        lines.append(
            f"| {row['dataset']} | {row['total_original_pairs']} | {row['use_now_count']} | {row['use_after_revision_count']} | {row['exclude_for_now_count']} | {row['unreviewed_clean_candidate_count']} |"
        )

    lines.extend(["", "## Unmatched Review Rows", ""])
    if unmatched_review_rows:
        lines.append(
            f"- {len(unmatched_review_rows)} reviewed rows could not be matched back to upstream paired candidates; see `unmatched_review_rows.csv`."
        )
    else:
        lines.append("- None. All reviewed rows matched an upstream paired candidate.")

    (FINAL_DIR / "final_paired_data_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    final_master_map, bucket_map, final_master_rows = load_review_layer()
    dataset_rows: dict[str, list[dict[str, str]]] = {}
    upstream_sources: dict[str, list[str]] = {}
    upstream_indices: dict[str, set[str]] = {}

    for dataset in DATASET_CONFIG:
        upstream_rows, sources = load_upstream_dataset_rows(dataset)
        upstream_sources[dataset] = sources
        upstream_indices[dataset] = {first_identifier(row) for row in upstream_rows if first_identifier(row)}
        final_rows = build_final_rows_for_dataset(dataset, upstream_rows, final_master_map, bucket_map)
        dataset_rows[dataset] = final_rows
        write_dataset_outputs(dataset, final_rows)

    unmatched_review_rows = build_unmatched_review_rows(final_master_rows, upstream_indices)
    write_csv(FINAL_DIR / "unmatched_review_rows.csv", unmatched_review_rows, UNMATCHED_REVIEW_COLUMNS)

    summary_rows = build_summary_rows(dataset_rows)
    write_csv(FINAL_DIR / "final_paired_data_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_summary_markdown(summary_rows, upstream_sources, unmatched_review_rows)


if __name__ == "__main__":
    main()
