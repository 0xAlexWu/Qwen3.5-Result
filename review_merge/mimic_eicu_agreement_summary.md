# MIMIC/eICU demo Agreement Summary

- Source file used: `mimic_eicu_merged.csv`
- Reviewed rows: 14
- Rows needing adjudication: 0 (0.0%)
- Rows with full agreement on binary reliability dimensions: 14
- Rows with any disagreement: 1
- Rows with decision disagreement: 0

Kappa interpretation used:

- < 0.40 = weak
- 0.40-0.60 = moderate
- 0.61-0.80 = substantial
- > 0.80 = strong

Weighted kappa is reported with linear weights for naturalness. Weighted decision kappa is omitted because keep/revise/drop is treated as a disposition rather than a strictly ordinal label.

## Agreement Metrics

| Metric | Comparable rows | Raw agreement | Kappa | Interpretation |
| --- | ---: | ---: | ---: | --- |
| faithfulness | 14 | 100.0% | 1.000 | strong |
| unsupported_fact | 14 | 100.0% | 1.000 | strong |
| omission | 14 | 100.0% | 1.000 | strong |
| context_leakage | 14 | 100.0% | 1.000 | strong |
| decision | 14 | 100.0% | 1.000 | strong |

## Naturalness

- Comparable rows: 14
- Linear weighted kappa: 0.857 (strong)

## Completeness Check

- No blank values were found in the required reviewer fields.

## Recommendation

- Agreement is high, but this remains demo-only source material. Keep it low-weight and out of formal training until a non-demo sample and adjudication policy are in place.
