# Qwen 4B v1 Evaluation Summary


## Split-level Summary


| split      |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| final_val  | 200 |             0.31     |                   0.16     |                  0.005    |                             0.5      |                            0.434783 |
| test       | 101 |             0.356436 |                   0.158416 |                  0        |                             0.392857 |                            0.357143 |
| robustness |  99 |             0.373737 |                   0.161616 |                  0.010101 |                             0.416667 |                            0.375    |


## Metrics by Resource Type


| resource_type   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| Condition       |  45 |             0.466667 |                   0.266667 |                  0        |                            nan       |                          nan        |
| Observation     | 277 |             0.353791 |                   0.155235 |                  0        |                              0.44898 |                            0.397959 |
| Patient         |  78 |             0.205128 |                   0.115385 |                  0.025641 |                            nan       |                          nan        |


## Metrics by Source Dataset


| source_dataset   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| gpt_expanded     |  39 |             0.307692 |                  0.102564  |                 0         |                             0        |                            0        |
| mimic_eicu       |   3 |             0        |                  0         |                 0         |                           nan        |                          nan        |
| nhanes           |  86 |             0.337209 |                  0.139535  |                 0.0232558 |                             0.421053 |                            0.157895 |
| official         |  24 |             0.291667 |                  0.0416667 |                 0         |                             0.166667 |                            0.166667 |
| synthea          | 248 |             0.350806 |                  0.189516  |                 0         |                             0.5      |                            0.5      |