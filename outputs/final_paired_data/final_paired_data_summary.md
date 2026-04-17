# Final Paired Data Summary

These exports reconcile the original upstream paired-candidate repositories with the downstream post-review governance decisions from `summary-human-judgement`.

## Source Repositories

- `synthea` paired candidates came from `FHIR-Synthea-Seeds` via `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_pilot50_pair_candidates.csv`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_remaining70_pair_candidates.csv`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_pilot50_pair_candidates.jsonl`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_remaining70_pair_candidates.jsonl`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/reviewer_batch_prompts/*.txt`.
- `official` paired candidates came from `FHIR-Official-Seeds` via `upstream_repos/FHIR-Official-Seeds/outputs/official/official_pilot12_pair_candidates.csv`, `upstream_repos/FHIR-Official-Seeds/outputs/official/official_pilot12_pair_candidates.jsonl`, `upstream_repos/FHIR-Official-Seeds/outputs/reviewer_batch_prompts/*.txt`.
- `nhanes` paired candidates came from `FHIR-NHANES-Seeds` via `upstream_repos/FHIR-NHANES-Seeds/outputs/nhanes/nhanes_pilot15_pair_candidates.csv`, `upstream_repos/FHIR-NHANES-Seeds/outputs/nhanes/nhanes_pilot15_pair_candidates.jsonl`.
- `gpt_expanded` paired candidates came from `FHIR-GPT-Seeds` via `upstream_repos/FHIR-GPT-Seeds/outputs/gpt_expanded/gpt_expanded_pair_candidates.csv`, `upstream_repos/FHIR-GPT-Seeds/outputs/gpt_expanded/gpt_expanded_pair_candidates.jsonl`.
- `mimic_eicu` paired candidates came from `MIMIC-eICU-Seeds` via `upstream_repos/MIMIC-eICU-Seeds/outputs/mimic_eicu/demo_pair_pilot/demo_pair_candidates.csv`, `upstream_repos/MIMIC-eICU-Seeds/outputs/mimic_eicu/demo_pair_pilot/demo_pair_candidates.jsonl`.

## Review Reconciliation

- `summary-human-judgement` supplied the post-review bucket files and final adjudication table.
- Rows appearing in `training_use_now.csv` were labeled `use_now`.
- Rows appearing in `training_use_after_revision.csv` were labeled `use_after_revision`.
- Rows appearing in `training_exclude_for_now.csv` were labeled `exclude_for_now`.
- Any original upstream paired candidate absent from all review bucket files was labeled `unreviewed_clean_candidate`.
- Counts in these final dataset exports are reported at unique upstream paired-candidate granularity. If multiple review rows point to the same `dataset + pair_id`, they reconcile onto one frozen upstream pair row rather than being duplicated.
- The main `*_final_paired_data.csv/.jsonl` exports intentionally exclude `use_after_revision` rows; those rows remain available only in the separate `*_use_after_revision.csv` subsets.

## Operational Meaning

- `use_now` rows are the currently frozen training-ready subset.
- `use_after_revision` rows remain potentially salvageable after adjudication or targeted cleanup, but are held out of the frozen main dataset exports.
- `exclude_for_now` rows are outside the current formal training set.
- `unreviewed_clean_candidate` rows were not part of the reviewed anomaly subset and remain outside the reviewed frozen subset unless explicitly promoted later.
- `mimic_eicu` remains demo-only even where rows appear clean; the exports preserve `source_status = demo_only` rather than upgrading them into a backbone source.

## Counts

| Dataset | Total original pairs | use_now | use_after_revision | exclude_for_now | unreviewed_clean_candidate |
| --- | ---: | ---: | ---: | ---: | ---: |
| synthea | 345 | 14 | 0 | 0 | 331 |
| official | 24 | 0 | 2 | 14 | 8 |
| nhanes | 30 | 14 | 6 | 0 | 10 |
| gpt_expanded | 52 | 5 | 18 | 14 | 15 |
| mimic_eicu | 14 | 0 | 0 | 14 | 0 |

## Unmatched Review Rows

- None. All reviewed rows matched an upstream paired candidate.
