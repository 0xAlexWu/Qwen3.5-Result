#!/usr/bin/env python3
"""Build the reviewed paired-data expansion corpus.

The expansion unit is a finalized paired row.  The script never reads upstream
seed catalogs: it uses only the reviewed paired-data exports under
outputs/final_paired_data.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "outputs" / "final_paired_data"
OUT_DIR = ROOT / "outputs" / "final_expansion"

DATASETS = ["synthea", "official", "nhanes", "gpt_expanded", "mimic_eicu"]

TARGET_COUNTS = {
    "synthea": 1200,
    "official": 0,
    "nhanes": 600,
    "gpt_expanded": 200,
    "mimic_eicu": 0,
}

REQUIRED_FIELDS = [
    "final_pair_id",
    "source_dataset",
    "source_status",
    "original_pair_id",
    "original_candidate_id",
    "resource_type",
    "input_style",
    "input_text",
    "target_fhir_json",
    "expansion_origin",
    "expansion_method",
    "from_use_now_or_promoted",
    "notes",
]

PROMOTION_RISK_TERMS = (
    "unsupported_fact",
    "context_leakage",
    "possible_hallucination",
)

PROMOTION_REASON = (
    "Promoted under NHANES-only disposition rule: the row is Patient-only, "
    "the recorded issue is disposition-only/pending adjudication, and the "
    "source text already carries the demographic fragments preserved in the "
    "target."
)

PROMOTION_RISK_NOTE = (
    "No unsupported_fact, context_leakage, or possible_hallucination flag was "
    "present in notes/final_notes; expansion is limited to source-side "
    "wrapping/reformatting with target JSON preserved exactly."
)

LEAD_PHRASES = [
    "Finalized source",
    "Reviewed source",
    "Clinical input",
    "Input text",
    "Source fragment",
    "Paired-data input",
    "FHIR source",
    "Record text",
    "Training source",
    "Clinical fragment",
    "Source row",
    "Target-local source",
    "FHIR pairing source",
    "Source-only facts",
    "Structured source",
    "Minimal source",
    "Extraction source",
    "Source note",
    "Reviewed input",
    "Frozen source",
    "Accepted source",
    "Compact source",
    "Clinical source row",
    "Pair input",
    "Source statement",
    "Model input",
    "FHIR mapping source",
    "Governed source",
    "Conservative source",
    "Reviewed paired input",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def status_text(row: dict[str, str]) -> str:
    return " ".join(
        row.get(field, "")
        for field in ("review_status", "notes", "final_notes", "final_decision")
    ).lower()


def is_promoted(row: dict[str, str]) -> bool:
    if row.get("dataset") != "nhanes":
        return False
    if row.get("final_status") != "use_after_revision":
        return False
    if row.get("resource_type") != "Patient":
        return False
    text = status_text(row)
    if "disposition-only" not in text:
        return False
    return not any(term in text for term in PROMOTION_RISK_TERMS)


def split_clauses(text: str) -> list[str]:
    raw_parts = re.split(r"\s*[;|]\s*|\.\s+", text)
    parts = []
    for part in raw_parts:
        cleaned = part.strip().strip(".")
        if cleaned:
            parts.append(cleaned)
    return parts


def add_candidate(
    candidates: list[tuple[str, str, str]],
    seen: set[str],
    style: str,
    text: str,
    method: str,
    *,
    preserve_exact: bool = False,
) -> None:
    candidate = text if preserve_exact else normalize_space(text)
    if not candidate:
        return
    key = normalize_space(candidate).lower()
    if key in seen:
        return
    seen.add(key)
    candidates.append((style, candidate, method))


def source_variants(row: dict[str, str], needed: int) -> list[tuple[str, str, str]]:
    original = row["input_text"]
    resource = row["resource_type"]
    original_style = row["input_style"]
    normalized = normalize_space(original)
    clauses = split_clauses(normalized)

    candidates: list[tuple[str, str, str]] = []
    seen: set[str] = set()

    add_candidate(
        candidates,
        seen,
        original_style,
        original,
        "source_preserved",
        preserve_exact=True,
    )

    if len(clauses) > 1:
        joined_semicolon = "; ".join(clauses)
        joined_pipe = " | ".join(clauses)
        joined_slash = " / ".join(clauses)
        add_candidate(
            candidates,
            seen,
            "field_reformat",
            f"{resource} facts: {joined_semicolon}",
            "clause_reformat_semicolon",
        )
        add_candidate(
            candidates,
            seen,
            "field_reformat",
            f"{resource} facts | {joined_pipe}",
            "clause_reformat_pipe",
        )
        add_candidate(
            candidates,
            seen,
            "compact_clinical",
            f"{resource} source - {joined_slash}",
            "clause_reformat_slash",
        )
        add_candidate(
            candidates,
            seen,
            "record_fragment",
            f"Record fragment ({resource}): {joined_semicolon}",
            "clause_record_fragment",
        )
        if len(clauses) <= 8:
            reversed_join = "; ".join(reversed(clauses))
            add_candidate(
                candidates,
                seen,
                "field_reformat",
                f"{resource} facts: {reversed_join}",
                "clause_reformat_reverse_order",
            )

    for lead in LEAD_PHRASES:
        lead_key = re.sub(r"[^a-z0-9]+", "_", lead.lower()).strip("_")
        add_candidate(
            candidates,
            seen,
            "source_wrapper",
            f"{lead}: {normalized}",
            f"source_wrapper_{lead_key}",
        )
        add_candidate(
            candidates,
            seen,
            "record_fragment",
            f"{lead} ({resource}): {normalized}",
            f"resource_labeled_wrapper_{lead_key}",
        )
        add_candidate(
            candidates,
            seen,
            "compact_clinical",
            f"{resource} input - {normalized}",
            f"resource_input_wrapper_{lead_key}",
        )
        add_candidate(
            candidates,
            seen,
            "structured_prompt",
            f"{lead} for {resource}: {normalized}",
            f"resource_prompt_wrapper_{lead_key}",
        )

    if len(candidates) < needed:
        raise ValueError(
            f"Only generated {len(candidates)} variants for {row['dataset']} "
            f"{row['pair_id']}; need {needed}."
        )
    return candidates[:needed]


def allocate_counts(rows: list[dict[str, str]], target: int) -> dict[str, int]:
    if target == 0:
        return {}
    if not rows:
        raise ValueError(f"Cannot allocate target={target} with an empty row pool.")
    base = target // len(rows)
    remainder = target % len(rows)
    allocation = {}
    for index, row in enumerate(rows):
        allocation[row["pair_id"]] = base + (1 if index < remainder else 0)
    return allocation


def table(headers: list[str], rows: list[list[object]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_rows = read_csv(FINAL_DIR / "final_paired_data_summary.csv")
    summary = {row["dataset"]: row for row in summary_rows}

    source_pools: dict[str, list[dict[str, str]]] = defaultdict(list)
    promoted_rows: list[dict[str, str]] = []

    for dataset in DATASETS:
        for row in read_csv(FINAL_DIR / f"{dataset}_use_now.csv"):
            if row.get("final_status") != "use_now":
                continue
            row = dict(row)
            row["_expansion_source_status"] = "use_now"
            row["_promotion_reason"] = ""
            row["_promotion_risk_note"] = ""
            source_pools[dataset].append(row)

        for row in read_csv(FINAL_DIR / f"{dataset}_use_after_revision.csv"):
            if not is_promoted(row):
                continue
            row = dict(row)
            row["_expansion_source_status"] = "promoted_use_after_revision"
            row["_promotion_reason"] = PROMOTION_REASON
            row["_promotion_risk_note"] = PROMOTION_RISK_NOTE
            source_pools[dataset].append(row)
            promoted_rows.append(row)

    expanded: list[dict[str, str]] = []
    sequence = 1
    for dataset in DATASETS:
        target = TARGET_COUNTS[dataset]
        pool = source_pools[dataset]
        allocation = allocate_counts(pool, target)
        for row in pool:
            needed = allocation.get(row["pair_id"], 0)
            if needed == 0:
                continue
            variants = source_variants(row, needed)
            for variant_index, (style, input_text, method) in enumerate(variants, start=1):
                source_status = row["_expansion_source_status"]
                if method == "source_preserved":
                    origin = "finalized_paired_row_preserved"
                    note_tail = "Original paired input preserved exactly."
                else:
                    origin = "finalized_paired_row_source_side_variant"
                    note_tail = (
                        "Source-side wrapper/reformat only; no new clinical facts; "
                        "target JSON preserved exactly."
                    )
                if source_status == "promoted_use_after_revision":
                    note_tail = f"{note_tail} {PROMOTION_REASON}"
                notes = normalize_space(
                    " ".join(
                        part
                        for part in [
                            row.get("notes", ""),
                            row.get("final_notes", ""),
                            note_tail,
                        ]
                        if part
                    )
                )
                expanded.append(
                    {
                        "final_pair_id": f"train-final-{sequence:04d}",
                        "source_dataset": dataset,
                        "source_status": source_status,
                        "original_pair_id": row.get("pair_id", ""),
                        "original_candidate_id": row.get("candidate_id", ""),
                        "resource_type": row.get("resource_type", ""),
                        "input_style": style,
                        "input_text": input_text,
                        "target_fhir_json": row.get("target_fhir_json", ""),
                        "expansion_origin": origin,
                        "expansion_method": f"{method}__v{variant_index:03d}",
                        "from_use_now_or_promoted": source_status,
                        "notes": notes,
                    }
                )
                sequence += 1

    if len(expanded) != 2000:
        raise AssertionError(f"Expected 2000 rows, built {len(expanded)} rows.")
    if any(row["source_status"] == "exclude_for_now" for row in expanded):
        raise AssertionError("exclude_for_now row entered the expanded corpus.")
    if any(row["source_dataset"] == "mimic_eicu" for row in expanded):
        raise AssertionError("MIMIC/eICU rows entered the formal corpus.")

    write_csv(
        OUT_DIR / "expanded_paired_data_2000.csv",
        expanded,
        REQUIRED_FIELDS,
    )
    with (OUT_DIR / "expanded_paired_data_2000.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in expanded:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    promoted_manifest = [
        {
            "dataset": row["dataset"],
            "pair_id_or_candidate_id": row.get("pair_id") or row.get("candidate_id", ""),
            "original_status": row.get("final_status", ""),
            "promotion_reason": PROMOTION_REASON,
            "risk_note": PROMOTION_RISK_NOTE,
        }
        for row in promoted_rows
    ]
    write_csv(
        OUT_DIR / "promoted_use_after_revision_rows.csv",
        promoted_manifest,
        [
            "dataset",
            "pair_id_or_candidate_id",
            "original_status",
            "promotion_reason",
            "risk_note",
        ],
    )

    excluded_counter: Counter[tuple[str, str]] = Counter()
    promoted_ids = {(row["dataset"], row["pair_id"]) for row in promoted_rows}
    used_use_now_ids = {
        (row["source_dataset"], row["original_pair_id"])
        for row in expanded
        if row["source_status"] == "use_now"
    }
    for dataset in DATASETS:
        for row in read_csv(FINAL_DIR / f"{dataset}_final_paired_data.csv"):
            key = (dataset, row.get("pair_id", ""))
            final_status = row.get("final_status", "")
            source_status = row.get("source_status", "")
            if final_status == "exclude_for_now":
                if dataset == "mimic_eicu" or "demo" in source_status:
                    reason = "demo_only_or_exclude_for_now_not_retained"
                else:
                    reason = "exclude_for_now_not_allowed"
                excluded_counter[(dataset, reason)] += 1
            elif final_status == "unreviewed_clean_candidate":
                reason = "unreviewed_clean_candidate_not_in_formal_use_now_or_promoted_pool"
                excluded_counter[(dataset, reason)] += 1
            elif final_status == "use_now" and key not in used_use_now_ids:
                reason = "use_now_not_allocated_by_dataset_cap"
                excluded_counter[(dataset, reason)] += 1

        for row in read_csv(FINAL_DIR / f"{dataset}_use_after_revision.csv"):
            key = (dataset, row.get("pair_id", ""))
            if key in promoted_ids:
                continue
            if dataset == "official":
                reason = "use_after_revision_not_promoted_hidden_linkage_risk"
            elif dataset == "gpt_expanded":
                reason = "use_after_revision_not_promoted_gpt_adjudication_pending"
            else:
                reason = "use_after_revision_not_promoted"
            excluded_counter[(dataset, reason)] += 1

    excluded_rows = [
        {
            "dataset": dataset,
            "exclusion_reason": reason,
            "row_count": count,
        }
        for (dataset, reason), count in sorted(excluded_counter.items())
        if count
    ]
    write_csv(
        OUT_DIR / "excluded_rows_summary.csv",
        excluded_rows,
        ["dataset", "exclusion_reason", "row_count"],
    )

    plan_rows = []
    for dataset in DATASETS:
        source_count = len(source_pools[dataset])
        target = TARGET_COUNTS[dataset]
        promoted_count = sum(
            1
            for row in source_pools[dataset]
            if row["_expansion_source_status"] == "promoted_use_after_revision"
        )
        retained_demo = target if dataset == "mimic_eicu" and target else 0
        factor = (target / source_count) if source_count else 0
        if dataset == "synthea":
            rationale = (
                "Backbone scale source. Uses all Synthea use_now rows and expands "
                "aggressively through source-only wrappers/reformats with targets frozen."
            )
        elif dataset == "nhanes":
            rationale = (
                "Moderate semi-structured realism source. Uses all use_now rows and "
                "six Patient use_after_revision rows promoted only under the documented "
                "disposition-only rule."
            )
        elif dataset == "official":
            rationale = (
                "No formal contribution: there are no use_now rows, and the two revision "
                "rows were not promoted because target references such as subject/performer "
                "are not fully supported by the paired input."
            )
        elif dataset == "gpt_expanded":
            rationale = (
                "Capped auxiliary diversity source. Uses only the five use_now rows; "
                "unresolved GPT revision rows remain held out."
            )
        else:
            rationale = (
                "Excluded from formal 2,000-row corpus because all rows are demo-only or "
                "exclude_for_now; no low-weight realism subset retained."
            )
        plan_rows.append(
            {
                "dataset": dataset,
                "original_use_now_count": int(summary[dataset]["use_now_count"]),
                "original_use_after_revision_count": int(
                    summary[dataset]["use_after_revision_count"]
                ),
                "original_exclude_for_now_count": int(
                    summary[dataset]["exclude_for_now_count"]
                ),
                "promoted_use_after_revision_count": promoted_count,
                "retained_demo_only_count": retained_demo,
                "target_final_pair_count": target,
                "expansion_factor": f"{factor:.2f}",
                "rationale": rationale,
            }
        )
    write_csv(
        OUT_DIR / "expansion_plan_2000.csv",
        plan_rows,
        [
            "dataset",
            "original_use_now_count",
            "original_use_after_revision_count",
            "original_exclude_for_now_count",
            "promoted_use_after_revision_count",
            "retained_demo_only_count",
            "target_final_pair_count",
            "expansion_factor",
            "rationale",
        ],
    )

    dataset_counts = Counter(row["source_dataset"] for row in expanded)
    resource_counts = Counter(row["resource_type"] for row in expanded)
    input_style_counts = Counter(row["input_style"] for row in expanded)
    source_status_counts = Counter(row["from_use_now_or_promoted"] for row in expanded)

    diversity_md = "\n\n".join(
        [
            "# Expansion Diversity Summary",
            "Final size = 2,000 paired examples.",
            "## Dataset Contribution",
            table(
                ["dataset", "rows", "share"],
                [
                    [
                        dataset,
                        dataset_counts.get(dataset, 0),
                        f"{dataset_counts.get(dataset, 0) / 2000:.1%}",
                    ]
                    for dataset in DATASETS
                ],
            ),
            "## Resource Type Contribution",
            table(
                ["resource_type", "rows", "share"],
                [
                    [name, count, f"{count / 2000:.1%}"]
                    for name, count in sorted(resource_counts.items())
                ],
            ),
            "## Input Style Contribution",
            table(
                ["input_style", "rows", "share"],
                [
                    [name, count, f"{count / 2000:.1%}"]
                    for name, count in sorted(input_style_counts.items())
                ],
            ),
            "## Governance Source",
            table(
                ["source", "rows", "share"],
                [
                    [name, count, f"{count / 2000:.1%}"]
                    for name, count in sorted(source_status_counts.items())
                ],
            ),
            (
                "Rows derived from original use_now paired rows: "
                f"{source_status_counts.get('use_now', 0)}. Rows derived from "
                "promoted use_after_revision paired rows: "
                f"{source_status_counts.get('promoted_use_after_revision', 0)}."
            ),
            (
                "MIMIC/eICU retention: none. All MIMIC/eICU rows remain excluded from "
                "the formal corpus because the finalized layer marks them demo-only or "
                "exclude_for_now."
            ),
            (
                "GPT-expanded cap: 200 rows, exactly 10.0% of the final corpus. Only "
                "use_now GPT-expanded rows are used; no unresolved flagged GPT revision "
                "rows were promoted."
            ),
            (
                "Training balance: Synthea supplies the structural majority, NHANES "
                "adds a moderate semi-structured Observation/Patient realism subset, "
                "and GPT-expanded contributes capped auxiliary phrasing diversity. "
                "The corpus keeps Conditions, Patients, and Observations represented "
                "while preventing unreviewed, excluded, hidden-context, and demo-only "
                "rows from becoming backbone training data."
            ),
        ]
    )
    (OUT_DIR / "expansion_diversity_summary.md").write_text(
        diversity_md + "\n", encoding="utf-8"
    )

    guardrails_md = "\n\n".join(
        [
            "# Expansion Quality Guardrails",
            "## Allowed Expansion",
            (
                "The expansion pool contains finalized paired rows labeled use_now plus "
                "six explicitly promoted NHANES Patient rows from use_after_revision. "
                "Every expanded row preserves the original target_fhir_json string exactly. "
                "New rows change only the source side through deterministic wrappers or "
                "separator/field reformatting of the original input_text."
            ),
            "## Disallowed Expansion",
            (
                "Rows labeled exclude_for_now are never included. Unreviewed clean "
                "candidates are not treated as formal expansion sources. Official "
                "revision rows are not promoted because the target contains linked "
                "subject/performer context not fully stated in the input. GPT-expanded "
                "revision rows are not promoted because they remain flagged for explicit "
                "adjudication. MIMIC/eICU rows are not retained because the finalized "
                "layer marks them demo-only/exclude_for_now."
            ),
            "## Unsupported-Fact And Context-Leakage Control",
            (
                "Promotion requires absence of unsupported_fact, context_leakage, and "
                "possible_hallucination terms in notes and final_notes. The only promoted "
                "rows are NHANES Patient rows whose issue is recorded as disposition-only. "
                "Expansion text is derived from the original paired input_text, not from "
                "upstream seeds or raw candidate catalogs, and target JSON is never enriched."
            ),
            "## Near-Duplicate Inflation Control",
            (
                "Near-duplicate expansion is tracked by original_pair_id, expansion_origin, "
                "and expansion_method. Each source row keeps one exact preserved source row; "
                "additional rows are deterministic source wrappers or clause reformats. "
                "Dataset caps limit GPT-expanded to 10% and exclude MIMIC/eICU entirely."
            ),
            "## Unit-Sensitive Observation Handling",
            (
                "Observation variants do not recalculate or convert values. Since the "
                "source side is wrapped/reformatted rather than numerically rewritten, "
                "measure identity, numeric value, and unit strings remain as stated in "
                "the accepted paired input."
            ),
            "## Governance Continuity",
            (
                "This build respects the reviewed paired-data governance layer by expanding "
                "from finalized paired rows rather than seed catalogs, documenting every "
                "promotion, retaining exact targets, excluding current exclude_for_now rows, "
                "and writing a separate exclusion summary for held-out finalized rows."
            ),
        ]
    )
    (OUT_DIR / "expansion_quality_guardrails.md").write_text(
        guardrails_md + "\n", encoding="utf-8"
    )

    print("Built expanded corpus:")
    print(f"  rows: {len(expanded)}")
    print(f"  datasets: {dict(dataset_counts)}")
    print(f"  source statuses: {dict(source_status_counts)}")
    print(f"  output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
