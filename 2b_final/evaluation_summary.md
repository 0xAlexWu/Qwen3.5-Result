# Qwen 2B v1 Evaluation Summary


## Split-level Summary


| split      |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| final_val  | 200 |             0.81     |                   0.81     |                  0.175    |                                    1 |                            0.945312 |
| test       | 101 |             0.722772 |                   0.722772 |                  0.168317 |                                    1 |                            0.892857 |
| robustness |  99 |             0.838384 |                   0.838384 |                  0.232323 |                                    1 |                            0.915254 |


## Metrics by Resource Type


| resource_type   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| Condition       |  45 |             1        |                   1        |                 0.0666667 |                                  nan |                          nan        |
| Observation     | 277 |             0.877256 |                   0.877256 |                 0.169675  |                                    1 |                            0.925926 |
| Patient         |  78 |             0.384615 |                   0.384615 |                 0.320513  |                                  nan |                          nan        |


## Metrics by Source Dataset


| source_dataset   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| gpt_expanded     |  39 |             0.846154 |                   0.846154 |                  0.307692 |                                    1 |                            1        |
| mimic_eicu       |   3 |             1        |                   1        |                  0.333333 |                                    1 |                            1        |
| nhanes           |  86 |             0.918605 |                   0.918605 |                  0.55814  |                                    1 |                            0.745763 |
| official         |  24 |             1        |                   1        |                  0.583333 |                                    1 |                            0.833333 |
| synthea          | 248 |             0.721774 |                   0.721774 |                  0        |                                    1 |                            1        |