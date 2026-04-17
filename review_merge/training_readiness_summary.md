# Training Readiness Summary

These groupings are based on reviewer agreement, adjudication burden, and any dataset-specific constraints such as demo-only status.

## safe_to_use_now

- **Synthea**: decision kappa 1.000, adjudication rate 0.0%, immediately usable keep rate 100.0%. The reviewed subset looks stable enough for downstream use after only light adjudication on the flagged rows.

## use_after_adjudication

- **nhanes**: decision kappa 0.000, adjudication rate 30.0%, immediately usable keep rate 70.0%. The reviewed subset is usable after targeted adjudication; the decision labels are directionally stable, but unresolved rows should stay out of downstream training.

## do_not_use_for_formal_training_yet

- **Official**: decision kappa 0.000, adjudication rate 87.5%, immediately usable keep rate 0.0%. The reviewed subset needs adjudication before downstream use because reviewer decisions are not yet stable enough.
- **gpt_expanded**: decision kappa 0.000, adjudication rate 87.8%, immediately usable keep rate 12.2%. The reviewed subset needs adjudication before downstream use because reviewer decisions are not yet stable enough.
- **MIMIC/eICU demo**: decision kappa 1.000, adjudication rate 0.0%, immediately usable keep rate 100.0%. Agreement is high, but this remains demo-only source material. Keep it low-weight and out of formal training until a non-demo sample and adjudication policy are in place.
