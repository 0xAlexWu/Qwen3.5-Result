# v1 Rebuilt Quality Guardrails

## Broadened Source Pool

The v1 rebuild expands from 417 unique finalized paired rows rather than the 39-row prototype base. The pool includes reviewed use_now rows plus finalized unreviewed_clean_candidate rows that were not in the exclude bucket, then adds only six documented NHANES Patient use_after_revision promotions.

## Excluded Row Control

Rows in the Official and GPT-expanded exclude buckets are skipped and listed in v1_unmatched_or_skipped_rows.csv. The only exception is the mandatory MIMIC/eICU realism-stress subset: those rows had review final_decision=keep but were bucketed as demo-only/low-weight rather than backbone-ready, so they are explicitly tagged demo_only_low_weight.

## Official Anchor Preservation

Official contributes 120 rows from eight finalized clean candidate anchors. The two Official use_after_revision rows are not promoted because their review notes include context leakage or omission risk.

## MIMIC/eICU Demo-Only Realism Subset

MIMIC/eICU contributes 14 rows, all Observations, with source_status demo_only_low_weight and source_pool_label mandatory_demo_only_low_weight_exception_from_review_keep_exclude_bucket. They are included only to satisfy the tiny realism-stress requirement and are not expanded beyond their original row count.

## GPT-Expanded Cap

GPT-expanded contributes 196 rows, 9.8% of the final corpus. It uses only use_now and finalized unreviewed clean candidates; no GPT use_after_revision row is promoted.

## Reduced Wrapper-Only Expansion

The rebuild avoids generic prefix/suffix wrappers as the primary mechanism. New source variants use clause normalization, key-value style conversion, brief factual notes, compact clinical phrasing, and Observation-specific value/unit restatements while preserving target JSON exactly.

## Near-Duplicate Control

Each original row is preserved exactly once. Additional variants are bounded by dataset allocation: broad Synthea rows receive only three or four total rows, GPT remains capped, Official remains small, and MIMIC/eICU is not expanded. Provenance is tracked through original_pair_id, source_pool_label, expansion_origin, and expansion_method.

## Observation And Unit Protection

Observation variants never convert, round, or reinterpret values. When an Observation is restyled, measure identity, numeric value, unit, status, and effective date are copied from the accepted paired row or its accepted target JSON without unit conversion.
