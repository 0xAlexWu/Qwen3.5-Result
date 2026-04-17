# nhanes Agreement Summary

- Source file used: `nhanes_manual_review_merged.csv`
- Reviewed rows: 20
- Rows needing adjudication: 6 (30.0%)
- Rows with full agreement on binary reliability dimensions: 20
- Rows with any disagreement: 20
- Rows with decision disagreement: 6

Kappa interpretation used:

- < 0.40 = weak
- 0.40-0.60 = moderate
- 0.61-0.80 = substantial
- > 0.80 = strong

Weighted kappa is reported with linear weights for naturalness. Weighted decision kappa is omitted because keep/revise/drop is treated as a disposition rather than a strictly ordinal label.

## Agreement Metrics

| Metric | Comparable rows | Raw agreement | Kappa | Interpretation |
| --- | ---: | ---: | ---: | --- |
| faithfulness | 20 | 100.0% | 1.000 | strong |
| unsupported_fact | 20 | 100.0% | 1.000 | strong |
| omission | 20 | 100.0% | 1.000 | strong |
| context_leakage | 20 | 100.0% | 1.000 | strong |
| decision | 20 | 70.0% | 0.000 | weak |

## Naturalness

- Comparable rows: 20
- Linear weighted kappa: 0.000 (weak)

## Completeness Check

- No blank values were found in the required reviewer fields.

## Recommendation

- The reviewed subset is usable after targeted adjudication; the decision labels are directionally stable, but unresolved rows should stay out of downstream training.
