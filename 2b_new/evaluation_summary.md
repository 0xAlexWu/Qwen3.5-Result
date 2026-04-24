# Qwen 2B v1 Evaluation Summary


## Split-level Summary


| split      |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| final_val  | 200 |             0.835    |                   0.835    |                  0.185    |                                    1 |                            0.945312 |
| test       | 101 |             0.732673 |                   0.732673 |                  0.227723 |                                    1 |                            0.892857 |
| robustness |  99 |             0.838384 |                   0.818182 |                  0.222222 |                                    1 |                            0.915254 |


## Metrics by Resource Type


| resource_type   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| Condition       |  45 |             0.977778 |                   0.933333 |                  0.133333 |                                  nan |                          nan        |
| Observation     | 277 |             0.877256 |                   0.877256 |                  0.169675 |                                    1 |                            0.925926 |
| Patient         |  78 |             0.474359 |                   0.474359 |                  0.371795 |                                  nan |                          nan        |


## Metrics by Source Dataset


| source_dataset   |   n |   json_validity_rate |   resource_type_match_rate |   exact_string_match_rate |   observation_value_exact_match_rate |   observation_unit_exact_match_rate |
|:-----------------|----:|---------------------:|---------------------------:|--------------------------:|-------------------------------------:|------------------------------------:|
| gpt_expanded     |  39 |             0.820513 |                   0.769231 |                  0.384615 |                                    1 |                            0.857143 |
| mimic_eicu       |   3 |             1        |                   1        |                  0        |                                    1 |                            0.666667 |
| nhanes           |  86 |             1        |                   1        |                  0.569767 |                                    1 |                            0.745763 |
| official         |  24 |             1        |                   1        |                  0.75     |                                    1 |                            0.944444 |
| synthea          | 248 |             0.721774 |                   0.721774 |                  0        |                                    1 |                            1        |