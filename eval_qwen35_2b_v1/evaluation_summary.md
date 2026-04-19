# Qwen 0.8B v1 Evaluation Summary


## Split-level Summary


| split      |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| final_val  | 200 |             0.835    |                   0.835    |                  0.28     |                                    1 |                            0.984375 |
| test       | 101 |             0.742574 |                   0.742574 |                  0.277228 |                                    1 |                            1        |
| robustness |  99 |             0.838384 |                   0.838384 |                  0.313131 |                                    1 |                            0.983051 |


## Metrics by Resource Type


| resource_type   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| Condition       |  45 |             1        |                   1        |                  0.133333 |                                  nan |                          nan        |
| Observation     | 277 |             0.877256 |                   0.877256 |                  0.281588 |                                    1 |                            0.987654 |
| Patient         |  78 |             0.474359 |                   0.474359 |                  0.397436 |                                  nan |                          nan        |


## Metrics by Source Dataset


| source_dataset   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| gpt_expanded     |  39 |             0.846154 |                   0.846154 |                  0.384615 |                                    1 |                            1        |
| mimic_eicu       |   3 |             1        |                   1        |                  1        |                                    1 |                            1        |
| nhanes           |  86 |             1        |                   1        |                  0.918605 |                                    1 |                            0.983051 |
| official         |  24 |             1        |                   1        |                  0.75     |                                    1 |                            0.888889 |
| synthea          | 248 |             0.721774 |                   0.721774 |                  0        |                                    1 |                            1        |