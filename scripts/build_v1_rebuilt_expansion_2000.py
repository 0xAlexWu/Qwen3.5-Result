#!/usr/bin/env python3
"""Build the v1 formal 2,000-example paired-data expansion corpus.

This rebuild uses the finalized paired-data exports plus post-review governance
outputs.  It broadens the source base to clean finalized paired candidates while
still excluding unsafe reviewed rows, and keeps MIMIC/eICU as an explicitly
tagged tiny demo-only realism subset.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "outputs" / "final_paired_data"
GOV_DIR = ROOT / "outputs" / "review_merge"
OUT_DIR = ROOT / "outputs" / "final_expansion"

DATASETS = ["synthea", "official", "nhanes", "gpt_expanded", "mimic_eicu"]

TARGET_COUNTS = {
    "synthea": 1240,
    "nhanes": 430,
    "official": 120,
    "gpt_expanded": 196,
    "mimic_eicu": 14,
}

OUTPUT_FIELDS = [
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
    "source_pool_label",
    "notes",
]

RISK_TERMS = (
    "unsupported_fact",
    "context_leakage",
    "possible_hallucination",
)

NHANES_PROMOTION_REASON = (
    "Promoted under NHANES disposition-only rule: Patient row, pending "
    "adjudication only because reviewers differed on disposition, with no "
    "unsupported_fact, context_leakage, or possible_hallucination flag."
)

NHANES_PROMOTION_RISK_NOTE = (
    "Expansion uses only source-side conservative style variation and preserves "
    "the original target FHIR JSON exactly."
)

MIMIC_EXCEPTION_LABEL = (
    "mandatory_demo_only_low_weight_exception_from_review_keep_exclude_bucket"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_json(text: str) -> dict[str, object]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def row_id(row: dict[str, str]) -> str:
    return row.get("pair_id") or row.get("candidate_id") or row.get(
        "pair_id_or_candidate_id", ""
    )


def governance_maps() -> dict[str, dict[tuple[str, str], dict[str, str]]]:
    maps: dict[str, dict[tuple[str, str], dict[str, str]]] = {
        "use_now": {},
        "use_after_revision": {},
        "exclude_for_now": {},
        "adjudication": {},
        "complete_use_now": {},
    }
    inputs = {
        "use_now": GOV_DIR / "training_use_now.csv",
        "use_after_revision": GOV_DIR / "training_use_after_revision.csv",
        "exclude_for_now": GOV_DIR / "training_exclude_for_now.csv",
        "adjudication": GOV_DIR / "final_adjudication_master.csv",
        "complete_use_now": GOV_DIR / "complete_training_use_now.csv",
    }
    for label, path in inputs.items():
        for row in read_csv(path):
            dataset = row.get("dataset", "")
            key = row.get("pair_id_or_candidate_id") or row.get("pair_id", "")
            if dataset and key:
                maps[label][(dataset, key)] = row
    return maps


def status_text(row: dict[str, str], gov_row: dict[str, str] | None = None) -> str:
    parts = [
        row.get("review_status", ""),
        row.get("notes", ""),
        row.get("final_notes", ""),
        row.get("final_decision", ""),
    ]
    if gov_row:
        parts.extend(
            [
                gov_row.get("disagreement_summary", ""),
                gov_row.get("final_notes", ""),
                gov_row.get("final_decision", ""),
            ]
        )
    return " ".join(parts).lower()


def is_nhanes_promotable(
    row: dict[str, str], gov_row: dict[str, str] | None
) -> bool:
    if row.get("dataset") != "nhanes":
        return False
    if row.get("final_status") != "use_after_revision":
        return False
    if row.get("resource_type") != "Patient":
        return False
    text = status_text(row, gov_row)
    if "disposition-only" not in text:
        return False
    return not any(term in text for term in RISK_TERMS)


def is_mimic_demo_exception(
    row: dict[str, str], gov_row: dict[str, str] | None
) -> bool:
    if row.get("dataset") != "mimic_eicu":
        return False
    if row.get("resource_type") != "Observation":
        return False
    source_status = row.get("source_status", "").lower()
    text = status_text(row, gov_row)
    final_decision = (gov_row or {}).get("final_decision", "").lower()
    return (
        row.get("final_status") == "exclude_for_now"
        and final_decision == "keep"
        and ("demo" in source_status or "demo_only" in text)
    )


def split_clauses(text: str) -> list[str]:
    text = normalize_space(text)
    if not text:
        return []
    primary = re.split(r"\s*[;|]\s*", text)
    clauses: list[str] = []
    for part in primary:
        part = part.strip()
        if not part:
            continue
        pieces = re.split(r"\.\s+(?=[A-Z])", part)
        for piece in pieces:
            cleaned = piece.strip().strip(".")
            if cleaned:
                clauses.append(cleaned)
    return clauses or [text.strip().strip(".")]


def clean_key(key: str) -> str:
    key = normalize_space(key).strip(" :=")
    replacements = {
        "Observation": "Observation",
        "Result": "Result",
        "Value": "Value",
        "Status": "Status",
        "Effective": "Effective",
        "Effective date": "Effective date",
        "Date": "Date",
        "Patient name": "Patient name",
        "Name": "Name",
        "Identifier": "Identifier",
        "Gender": "Gender",
        "Birth date": "Birth date",
        "DOB": "DOB",
        "Clinical status": "Clinical status",
        "Verification status": "Verification status",
        "Onset": "Onset",
        "Onset date": "Onset date",
        "Abatement": "Abatement",
    }
    return replacements.get(key, key[:1].upper() + key[1:] if key else key)


def clause_facts(clauses: Iterable[str]) -> list[tuple[str, str]]:
    facts: list[tuple[str, str]] = []
    for index, clause in enumerate(clauses, start=1):
        if "=" in clause:
            key, value = clause.split("=", 1)
            facts.append((clean_key(key), normalize_space(value)))
        elif ":" in clause:
            key, value = clause.split(":", 1)
            facts.append((clean_key(key), normalize_space(value)))
        else:
            facts.append((f"Fact {index}", normalize_space(clause)))
    return [(key, value) for key, value in facts if key and value]


def observation_facts_from_target(row: dict[str, str]) -> list[tuple[str, str]]:
    if row.get("resource_type") != "Observation":
        return []
    target = load_json(row.get("target_fhir_json", ""))
    if not target:
        return []
    code = ""
    code_obj = target.get("code")
    if isinstance(code_obj, dict):
        code = str(code_obj.get("text") or "")
        coding = code_obj.get("coding")
        if not code and isinstance(coding, list) and coding:
            first = coding[0]
            if isinstance(first, dict):
                code = str(first.get("display") or first.get("code") or "")
    value_text = ""
    value = target.get("valueQuantity")
    if isinstance(value, dict) and value.get("value") is not None:
        unit = value.get("unit") or value.get("code") or ""
        value_text = normalize_space(f"{value.get('value')} {unit}")
    facts: list[tuple[str, str]] = []
    if code:
        facts.append(("Observation", code))
    if target.get("status"):
        facts.append(("Status", str(target["status"])))
    if value_text:
        facts.append(("Value", value_text))
    effective = target.get("effectiveDateTime")
    if not effective and isinstance(target.get("effectivePeriod"), dict):
        effective = target["effectivePeriod"].get("start")
    if effective:
        facts.append(("Effective", str(effective)))
    return facts


def patient_facts_from_target(row: dict[str, str]) -> list[tuple[str, str]]:
    if row.get("resource_type") != "Patient":
        return []
    if row.get("dataset") == "synthea":
        return []
    target = load_json(row.get("target_fhir_json", ""))
    if not target:
        return []
    facts: list[tuple[str, str]] = []
    names = target.get("name")
    if isinstance(names, list) and names:
        first = names[0]
        if isinstance(first, dict):
            given = first.get("given")
            given_text = " ".join(str(part) for part in given) if isinstance(given, list) else ""
            family = str(first.get("family") or "")
            name = normalize_space(f"{given_text} {family}")
            if name:
                facts.append(("Name", name))
    identifiers = target.get("identifier")
    if isinstance(identifiers, list) and identifiers:
        first_identifier = identifiers[0]
        if isinstance(first_identifier, dict) and first_identifier.get("value"):
            facts.append(("Identifier", str(first_identifier["value"])))
    if target.get("active") is not None:
        facts.append(("Active", str(target["active"]).lower()))
    if target.get("gender"):
        facts.append(("Gender", str(target["gender"])))
    if target.get("birthDate"):
        facts.append(("Birth date", str(target["birthDate"])))
    if target.get("deceasedDateTime"):
        facts.append(("Deceased date", str(target["deceasedDateTime"])))
    elif target.get("deceasedBoolean") is not None:
        facts.append(("Deceased", str(target["deceasedBoolean"]).lower()))
    extensions = target.get("extension")
    if isinstance(extensions, list):
        for extension in extensions:
            if not isinstance(extension, dict):
                continue
            url = str(extension.get("url") or "")
            if not url.startswith("urn:nhanes:"):
                continue
            label = url.rsplit(":", 1)[-1].replace("_", " ")
            label = label[:1].upper() + label[1:]
            for value_key in ("valueString", "valueInteger", "valueDecimal", "valueBoolean"):
                if value_key in extension:
                    facts.append((label, str(extension[value_key])))
                    break
    return facts


def condition_facts_from_target(row: dict[str, str]) -> list[tuple[str, str]]:
    if row.get("resource_type") != "Condition":
        return []
    if row.get("dataset") not in {"official", "gpt_expanded"}:
        return []
    target = load_json(row.get("target_fhir_json", ""))
    if not target:
        return []
    facts: list[tuple[str, str]] = []
    code_obj = target.get("code")
    condition = ""
    if isinstance(code_obj, dict):
        condition = str(code_obj.get("text") or "")
        coding = code_obj.get("coding")
        if not condition and isinstance(coding, list) and coding:
            first = coding[0]
            if isinstance(first, dict):
                condition = str(first.get("display") or first.get("code") or "")
    if condition:
        facts.append(("Condition", condition))
    for target_key, label in (
        ("clinicalStatus", "Clinical status"),
        ("verificationStatus", "Verification status"),
    ):
        value = target.get(target_key)
        if isinstance(value, dict):
            coding = value.get("coding")
            if isinstance(coding, list) and coding:
                first = coding[0]
                if isinstance(first, dict):
                    facts.append((label, str(first.get("code") or first.get("display") or "")))
    if target.get("onsetDateTime"):
        facts.append(("Onset", str(target["onsetDateTime"])))
    if target.get("abatementDateTime"):
        facts.append(("Abatement", str(target["abatementDateTime"])))
    return [(key, value) for key, value in facts if value]


def target_supported_facts(row: dict[str, str]) -> list[tuple[str, str]]:
    """Return target facts safe enough for source-side restyling.

    For Observations, value/unit/status/date identity is central and must be
    protected, so the target is used as a canonical reference.  For other
    resource types, the source text clauses remain the primary basis to avoid
    adding hidden context such as Synthea subject/encounter references.
    """

    if row.get("resource_type") == "Observation":
        return observation_facts_from_target(row)
    if row.get("resource_type") == "Patient":
        return patient_facts_from_target(row)
    if row.get("resource_type") == "Condition":
        return condition_facts_from_target(row)
    return []


def maybe_patient_regex_facts(text: str) -> list[tuple[str, str]]:
    patterns = [
        (
            r"Active patient record for (?P<name>.+?) with identifier (?P<identifier>[^.]+)",
            [("Active", "true"), ("Name", "name"), ("Identifier", "identifier")],
        ),
        (
            r"Active patient (?P<name>.+?), identifier (?P<identifier>[^.]+)",
            [("Active", "true"), ("Name", "name"), ("Identifier", "identifier")],
        ),
        (
            r"(?P<gender>male|female) patient (?P<name>.+?), born (?P<birth>[^.]+)",
            [("Gender", "gender"), ("Name", "name"), ("Birth date", "birth")],
        ),
    ]
    for pattern, fields in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        facts: list[tuple[str, str]] = []
        for label, group in fields:
            value = group if group in ("true", "false") else match.group(group)
            facts.append((label, normalize_space(value)))
        return facts
    return []


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
    candidate = candidate.strip()
    if not candidate:
        return
    key = normalize_space(candidate).lower()
    if key in seen:
        return
    seen.add(key)
    candidates.append((style, candidate, method))


def facts_variants(
    row: dict[str, str],
    facts: list[tuple[str, str]],
    candidates: list[tuple[str, str, str]],
    seen: set[str],
) -> None:
    if not facts:
        return
    resource = row.get("resource_type", "Resource")
    colon = "; ".join(f"{key}: {value}" for key, value in facts)
    equals = " | ".join(f"{key}={value}" for key, value in facts)
    sentences = ". ".join(f"{key}: {value}" for key, value in facts) + "."
    compact = " / ".join(f"{key} {value}" for key, value in facts)
    add_candidate(candidates, seen, "semi_structured", equals, "facts_equal_pipe")
    add_candidate(candidates, seen, "compact_clinical", colon, "facts_colon_semicolon")
    add_candidate(
        candidates, seen, "brief_factual_note", sentences, "facts_sentence_note"
    )
    add_candidate(candidates, seen, "compact_clinical", compact, "facts_slash_compact")

    fact_map = {key.lower(): value for key, value in facts}
    if resource == "Observation":
        name = fact_map.get("observation") or fact_map.get("measure") or ""
        value = fact_map.get("value") or fact_map.get("result") or ""
        status = fact_map.get("status") or ""
        effective = fact_map.get("effective") or fact_map.get("date") or ""
        if name and value:
            add_candidate(
                candidates,
                seen,
                "concise_clinical",
                f"{name}: {value}.",
                "observation_name_value",
            )
            detail_parts = [f"{name} = {value}"]
            if status:
                detail_parts.append(f"status {status}")
            if effective:
                detail_parts.append(f"effective {effective}")
            add_candidate(
                candidates,
                seen,
                "compact_clinical",
                "; ".join(detail_parts),
                "observation_compact_result_status_date",
            )
            semi_parts = [f"Observation={name}", f"Value={value}"]
            if status:
                semi_parts.append(f"Status={status}")
            if effective:
                semi_parts.append(f"Effective={effective}")
            add_candidate(
                candidates,
                seen,
                "semi_structured",
                " | ".join(semi_parts),
                "observation_semistructured_result",
            )
            note = f"{name} result {value}"
            if status:
                note += f", status {status}"
            if effective:
                note += f", effective {effective}"
            add_candidate(
                candidates,
                seen,
                "brief_factual_note",
                note + ".",
                "observation_brief_result_note",
            )

    elif resource == "Condition":
        condition = fact_map.get("condition") or fact_map.get("fact 1") or ""
        status = fact_map.get("clinical status") or ""
        verification = fact_map.get("verification status") or ""
        onset = fact_map.get("onset") or fact_map.get("onset date") or ""
        abatement = fact_map.get("abatement") or ""
        if condition:
            pieces = [f"Condition: {condition}"]
            if status:
                pieces.append(f"clinical status: {status}")
            if verification:
                pieces.append(f"verification: {verification}")
            if onset:
                pieces.append(f"onset: {onset}")
            if abatement:
                pieces.append(f"abatement: {abatement}")
            add_candidate(
                candidates,
                seen,
                "concise_clinical",
                "; ".join(pieces) + ".",
                "condition_concise_fact_set",
            )
            add_candidate(
                candidates,
                seen,
                "semi_structured",
                " | ".join(piece.replace(": ", "=") for piece in pieces),
                "condition_semistructured_fact_set",
            )

    elif resource == "Patient":
        name = fact_map.get("patient name") or fact_map.get("name") or ""
        identifier = fact_map.get("identifier") or ""
        gender = fact_map.get("gender") or ""
        birth = fact_map.get("birth date") or fact_map.get("dob") or ""
        active = fact_map.get("active") or ""
        pieces = []
        if name:
            pieces.append(f"Name: {name}")
        if identifier:
            pieces.append(f"Identifier: {identifier}")
        if gender:
            pieces.append(f"Gender: {gender}")
        if birth:
            pieces.append(f"Birth date: {birth}")
        if active:
            pieces.append(f"Active: {active}")
        if pieces:
            add_candidate(
                candidates,
                seen,
                "semi_structured",
                "Patient | " + " | ".join(pieces),
                "patient_semistructured_core_fields",
            )
            add_candidate(
                candidates,
                seen,
                "brief_factual_note",
                "; ".join(pieces) + ".",
                "patient_brief_core_fields",
            )


def source_variants(row: dict[str, str], needed: int) -> list[tuple[str, str, str]]:
    original = row.get("input_text", "")
    resource = row.get("resource_type", "Resource")
    original_style = row.get("input_style", "source")
    clauses = split_clauses(original)
    facts = clause_facts(clauses)
    regex_facts = maybe_patient_regex_facts(original)
    if regex_facts:
        facts = regex_facts + [
            fact for fact in facts if fact[0] not in {label for label, _ in regex_facts}
        ]
    target_facts = target_supported_facts(row)
    if target_facts:
        facts = target_facts

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

    if clauses:
        semicolon = "; ".join(clauses)
        pipe = " | ".join(clauses)
        sentences = ". ".join(clauses) + "."
        slash = " / ".join(clauses)
        comma = ", ".join(clauses) + "."
        add_candidate(
            candidates,
            seen,
            "compact_clinical",
            semicolon,
            "clause_semicolon_compact",
        )
        add_candidate(
            candidates,
            seen,
            "semi_structured",
            pipe,
            "clause_pipe_semistructured",
        )
        add_candidate(
            candidates,
            seen,
            "brief_factual_note",
            sentences,
            "clause_sentence_note",
        )
        add_candidate(
            candidates,
            seen,
            "compact_clinical",
            slash,
            "clause_slash_compact",
        )
        add_candidate(
            candidates,
            seen,
            "brief_factual_note",
            comma,
            "clause_comma_note",
        )
        if len(clauses) > 2:
            for offset in range(1, len(clauses)):
                rotated = clauses[offset:] + clauses[:offset]
                add_candidate(
                    candidates,
                    seen,
                    "compact_clinical",
                    "; ".join(rotated),
                    f"clause_rotation_{offset}",
                )

    facts_variants(row, facts, candidates, seen)

    if len(candidates) < needed and facts:
        label_sets = [
            ("concise_clinical", " ; ", ": ", "fact_label_colon"),
            ("semi_structured", " | ", " = ", "fact_label_equals"),
            ("compact_clinical", " / ", " ", "fact_label_minimal"),
            ("brief_factual_note", ". ", ": ", "fact_label_sentence"),
        ]
        for style, separator, joiner, method_prefix in label_sets:
            for offset in range(len(facts)):
                rotated = facts[offset:] + facts[:offset]
                text = separator.join(
                    f"{key}{joiner}{value}" for key, value in rotated
                )
                if style == "brief_factual_note" and not text.endswith("."):
                    text += "."
                add_candidate(
                    candidates,
                    seen,
                    style,
                    text,
                    f"{method_prefix}_rotation_{offset}",
                )
                if len(candidates) >= needed:
                    break
            if len(candidates) >= needed:
                break

    if len(candidates) < needed:
        text = normalize_space(original).rstrip(".")
        templates = [
            ("concise_clinical", f"{resource}: {text}.", "resource_colon_original"),
            (
                "semi_structured",
                f"Resource={resource} | Text={text}",
                "resource_text_fields",
            ),
            (
                "compact_clinical",
                f"{resource} - {text}",
                "resource_dash_original",
            ),
            (
                "brief_factual_note",
                f"{text}.",
                "normalized_original_sentence",
            ),
        ]
        for style, candidate, method in templates:
            add_candidate(candidates, seen, style, candidate, method)
            if len(candidates) >= needed:
                break

    if len(candidates) < needed:
        raise ValueError(
            f"Generated {len(candidates)} variants for {row.get('dataset')} "
            f"{row.get('pair_id')} but need {needed}."
        )
    return candidates[:needed]


def allocation_priority(dataset: str, row: dict[str, str]) -> tuple[int, str]:
    resource = row.get("resource_type", "")
    if dataset in {"synthea", "nhanes", "official"}:
        resource_order = {"Observation": 0, "Patient": 1, "Condition": 2}
    elif dataset == "gpt_expanded":
        resource_order = {"Observation": 0, "Patient": 1, "Condition": 2}
    else:
        resource_order = {"Observation": 0, "Patient": 1, "Condition": 2}
    return (resource_order.get(resource, 9), row_id(row))


def allocate_counts(
    dataset: str, rows: list[dict[str, str]], target: int
) -> dict[str, int]:
    if not rows and target:
        raise ValueError(f"No source rows for {dataset} target {target}")
    if not target:
        return {}
    base = target // len(rows)
    remainder = target % len(rows)
    allocation = {row_id(row): base for row in rows}
    prioritized = sorted(rows, key=lambda row: allocation_priority(dataset, row))
    for row in prioritized[:remainder]:
        allocation[row_id(row)] += 1
    return allocation


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gov = governance_maps()

    pools: dict[str, list[dict[str, str]]] = defaultdict(list)
    promoted: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for dataset in DATASETS:
        final_rows = read_csv(FINAL_DIR / f"{dataset}_final_paired_data.csv")
        for row in final_rows:
            row = dict(row)
            key = (dataset, row_id(row))
            gov_row = gov["adjudication"].get(key) or gov["exclude_for_now"].get(key)
            final_status = row.get("final_status", "")

            if final_status in {"use_now", "unreviewed_clean_candidate"}:
                if key in gov["exclude_for_now"]:
                    skipped.append(
                        {
                            "dataset": dataset,
                            "pair_id_or_candidate_id": row_id(row),
                            "final_status": final_status,
                            "governance_bucket": "exclude_for_now",
                            "source_status": row.get("source_status", ""),
                            "skip_reason": "Governance exclude bucket overrides clean candidate status.",
                        }
                    )
                    continue
                row["_source_status"] = final_status
                row["_source_pool_label"] = f"finalized_{final_status}"
                pools[dataset].append(row)
            elif is_mimic_demo_exception(row, gov_row):
                row["_source_status"] = "demo_only_low_weight"
                row["_source_pool_label"] = MIMIC_EXCEPTION_LABEL
                pools[dataset].append(row)
            else:
                reason = "final_status_exclude_for_now_not_allowed"
                if dataset == "mimic_eicu":
                    reason = "mimic_eicu_row_not_selected_as_demo_only_exception"
                skipped.append(
                    {
                        "dataset": dataset,
                        "pair_id_or_candidate_id": row_id(row),
                        "final_status": final_status,
                        "governance_bucket": (
                            "exclude_for_now"
                            if key in gov["exclude_for_now"]
                            else final_status
                        ),
                        "source_status": row.get("source_status", ""),
                        "skip_reason": reason,
                    }
                )

        for row in read_csv(FINAL_DIR / f"{dataset}_use_after_revision.csv"):
            row = dict(row)
            key = (dataset, row_id(row))
            gov_row = gov["use_after_revision"].get(key) or gov["adjudication"].get(key)
            if is_nhanes_promotable(row, gov_row):
                row["_source_status"] = "promoted_use_after_revision"
                row["_source_pool_label"] = (
                    "promoted_nhanes_patient_disposition_only"
                )
                row["_promotion_reason"] = NHANES_PROMOTION_REASON
                row["_promotion_risk_note"] = NHANES_PROMOTION_RISK_NOTE
                pools[dataset].append(row)
                promoted.append(row)
            elif row_id(row):
                if dataset == "official":
                    reason = "not_promoted_official_revision_has_context_leakage_or_omission_risk"
                elif dataset == "gpt_expanded":
                    reason = "not_promoted_gpt_expanded_revision_pending_adjudication"
                else:
                    reason = "not_promoted_use_after_revision"
                skipped.append(
                    {
                        "dataset": dataset,
                        "pair_id_or_candidate_id": row_id(row),
                        "final_status": row.get("final_status", ""),
                        "governance_bucket": "use_after_revision",
                        "source_status": row.get("source_status", ""),
                        "skip_reason": reason,
                    }
                )

    for dataset, expected in {
        "synthea": 345,
        "official": 8,
        "nhanes": 30,
        "gpt_expanded": 20,
        "mimic_eicu": 14,
    }.items():
        actual = len(pools[dataset])
        if actual != expected:
            raise AssertionError(
                f"Unexpected {dataset} source pool size {actual}, expected {expected}"
            )

    expanded: list[dict[str, str]] = []
    sequence = 1
    for dataset in DATASETS:
        rows = pools[dataset]
        allocation = allocate_counts(dataset, rows, TARGET_COUNTS[dataset])
        for row in rows:
            source_id = row_id(row)
            needed = allocation[source_id]
            variants = source_variants(row, needed)
            for variant_index, (style, input_text, method) in enumerate(
                variants, start=1
            ):
                preserved = method == "source_preserved"
                if preserved:
                    origin = "finalized_paired_row_preserved"
                elif row["_source_status"] == "demo_only_low_weight":
                    origin = "demo_only_low_weight_source_side_variant"
                else:
                    origin = "finalized_paired_row_source_side_variant"
                notes = normalize_space(
                    " ".join(
                        part
                        for part in [
                            row.get("notes", ""),
                            row.get("final_notes", ""),
                            row.get("_promotion_reason", ""),
                            (
                                "MIMIC/eICU retained only as mandatory tiny "
                                "demo_only low-weight realism-stress subset."
                                if row["_source_status"] == "demo_only_low_weight"
                                else ""
                            ),
                            (
                                "Original paired input preserved exactly."
                                if preserved
                                else (
                                    "Conservative source-side style variation; "
                                    "target FHIR JSON preserved exactly."
                                )
                            ),
                        ]
                        if part
                    )
                )
                expanded.append(
                    {
                        "final_pair_id": f"train-final-v1-{sequence:04d}",
                        "source_dataset": dataset,
                        "source_status": row["_source_status"],
                        "original_pair_id": row.get("pair_id", ""),
                        "original_candidate_id": row.get("candidate_id", ""),
                        "resource_type": row.get("resource_type", ""),
                        "input_style": style,
                        "input_text": input_text,
                        "target_fhir_json": row.get("target_fhir_json", ""),
                        "expansion_origin": origin,
                        "expansion_method": f"{method}__v{variant_index:03d}",
                        "source_pool_label": row["_source_pool_label"],
                        "notes": notes,
                    }
                )
                sequence += 1

    if len(expanded) != 2000:
        raise AssertionError(f"Expected 2000 rows; built {len(expanded)}")
    if any(
        row["source_status"] == "exclude_for_now"
        for row in expanded
    ):
        raise AssertionError("A raw exclude_for_now status entered the corpus")
    if sum(row["source_dataset"] == "official" for row in expanded) == 0:
        raise AssertionError("Official contribution is zero")
    if sum(row["source_dataset"] == "mimic_eicu" for row in expanded) == 0:
        raise AssertionError("MIMIC/eICU contribution is zero")

    write_csv(
        OUT_DIR / "v1_rebuilt_expanded_paired_data_2000.csv",
        expanded,
        OUTPUT_FIELDS,
    )
    with (OUT_DIR / "v1_rebuilt_expanded_paired_data_2000.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in expanded:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    dataset_counts = Counter(row["source_dataset"] for row in expanded)
    resource_by_dataset: dict[str, Counter[str]] = defaultdict(Counter)
    for row in expanded:
        resource_by_dataset[row["source_dataset"]][row["resource_type"]] += 1
    dataset_mix = []
    for dataset in DATASETS:
        count = dataset_counts.get(dataset, 0)
        resources = resource_by_dataset[dataset]
        dataset_mix.append(
            {
                "dataset": dataset,
                "row_count": count,
                "percentage": f"{count / len(expanded):.2%}",
                "observation_count": resources.get("Observation", 0),
                "patient_count": resources.get("Patient", 0),
                "condition_count": resources.get("Condition", 0),
            }
        )
    write_csv(
        OUT_DIR / "v1_rebuilt_dataset_mix_summary.csv",
        dataset_mix,
        [
            "dataset",
            "row_count",
            "percentage",
            "observation_count",
            "patient_count",
            "condition_count",
        ],
    )

    style_counts = Counter(row["input_style"] for row in expanded)
    style_mix = [
        {
            "input_style": style,
            "row_count": count,
            "percentage": f"{count / len(expanded):.2%}",
        }
        for style, count in sorted(style_counts.items())
    ]
    write_csv(
        OUT_DIR / "v1_rebuilt_style_mix_summary.csv",
        style_mix,
        ["input_style", "row_count", "percentage"],
    )

    promoted_manifest = [
        {
            "dataset": row["dataset"],
            "pair_id_or_candidate_id": row_id(row),
            "original_status": row.get("final_status", ""),
            "promotion_reason": NHANES_PROMOTION_REASON,
            "risk_note": NHANES_PROMOTION_RISK_NOTE,
        }
        for row in promoted
    ]
    write_csv(
        OUT_DIR / "v1_promoted_use_after_revision_rows.csv",
        promoted_manifest,
        [
            "dataset",
            "pair_id_or_candidate_id",
            "original_status",
            "promotion_reason",
            "risk_note",
        ],
    )

    skipped_unique = {
        (
            row["dataset"],
            row["pair_id_or_candidate_id"],
            row["final_status"],
            row["governance_bucket"],
            row["skip_reason"],
        ): row
        for row in skipped
        if row["pair_id_or_candidate_id"]
    }
    skipped_rows = list(skipped_unique.values())
    skipped_rows.sort(
        key=lambda row: (
            DATASETS.index(row["dataset"])
            if row["dataset"] in DATASETS
            else 99,
            row["pair_id_or_candidate_id"],
            row["skip_reason"],
        )
    )
    write_csv(
        OUT_DIR / "v1_unmatched_or_skipped_rows.csv",
        skipped_rows,
        [
            "dataset",
            "pair_id_or_candidate_id",
            "final_status",
            "governance_bucket",
            "source_status",
            "skip_reason",
        ],
    )

    skipped_exclude_counts = Counter(
        row["dataset"]
        for row in skipped_rows
        if row["governance_bucket"] == "exclude_for_now"
    )
    plan = []
    for dataset in DATASETS:
        pool = pools[dataset]
        status_counts = Counter(row["_source_status"] for row in pool)
        if dataset == "mimic_eicu":
            source_pool_used = (
                "14 mandatory demo_only low-weight Observation rows with "
                "review final_decision=keep, retained as realism stress only"
            )
            rationale = (
                "Mandatory tiny realism-stress subset. Rows remain tagged "
                "demo_only_low_weight and are not used as backbone training data."
            )
        elif dataset == "official":
            source_pool_used = "finalized unreviewed_clean_candidate anchor rows"
            rationale = (
                "Non-zero high-fidelity anchor subset from clean finalized Official "
                "rows; excluded and revision-risk Official rows remain held out."
            )
        elif dataset == "gpt_expanded":
            source_pool_used = (
                "finalized use_now plus finalized unreviewed_clean_candidate rows"
            )
            rationale = (
                "Capped auxiliary diversity source below 10%; no GPT revision rows "
                "were promoted."
            )
        elif dataset == "nhanes":
            source_pool_used = (
                "finalized use_now plus unreviewed_clean_candidate rows, plus "
                "six promoted Patient disposition-only rows"
            )
            rationale = (
                "Moderate semi-structured realism subset with Observation-strong "
                "allocation and explicit conservative NHANES Patient promotions."
            )
        else:
            source_pool_used = (
                "finalized use_now plus finalized unreviewed_clean_candidate rows"
            )
            rationale = (
                "Majority backbone source using the broad clean finalized paired "
                "pool, including Synthea Observations."
            )
        plan.append(
            {
                "dataset": dataset,
                "source_pool_used": source_pool_used,
                "use_now_rows_used": status_counts.get("use_now", 0),
                "unreviewed_clean_candidate_rows_used": status_counts.get(
                    "unreviewed_clean_candidate", 0
                ),
                "promoted_use_after_revision_rows_used": status_counts.get(
                    "promoted_use_after_revision", 0
                ),
                "excluded_rows_ignored": skipped_exclude_counts.get(dataset, 0),
                "target_final_pair_count": TARGET_COUNTS[dataset],
                "final_pair_count": dataset_counts.get(dataset, 0),
                "rationale": rationale,
            }
        )
    write_csv(
        OUT_DIR / "v1_rebuilt_expansion_plan_2000.csv",
        plan,
        [
            "dataset",
            "source_pool_used",
            "use_now_rows_used",
            "unreviewed_clean_candidate_rows_used",
            "promoted_use_after_revision_rows_used",
            "excluded_rows_ignored",
            "target_final_pair_count",
            "final_pair_count",
            "rationale",
        ],
    )

    status_counts = Counter(row["source_status"] for row in expanded)
    resource_counts = Counter(row["resource_type"] for row in expanded)
    unique_bases = {
        (row["source_dataset"], row["original_pair_id"], row["original_candidate_id"])
        for row in expanded
    }

    guardrails = "\n\n".join(
        [
            "# v1 Rebuilt Quality Guardrails",
            "## Broadened Source Pool",
            (
                "The v1 rebuild expands from 417 unique finalized paired rows rather "
                "than the 39-row prototype base. The pool includes reviewed use_now "
                "rows plus finalized unreviewed_clean_candidate rows that were not in "
                "the exclude bucket, then adds only six documented NHANES Patient "
                "use_after_revision promotions."
            ),
            "## Excluded Row Control",
            (
                "Rows in the Official and GPT-expanded exclude buckets are skipped and "
                "listed in v1_unmatched_or_skipped_rows.csv. The only exception is the "
                "mandatory MIMIC/eICU realism-stress subset: those rows had review "
                "final_decision=keep but were bucketed as demo-only/low-weight rather "
                "than backbone-ready, so they are explicitly tagged demo_only_low_weight."
            ),
            "## Official Anchor Preservation",
            (
                "Official contributes 120 rows from eight finalized clean candidate "
                "anchors. The two Official use_after_revision rows are not promoted "
                "because their review notes include context leakage or omission risk."
            ),
            "## MIMIC/eICU Demo-Only Realism Subset",
            (
                "MIMIC/eICU contributes 14 rows, all Observations, with source_status "
                "demo_only_low_weight and source_pool_label "
                f"{MIMIC_EXCEPTION_LABEL}. They are included only to satisfy the tiny "
                "realism-stress requirement and are not expanded beyond their original "
                "row count."
            ),
            "## GPT-Expanded Cap",
            (
                "GPT-expanded contributes 196 rows, 9.8% of the final corpus. It uses "
                "only use_now and finalized unreviewed clean candidates; no GPT "
                "use_after_revision row is promoted."
            ),
            "## Reduced Wrapper-Only Expansion",
            (
                "The rebuild avoids generic prefix/suffix wrappers as the primary "
                "mechanism. New source variants use clause normalization, key-value "
                "style conversion, brief factual notes, compact clinical phrasing, and "
                "Observation-specific value/unit restatements while preserving target "
                "JSON exactly."
            ),
            "## Near-Duplicate Control",
            (
                "Each original row is preserved exactly once. Additional variants are "
                "bounded by dataset allocation: broad Synthea rows receive only three "
                "or four total rows, GPT remains capped, Official remains small, and "
                "MIMIC/eICU is not expanded. Provenance is tracked through "
                "original_pair_id, source_pool_label, expansion_origin, and "
                "expansion_method."
            ),
            "## Observation And Unit Protection",
            (
                "Observation variants never convert, round, or reinterpret values. "
                "When an Observation is restyled, measure identity, numeric value, "
                "unit, status, and effective date are copied from the accepted paired "
                "row or its accepted target JSON without unit conversion."
            ),
        ]
    )
    (OUT_DIR / "v1_rebuilt_quality_guardrails.md").write_text(
        guardrails + "\n", encoding="utf-8"
    )

    summary = "\n\n".join(
        [
            "# v1 Rebuilt Expansion Summary",
            f"Final total size: {len(expanded)} paired examples.",
            f"Unique original rows used as the expansion base: {len(unique_bases)}.",
            "## Dataset Contribution",
            markdown_table(
                ["dataset", "rows", "percentage"],
                [
                    [
                        dataset,
                        dataset_counts.get(dataset, 0),
                        f"{dataset_counts.get(dataset, 0) / len(expanded):.1%}",
                    ]
                    for dataset in DATASETS
                ],
            ),
            "## Resource-Type Contribution",
            markdown_table(
                ["resource_type", "rows", "percentage"],
                [
                    [resource, count, f"{count / len(expanded):.1%}"]
                    for resource, count in sorted(resource_counts.items())
                ],
            ),
            "## Source Status Contribution",
            markdown_table(
                ["source_status", "rows", "percentage"],
                [
                    [status, count, f"{count / len(expanded):.1%}"]
                    for status, count in sorted(status_counts.items())
                ],
            ),
            (
                "Official is non-zero: yes, 120 rows from eight finalized clean "
                "Official anchors."
            ),
            (
                "MIMIC/eICU is non-zero: yes, 14 demo_only_low_weight Observation "
                "rows retained as a tiny realism-stress subset."
            ),
            (
                "Suitability improvement over the prototype: yes. The prototype "
                "expanded from 39 unique reviewed/promoted rows and relied heavily on "
                "wrapper-style variants. This v1 rebuild expands from 417 unique "
                "original paired rows, includes Official anchors, retains a tiny "
                "MIMIC/eICU realism subset, keeps GPT-expanded capped, and uses more "
                "substantive conservative source-side variation."
            ),
            (
                "Remaining weaknesses: Official still has only eight clean finalized "
                "base rows, NHANES remains a small source pool relative to its target "
                "count, and the MIMIC/eICU subset is included under an explicit "
                "demo-only exception because the prior governance layer did not mark "
                "those rows as formal backbone training rows. These limitations are "
                "made visible rather than hidden."
            ),
        ]
    )
    (OUT_DIR / "v1_rebuilt_expansion_summary.md").write_text(
        summary + "\n", encoding="utf-8"
    )

    print("Built v1 rebuilt corpus")
    print(f"  rows: {len(expanded)}")
    print(f"  unique original base rows: {len(unique_bases)}")
    print(f"  datasets: {dict(dataset_counts)}")
    print(f"  resources: {dict(resource_counts)}")
    print(f"  source statuses: {dict(status_counts)}")


if __name__ == "__main__":
    main()
