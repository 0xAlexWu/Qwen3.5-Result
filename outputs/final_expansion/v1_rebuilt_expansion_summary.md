# v1 Rebuilt Expansion Summary

Final total size: 2000 paired examples.

Unique original rows used as the expansion base: 417.

## Dataset Contribution

| dataset | rows | percentage |
| --- | --- | --- |
| synthea | 1240 | 62.0% |
| official | 120 | 6.0% |
| nhanes | 430 | 21.5% |
| gpt_expanded | 196 | 9.8% |
| mimic_eicu | 14 | 0.7% |

## Resource-Type Contribution

| resource_type | rows | percentage |
| --- | --- | --- |
| Condition | 275 | 13.8% |
| Observation | 1369 | 68.5% |
| Patient | 356 | 17.8% |

## Source Status Contribution

| source_status | rows | percentage |
| --- | --- | --- |
| demo_only_low_weight | 14 | 0.7% |
| promoted_use_after_revision | 84 | 4.2% |
| unreviewed_clean_candidate | 1610 | 80.5% |
| use_now | 292 | 14.6% |

Official is non-zero: yes, 120 rows from eight finalized clean Official anchors.

MIMIC/eICU is non-zero: yes, 14 demo_only_low_weight Observation rows retained as a tiny realism-stress subset.

Suitability improvement over the prototype: yes. The prototype expanded from 39 unique reviewed/promoted rows and relied heavily on wrapper-style variants. This v1 rebuild expands from 417 unique original paired rows, includes Official anchors, retains a tiny MIMIC/eICU realism subset, keeps GPT-expanded capped, and uses more substantive conservative source-side variation.

Remaining weaknesses: Official still has only eight clean finalized base rows, NHANES remains a small source pool relative to its target count, and the MIMIC/eICU subset is included under an explicit demo-only exception because the prior governance layer did not mark those rows as formal backbone training rows. These limitations are made visible rather than hidden.
