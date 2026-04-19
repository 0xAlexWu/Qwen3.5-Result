# Qwen 0.8B vs 2B v1 Comparison

Artifacts compare training curves, token accuracy, split-level structured metrics, source-dataset metrics, and resource-type metrics.

## Split-level comparison
split,n_08b,json_validity_rate_08b,resource_type_match_rate_08b,exact_string_match_rate_08b,observation_value_exact_match_rate_08b,observation_unit_exact_match_rate_08b,n_2b,json_validity_rate_2b,resource_type_match_rate_2b,exact_string_match_rate_2b,observation_value_exact_match_rate_2b,observation_unit_exact_match_rate_2b
final_val,200,0.835,0.835,0.445,1.0,0.9921875,200,0.835,0.835,0.28,1.0,0.984375
test,101,0.7425742574257426,0.7425742574257426,0.4851485148514851,1.0,1.0,101,0.7425742574257426,0.7425742574257426,0.2772277227722772,1.0,1.0
robustness,99,0.8383838383838383,0.8383838383838383,0.4646464646464646,1.0,0.9830508474576272,99,0.8383838383838383,0.8383838383838383,0.3131313131313131,1.0,0.9830508474576272


## Resource-type comparison
resource_type,n_08b,json_validity_rate_08b,resource_type_match_rate_08b,exact_string_match_rate_08b,observation_value_exact_match_rate_08b,observation_unit_exact_match_rate_08b,n_2b,json_validity_rate_2b,resource_type_match_rate_2b,exact_string_match_rate_2b,observation_value_exact_match_rate_2b,observation_unit_exact_match_rate_2b
Condition,45,1.0,1.0,0.5111111111111111,,,45,1.0,1.0,0.1333333333333333,,
Observation,277,0.8772563176895307,0.8772563176895307,0.4657039711191336,1.0,0.9917695473251028,277,0.8772563176895307,0.8772563176895307,0.2815884476534296,1.0,0.9876543209876544
Patient,78,0.4743589743589743,0.4743589743589743,0.4102564102564102,,,78,0.4743589743589743,0.4743589743589743,0.3974358974358974,,


## Source-dataset comparison
source_dataset,n_08b,json_validity_rate_08b,resource_type_match_rate_08b,exact_string_match_rate_08b,observation_value_exact_match_rate_08b,observation_unit_exact_match_rate_08b,n_2b,json_validity_rate_2b,resource_type_match_rate_2b,exact_string_match_rate_2b,observation_value_exact_match_rate_2b,observation_unit_exact_match_rate_2b
gpt_expanded,39,0.8461538461538461,0.8461538461538461,0.8461538461538461,1.0,1.0,39,0.8461538461538461,0.8461538461538461,0.3846153846153846,1.0,1.0
mimic_eicu,3,1.0,1.0,0.6666666666666666,1.0,0.6666666666666666,3,1.0,1.0,1.0,1.0,1.0
nhanes,86,1.0,1.0,0.9418604651162792,1.0,1.0,86,1.0,1.0,0.9186046511627908,1.0,0.9830508474576272
official,24,1.0,1.0,0.875,1.0,0.9444444444444444,24,1.0,1.0,0.75,1.0,0.8888888888888888
synthea,248,0.7217741935483871,0.7217741935483871,0.189516129032258,1.0,1.0,248,0.7217741935483871,0.7217741935483871,0.0,1.0,1.0
