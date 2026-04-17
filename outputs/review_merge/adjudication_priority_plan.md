# Adjudication Priority Plan

## Queue Ranking

1. **NHANES** (6 rows pending): resolve first. It has the lightest remaining adjudication burden among the non-empty queues, most unresolved rows are disposition-only, and finishing it quickly unlocks a mostly clean dataset line for formal training.
2. **Official** (14 rows pending): resolve second. It is important reference material, but its unresolved rows carry more unsupported-fact and leakage concerns than NHANES, so the cleanup cost per usable row is higher.
3. **GPT-expanded** (43 rows pending): defer until the cleaner sources are finalized. The queue is large and noisy, so adjudicating it early would consume attention before the higher-confidence sources are stabilized.

NHANES should likely be resolved before Official or GPT-expanded because the remaining queue is smaller, the disagreement pattern is mostly targeted and disposition-only, and the expected yield of quickly promotable training rows is higher.

GPT-expanded should be deferred until Synthea and NHANES are finalized, and until a meaningful share of Official is adjudicated. Even where some GPT-expanded rows look individually clean, the dataset line as a whole is still too adjudication-heavy to serve as a backbone source.

Synthea is ready for immediate training use now. Its reviewed rows are already stable enough to populate the first formal bucket without additional reviewer-agreement work.

MIMIC/eICU should remain demo-only or, at most, a very small low-weight realism subset. It should not be promoted into the backbone formal training mix at this stage.

## Operational Read

- `Synthea`: immediate use now (14 rows in `use_now`).
- `NHANES`: targeted adjudication next (6 rows in `use_after_revision`).
- `Official`: hold broader use until heavier adjudication is completed (14 rows already conservatively excluded).
- `GPT-expanded`: defer broad training use while the large pending queue remains unresolved.
- `MIMIC/eICU demo`: keep out of formal training despite clean review agreement.

Reviewer-agreement metrics above are reused from the existing master summary and are not recomputed here.
