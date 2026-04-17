# Final Training Readiness Summary

## Ready Now

- **Synthea**: ready now. All 14 reviewed rows land in `use_now`, matching the policy that clean Synthea rows should enter formal training immediately.
- **NHANES clean subset**: 14 rows are already usable now, while the remaining pending rows stay out of the immediate bucket until targeted adjudication is finished.

## Targeted Adjudication Needed

- **NHANES**: 6 rows belong in `use_after_revision`. This is the best next adjudication target because the queue is small and mostly repairable.
- **Official**: 2 rows are potentially salvageable after revision or adjudication, but the source still has a much heavier unresolved burden than NHANES.
- **GPT-expanded**: 28 rows are only tentatively salvageable. They should not be promoted until cleaner sources are finalized and the larger pending queue is materially reduced.

## Do Not Use Yet

- **Official**: 14 rows remain excluded for now because unresolved disagreements frequently involve unsupported facts or leakage-like concerns.
- **GPT-expanded**: 15 rows are excluded for now under the conservative policy for large pending disagreement queues.
- **MIMIC/eICU demo**: all 14 reviewed rows remain out of formal training. Even though agreement is clean, this source stays demo-only or very low-weight only.

## Operational Recommendation

Use Synthea immediately as the first formal training source. Add the clean NHANES subset now if you want a second source, but prioritize adjudicating the remaining NHANES queue before spending reviewer effort on Official or GPT-expanded.

Keep Official in a controlled revision lane rather than broad deployment. Treat GPT-expanded as deferred source material: a few rows are individually clean, but the dataset line should not yet be treated as training-ready while so many pending rows remain unresolved.

Do not use MIMIC/eICU as backbone training material; at most, reserve it for demo-only evaluation or a tiny low-weight realism subset under separate policy.

This summary translates the existing agreement and adjudication outputs into an operational training recommendation without recomputing reviewer-agreement metrics.
