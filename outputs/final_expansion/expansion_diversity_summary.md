# Expansion Diversity Summary

Final size = 2,000 paired examples.

## Dataset Contribution

| dataset | rows | share |
| --- | --- | --- |
| synthea | 1200 | 60.0% |
| official | 0 | 0.0% |
| nhanes | 600 | 30.0% |
| gpt_expanded | 200 | 10.0% |
| mimic_eicu | 0 | 0.0% |

## Resource Type Contribution

| resource_type | rows | share |
| --- | --- | --- |
| Condition | 728 | 36.4% |
| Observation | 500 | 25.0% |
| Patient | 772 | 38.6% |

## Input Style Contribution

| input_style | rows | share |
| --- | --- | --- |
| brief_clinical_narrative | 1 | 0.1% |
| compact_clinical | 59 | 2.9% |
| concise_clinical | 15 | 0.8% |
| field_reformat | 60 | 3.0% |
| patient_utterance | 8 | 0.4% |
| record_fragment | 620 | 31.0% |
| semi_structured | 15 | 0.8% |
| source_wrapper | 627 | 31.4% |
| structured_prompt | 595 | 29.8% |

## Governance Source

| source | rows | share |
| --- | --- | --- |
| promoted_use_after_revision | 180 | 9.0% |
| use_now | 1820 | 91.0% |

Rows derived from original use_now paired rows: 1820. Rows derived from promoted use_after_revision paired rows: 180.

MIMIC/eICU retention: none. All MIMIC/eICU rows remain excluded from the formal corpus because the finalized layer marks them demo-only or exclude_for_now.

GPT-expanded cap: 200 rows, exactly 10.0% of the final corpus. Only use_now GPT-expanded rows are used; no unresolved flagged GPT revision rows were promoted.

Training balance: Synthea supplies the structural majority, NHANES adds a moderate semi-structured Observation/Patient realism subset, and GPT-expanded contributes capped auxiliary phrasing diversity. The corpus keeps Conditions, Patients, and Observations represented while preventing unreviewed, excluded, hidden-context, and demo-only rows from becoming backbone training data.
