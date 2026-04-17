# Synthea Agreement Summary

- Source file used: `synthea_anomalies_merged.csv`
- Reviewed rows: 14
- Rows needing adjudication: 0 (0.0%)
- Rows with full agreement on binary reliability dimensions: 14
- Rows with any disagreement: 6
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
- Linear weighted kappa: 0.478 (moderate)

## Completeness Check

- No blank values were found in the required reviewer fields.

## Recommendation

- The reviewed subset looks stable enough for downstream use after only light adjudication on the flagged rows.
