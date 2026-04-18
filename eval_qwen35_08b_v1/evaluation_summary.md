# Qwen 0.8B v1 Evaluation Summary


## Split-level Summary


| split      |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| final_val  | 200 |             0.835    |                   0.835    |                  0.445    |                                    1 |                            0.992188 |
| test       | 101 |             0.742574 |                   0.742574 |                  0.485149 |                                    1 |                            1        |
| robustness |  99 |             0.838384 |                   0.838384 |                  0.464646 |                                    1 |                            0.983051 |


## Metrics by Resource Type


| resource_type   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| Condition       |  45 |             1        |                   1        |                  0.511111 |                                  nan |                           nan       |
| Observation     | 277 |             0.877256 |                   0.877256 |                  0.465704 |                                    1 |                             0.99177 |
| Patient         |  78 |             0.474359 |                   0.474359 |                  0.410256 |                                  nan |                           nan       |


## Metrics by Source Dataset


| source_dataset   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| gpt_expanded     |  39 |             0.846154 |                   0.846154 |                  0.846154 |                                    1 |                            1        |
| mimic_eicu       |   3 |             1        |                   1        |                  0.666667 |                                    1 |                            0.666667 |
| nhanes           |  86 |             1        |                   1        |                  0.94186  |                                    1 |                            1        |
| official         |  24 |             1        |                   1        |                  0.875    |                                    1 |                            0.944444 |
| synthea          | 248 |             0.721774 |                   0.721774 |                  0.189516 |                                    1 |                            1        |