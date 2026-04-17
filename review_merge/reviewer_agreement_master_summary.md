# Reviewer Agreement Master Summary

This summary compares reviewer agreement across the five completed datasets using raw agreement, Cohen's kappa, linear weighted kappa for naturalness, and adjudication burden.

| Dataset | Rows | Decision agreement | Decision kappa | Naturalness weighted kappa | Adjudication rate | Agreed keep rate | Pending adjudication |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Synthea | 14 | 100.0% | 1.000 | 0.478 | 0.0% | 100.0% | 0.0% |
| Official | 16 | 12.5% | 0.000 | 0.778 | 87.5% | 0.0% | 87.5% |
| nhanes | 20 | 70.0% | 0.000 | 0.000 | 30.0% | 70.0% | 30.0% |
| gpt_expanded | 49 | 12.2% | 0.000 | 0.018 | 87.8% | 12.2% | 87.8% |
| MIMIC/eICU demo | 14 | 100.0% | 1.000 | 0.857 | 0.0% | 100.0% | 0.0% |

- Most stable dataset by decision agreement: **Synthea** (with MIMIC/eICU also clean on agreement, but still demo-only).
- Highest adjudication burden: **gpt_expanded**.

## Cross-Dataset Read

- Synthea and Official are the main reference point. Their decision kappas are 1.000 and 0.000, with adjudication rates of 0.0% and 87.5%.
- GPT-expanded clearly requires more caution than Synthea: its decision kappa is 0.000 and 87.8% of rows are still pending adjudication. NHANES is materially cleaner than GPT-expanded and far cleaner than Official on adjudication burden, but it still needs more caution than Synthea because 30.0% of rows are disposition disagreements awaiting adjudication.
- MIMIC/eICU is clean on reviewer agreement (1.000 decision kappa) and has 0.0% pending adjudication, but it remains demo-only. Treat it as, at most, a small low-weight subset rather than formal training material.

## Immediately Usable vs Pending

- **Synthea**: keep-now 100.0%, agreed-revise 0.0%, agreed-drop 0.0%, pending adjudication 0.0%.
- **Official**: keep-now 0.0%, agreed-revise 12.5%, agreed-drop 0.0%, pending adjudication 87.5%.
- **nhanes**: keep-now 70.0%, agreed-revise 0.0%, agreed-drop 0.0%, pending adjudication 30.0%.
- **gpt_expanded**: keep-now 12.2%, agreed-revise 0.0%, agreed-drop 0.0%, pending adjudication 87.8%.
- **MIMIC/eICU demo**: keep-now 100.0%, agreed-revise 0.0%, agreed-drop 0.0%, pending adjudication 0.0%.