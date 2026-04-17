from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "review_merge"
UPSTREAM_ROOT = ROOT / "upstream_repos"

TRAINING_USE_NOW = OUTPUT_DIR / "training_use_now.csv"

REVIEW_TABLE_CANDIDATES = {
    "synthea": [
        OUTPUT_DIR / "synthea_review_merge.csv",
        ROOT / "review_merge" / "synthea_review_merge.csv",
    ],
    "official": [
        OUTPUT_DIR / "official_review_merge.csv",
        ROOT / "review_merge" / "official_review_merge.csv",
    ],
    "nhanes": [
        OUTPUT_DIR / "nhanes_review_merge.csv",
        ROOT / "review_merge" / "nhanes_review_merge.csv",
    ],
    "gpt_expanded": [
        OUTPUT_DIR / "gpt_expanded_review_merge.csv",
        ROOT / "review_merge" / "gpt_expanded_review_merge.csv",
    ],
    "mimic_eicu": [
        OUTPUT_DIR / "mimic_eicu_review_merge.csv",
        ROOT / "review_merge" / "mimic_eicu_review_merge.csv",
    ],
}

UPSTREAM_CONTENT_FILES = {
    "nhanes": [
        UPSTREAM_ROOT / "FHIR-NHANES-Seeds" / "outputs" / "nhanes" / "nhanes_pilot15_pair_candidates.csv",
    ],
    "gpt_expanded": [
        UPSTREAM_ROOT / "FHIR-GPT-Seeds" / "outputs" / "gpt_expanded" / "gpt_expanded_pair_candidates.csv",
    ],
}

SYNTHEA_PAIR_CANDIDATES = [
    UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_pilot50_pair_candidates.csv",
    UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "synthea_remaining70_pair_candidates.csv",
]

SYNTHEA_REVIEWER_PROMPTS = sorted(
    (UPSTREAM_ROOT / "FHIR-Synthea-Seeds" / "outputs" / "large" / "reviewer_batch_prompts").glob("review_batch_*.txt")
)

EXPORT_COLUMNS = [
    "dataset",
    "pair_id_or_candidate_id",
    "pair_id",
    "candidate_id",
    "resource_type",
    "input_style",
    "input_text",
    "target_fhir_json",
    "seed_id",
    "canonical_seed_id",
    "source_origin",
    "target_seed_file",
    "source_file",
    "merged_decision",
    "preliminary_training_bucket",
    "final_decision",
    "final_notes",
]

UNMATCHED_COLUMNS = EXPORT_COLUMNS + [
    "match_status",
    "review_match_found",
    "content_match_found",
]


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    return {str(key).lstrip("\ufeff"): (value or "") for key, value in row.items()}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [normalize_row(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def norm(value: str | None) -> str:
    return (value or "").strip()


def low(value: str | None) -> str:
    return norm(value).lower()


def row_identifier(row: dict[str, str]) -> str:
    return norm(row.get("pair_id")) or norm(row.get("candidate_id")) or norm(row.get("pair_id_or_candidate_id"))


def index_rows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        for key in {norm(row.get("pair_id")), norm(row.get("candidate_id"))}:
            if key:
                index[key].append(row)
    return index


def candidate_score(training_row: dict[str, str], source_row: dict[str, str]) -> tuple[int, int, int, int]:
    score = 0
    if norm(training_row.get("disagreement_summary")) and norm(training_row.get("disagreement_summary")) == norm(source_row.get("disagreement_summary")):
        score += 16
    if norm(training_row.get("merged_decision")) and norm(training_row.get("merged_decision")) == norm(source_row.get("merged_decision")):
        score += 8
    if norm(training_row.get("final_decision")) and norm(training_row.get("final_decision")) == norm(source_row.get("final_decision")):
        score += 4
    if norm(training_row.get("preliminary_training_bucket")) == "use_now" and low(source_row.get("adjudication_needed")) == "no":
        score += 2
    return (
        score,
        1 if norm(source_row.get("input_text")) else 0,
        1 if norm(source_row.get("target_fhir_json")) else 0,
        0,
    )


def choose_best_match(training_row: dict[str, str], candidates: list[dict[str, str]]) -> dict[str, str] | None:
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda row: candidate_score(training_row, row), reverse=True)
    return ranked[0]


def get_from_first(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = norm(row.get(key))
        if value:
            return value
    return ""


def parse_synthea_prompt_file(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    rows: list[dict[str, str]] = []
    decoder = json.JSONDecoder()
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

        json_block = text[target_marker + len("\ntarget_fhir_json:\n"):]
        stripped = json_block.lstrip()
        leading_whitespace = len(json_block) - len(stripped)
        _, end_index = decoder.raw_decode(stripped)
        target_fhir_json = stripped[:end_index]

        rows.append(
            {
                "pair_id": pair_id,
                "resource_type": resource_type,
                "input_style": input_style,
                "input_text": input_text,
                "target_fhir_json": target_fhir_json,
                "source_file": str(path.relative_to(ROOT)),
            }
        )
        cursor = target_marker + len("\ntarget_fhir_json:\n") + leading_whitespace + end_index

    return rows


def load_synthea_content_rows() -> tuple[list[dict[str, str]], list[str]]:
    merged: dict[str, dict[str, str]] = {}
    used_sources: list[str] = []
    used_prompt_source = False

    for path in SYNTHEA_PAIR_CANDIDATES:
        if not path.exists():
            continue
        used_sources.append(str(path.relative_to(ROOT)))
        for row in read_csv_rows(path):
            pair_id = norm(row.get("pair_id"))
            if not pair_id:
                continue
            merged.setdefault(pair_id, {}).update(row)
            merged[pair_id].setdefault("source_file", str(path.relative_to(ROOT)))

    for path in SYNTHEA_REVIEWER_PROMPTS:
        if not path.exists():
            continue
        parsed_rows = parse_synthea_prompt_file(path)
        if parsed_rows and not used_prompt_source:
            used_sources.append("upstream_repos/FHIR-Synthea-Seeds/outputs/large/reviewer_batch_prompts/*.txt")
            used_prompt_source = True
        for row in parsed_rows:
            pair_id = norm(row.get("pair_id"))
            if not pair_id:
                continue
            merged.setdefault(pair_id, {}).update(row)

    return list(merged.values()), used_sources


def load_upstream_content_rows() -> tuple[dict[str, list[dict[str, str]]], dict[str, list[str]]]:
    content_rows: dict[str, list[dict[str, str]]] = {"synthea": [], "nhanes": [], "gpt_expanded": [], "official": [], "mimic_eicu": []}
    content_sources: dict[str, list[str]] = {dataset: [] for dataset in content_rows}

    synthea_rows, synthea_sources = load_synthea_content_rows()
    content_rows["synthea"] = synthea_rows
    content_sources["synthea"] = synthea_sources

    for dataset, paths in UPSTREAM_CONTENT_FILES.items():
        loaded_rows: list[dict[str, str]] = []
        used_sources: list[str] = []
        for path in paths:
            if not path.exists():
                continue
            used_sources.append(str(path.relative_to(ROOT)))
            rows = read_csv_rows(path)
            for row in rows:
                row["source_file"] = str(path.relative_to(ROOT))
            loaded_rows.extend(rows)
        content_rows[dataset] = loaded_rows
        content_sources[dataset] = used_sources

    return content_rows, content_sources


def build_export_row(
    training_row: dict[str, str],
    review_row: dict[str, str] | None,
    content_row: dict[str, str] | None,
    review_source_file: str,
) -> dict[str, str]:
    source_row = content_row or review_row or {}
    pair_id_or_candidate_id = norm(training_row.get("pair_id_or_candidate_id"))

    export_row = {
        "dataset": norm(training_row.get("dataset")),
        "pair_id_or_candidate_id": pair_id_or_candidate_id,
        "pair_id": get_from_first(source_row, ["pair_id"]),
        "candidate_id": get_from_first(source_row, ["candidate_id"]),
        "resource_type": get_from_first(source_row, ["resource_type"]),
        "input_style": get_from_first(source_row, ["input_style"]),
        "input_text": get_from_first(source_row, ["input_text"]),
        "target_fhir_json": get_from_first(source_row, ["target_fhir_json"]),
        "seed_id": get_from_first(source_row, ["seed_id"]),
        "canonical_seed_id": get_from_first(source_row, ["canonical_seed_id"]),
        "source_origin": get_from_first(source_row, ["source_origin", "source_dataset"]),
        "target_seed_file": get_from_first(source_row, ["target_seed_file"]),
        "source_file": get_from_first(source_row, ["source_file"]) or review_source_file,
        "merged_decision": norm(training_row.get("merged_decision")),
        "preliminary_training_bucket": norm(training_row.get("preliminary_training_bucket")),
        "final_decision": norm(training_row.get("final_decision")),
        "final_notes": norm(training_row.get("final_notes")),
    }

    if not export_row["pair_id"]:
        export_row["pair_id"] = pair_id_or_candidate_id if "__" in pair_id_or_candidate_id or pair_id_or_candidate_id.startswith(("NHANES-", "gptx-", "official-", "pilot", "remaining", "demo-")) else ""
    if not export_row["candidate_id"] and review_row:
        export_row["candidate_id"] = get_from_first(review_row, ["candidate_id"])

    return export_row


def match_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, str], dict[str, list[str]]]:
    training_rows = read_csv_rows(TRAINING_USE_NOW)

    review_paths = {dataset: first_existing(paths) for dataset, paths in REVIEW_TABLE_CANDIDATES.items()}
    review_rows = {dataset: read_csv_rows(path) if path else [] for dataset, path in review_paths.items()}
    review_indices = {dataset: index_rows(rows) for dataset, rows in review_rows.items()}

    content_rows, content_sources = load_upstream_content_rows()
    content_indices = {dataset: index_rows(rows) for dataset, rows in content_rows.items()}

    export_rows: list[dict[str, str]] = []
    unmatched_rows: list[dict[str, str]] = []

    for training_row in training_rows:
        dataset = low(training_row.get("dataset"))
        identifier = norm(training_row.get("pair_id_or_candidate_id"))

        review_candidates = review_indices.get(dataset, {}).get(identifier, [])
        content_candidates = content_indices.get(dataset, {}).get(identifier, [])

        review_match = choose_best_match(training_row, review_candidates)
        content_match = choose_best_match(training_row, content_candidates)

        export_row = build_export_row(
            training_row=training_row,
            review_row=review_match,
            content_row=content_match,
            review_source_file=str(review_paths.get(dataset).relative_to(ROOT)) if review_paths.get(dataset) else "",
        )
        export_rows.append(export_row)

        fully_recovered = bool(export_row["input_text"] and export_row["target_fhir_json"])
        if not fully_recovered:
            if not review_match and not content_match:
                status = "no_source_match"
            elif review_match and not content_match:
                status = "matched_review_only_missing_upstream_pair_content"
            else:
                status = "matched_upstream_or_review_but_pair_content_incomplete"

            unmatched_rows.append(
                {
                    **export_row,
                    "match_status": status,
                    "review_match_found": "yes" if review_match else "no",
                    "content_match_found": "yes" if content_match else "no",
                }
            )

    review_report = {dataset: str(path.relative_to(ROOT)) if path else "" for dataset, path in review_paths.items()}
    return export_rows, unmatched_rows, review_report, content_sources


def write_summary(
    export_rows: list[dict[str, str]],
    unmatched_rows: list[dict[str, str]],
    review_paths: dict[str, str],
    content_sources: dict[str, list[str]],
) -> None:
    total_rows = len(export_rows)
    full_content_matches = sum(1 for row in export_rows if row["input_text"] and row["target_fhir_json"])
    missing_input_text = sum(1 for row in export_rows if not row["input_text"])
    missing_target_fhir_json = sum(1 for row in export_rows if not row["target_fhir_json"])
    datasets = Counter(row["dataset"] for row in export_rows)
    unmatched_ids = [f"{row['dataset']}:{row['pair_id_or_candidate_id']}" for row in unmatched_rows]

    lines = [
        "# Complete Training Use Now Summary",
        "",
        f"- Total rows in `training_use_now.csv`: **{total_rows}**",
        f"- Total rows successfully matched back to full paired content (`input_text` + `target_fhir_json` both recovered): **{full_content_matches}**",
        f"- Rows with missing `input_text`: **{missing_input_text}**",
        f"- Rows with missing `target_fhir_json`: **{missing_target_fhir_json}**",
        f"- Rows not fully matched back to raw paired content: **{len(unmatched_rows)}**",
        "",
        "## Dataset Contribution",
        "",
    ]

    for dataset, count in sorted(datasets.items()):
        lines.append(f"- `{dataset}`: {count} rows")

    lines.extend(
        [
            "",
            "## Source Tables Used",
            "",
        ]
    )

    for dataset in sorted(REVIEW_TABLE_CANDIDATES):
        review_path = review_paths.get(dataset) or "not found"
        upstream_paths = content_sources.get(dataset) or []
        upstream_text = ", ".join(f"`{path}`" for path in upstream_paths) if upstream_paths else "`not found`"
        lines.append(f"- `{dataset}` review table: `{review_path}`; upstream paired-content sources: {upstream_text}")

    lines.extend(
        [
            "",
            "## Unmatched Or Partial Rows",
            "",
        ]
    )

    if unmatched_rows:
        lines.append("Rows are preserved in `complete_training_use_now.csv` and also listed in `complete_training_use_now_unmatched.csv`.")
        lines.append("")
        for row in unmatched_rows:
            lines.append(
                f"- `{row['dataset']}:{row['pair_id_or_candidate_id']}` -> `{row['match_status']}`"
            )
    else:
        lines.append("- None")

    (OUTPUT_DIR / "complete_training_use_now_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    export_rows, unmatched_rows, review_paths, content_sources = match_rows()

    write_csv(OUTPUT_DIR / "complete_training_use_now.csv", export_rows, EXPORT_COLUMNS)
    write_csv(OUTPUT_DIR / "complete_training_use_now_unmatched.csv", unmatched_rows, UNMATCHED_COLUMNS)
    write_summary(export_rows, unmatched_rows, review_paths, content_sources)


if __name__ == "__main__":
    main()
