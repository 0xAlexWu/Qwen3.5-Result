# Complete Training Use Now Summary

- Total rows in `training_use_now.csv`: **34**
- Total rows successfully matched back to full paired content (`input_text` + `target_fhir_json` both recovered): **34**
- Rows with missing `input_text`: **0**
- Rows with missing `target_fhir_json`: **0**
- Rows not fully matched back to raw paired content: **0**

## Dataset Contribution

- `gpt_expanded`: 6 rows
- `nhanes`: 14 rows
- `synthea`: 14 rows

## Source Tables Used

- `gpt_expanded` review table: `review_merge/gpt_expanded_review_merge.csv`; upstream paired-content sources: `upstream_repos/FHIR-GPT-Seeds/outputs/gpt_expanded/gpt_expanded_pair_candidates.csv`
- `mimic_eicu` review table: `review_merge/mimic_eicu_review_merge.csv`; upstream paired-content sources: `not found`
- `nhanes` review table: `review_merge/nhanes_review_merge.csv`; upstream paired-content sources: `upstream_repos/FHIR-NHANES-Seeds/outputs/nhanes/nhanes_pilot15_pair_candidates.csv`
- `official` review table: `review_merge/official_review_merge.csv`; upstream paired-content sources: `not found`
- `synthea` review table: `review_merge/synthea_review_merge.csv`; upstream paired-content sources: `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_pilot50_pair_candidates.csv`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/synthea_remaining70_pair_candidates.csv`, `upstream_repos/FHIR-Synthea-Seeds/outputs/large/reviewer_batch_prompts/*.txt`

## Unmatched Or Partial Rows

- None
