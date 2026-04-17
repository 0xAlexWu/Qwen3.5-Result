# gpt_expanded Agreement Summary

- Source file used: `gpt_expanded_merged.csv`
- Reviewed rows: 49
- Rows needing adjudication: 43 (87.8%)
- Rows with full agreement on binary reliability dimensions: 34
- Rows with any disagreement: 48
- Rows with decision disagreement: 43

Kappa interpretation used:

- < 0.40 = weak
- 0.40-0.60 = moderate
- 0.61-0.80 = substantial
- > 0.80 = strong

Weighted kappa is reported with linear weights for naturalness. Weighted decision kappa is omitted because keep/revise/drop is treated as a disposition rather than a strictly ordinal label.

## Agreement Metrics

| Metric | Comparable rows | Raw agreement | Kappa | Interpretation |
| --- | ---: | ---: | ---: | --- |
| faithfulness | 49 | 100.0% | 1.000 | strong |
| unsupported_fact | 49 | 95.9% | 0.000 | weak |
| omission | 49 | 93.9% | 0.000 | weak |
| context_leakage | 49 | 75.5% | 0.109 | weak |
| decision | 49 | 12.2% | 0.000 | weak |

## Naturalness

- Comparable rows: 49
- Linear weighted kappa: 0.018 (weak)

## Completeness Check

- No blank values were found in the required reviewer fields.

## Recommendation

- The reviewed subset needs adjudication before downstream use because reviewer decisions are not yet stable enough.
