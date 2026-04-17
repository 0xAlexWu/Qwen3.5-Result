# Official Agreement Summary

- Source file used: `official_anomalies_merged.csv`
- Reviewed rows: 16
- Rows needing adjudication: 14 (87.5%)
- Rows with full agreement on binary reliability dimensions: 0
- Rows with any disagreement: 16
- Rows with decision disagreement: 14

Kappa interpretation used:

- < 0.40 = weak
- 0.40-0.60 = moderate
- 0.61-0.80 = substantial
- > 0.80 = strong

Weighted kappa is reported with linear weights for naturalness. Weighted decision kappa is omitted because keep/revise/drop is treated as a disposition rather than a strictly ordinal label.

## Agreement Metrics

| Metric | Comparable rows | Raw agreement | Kappa | Interpretation |
| --- | ---: | ---: | ---: | --- |
| faithfulness | 16 | 75.0% | 0.000 | weak |
| unsupported_fact | 16 | 25.0% | 0.000 | weak |
| omission | 16 | 56.2% | 0.000 | weak |
| context_leakage | 16 | 87.5% | 0.600 | moderate |
| decision | 16 | 12.5% | 0.000 | weak |

## Naturalness

- Comparable rows: 16
- Linear weighted kappa: 0.778 (substantial)

## Completeness Check

- No blank values were found in the required reviewer fields.

## Recommendation

- The reviewed subset needs adjudication before downstream use because reviewer decisions are not yet stable enough.
