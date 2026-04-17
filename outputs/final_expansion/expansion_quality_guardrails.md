# Expansion Quality Guardrails

## Allowed Expansion

The expansion pool contains finalized paired rows labeled use_now plus six explicitly promoted NHANES Patient rows from use_after_revision. Every expanded row preserves the original target_fhir_json string exactly. New rows change only the source side through deterministic wrappers or separator/field reformatting of the original input_text.

## Disallowed Expansion

Rows labeled exclude_for_now are never included. Unreviewed clean candidates are not treated as formal expansion sources. Official revision rows are not promoted because the target contains linked subject/performer context not fully stated in the input. GPT-expanded revision rows are not promoted because they remain flagged for explicit adjudication. MIMIC/eICU rows are not retained because the finalized layer marks them demo-only/exclude_for_now.

## Unsupported-Fact And Context-Leakage Control

Promotion requires absence of unsupported_fact, context_leakage, and possible_hallucination terms in notes and final_notes. The only promoted rows are NHANES Patient rows whose issue is recorded as disposition-only. Expansion text is derived from the original paired input_text, not from upstream seeds or raw candidate catalogs, and target JSON is never enriched.

## Near-Duplicate Inflation Control

Near-duplicate expansion is tracked by original_pair_id, expansion_origin, and expansion_method. Each source row keeps one exact preserved source row; additional rows are deterministic source wrappers or clause reformats. Dataset caps limit GPT-expanded to 10% and exclude MIMIC/eICU entirely.

## Unit-Sensitive Observation Handling

Observation variants do not recalculate or convert values. Since the source side is wrapped/reformatted rather than numerically rewritten, measure identity, numeric value, and unit strings remain as stated in the accepted paired input.

## Governance Continuity

This build respects the reviewed paired-data governance layer by expanding from finalized paired rows rather than seed catalogs, documenting every promotion, retaining exact targets, excluding current exclude_for_now rows, and writing a separate exclusion summary for held-out finalized rows.
