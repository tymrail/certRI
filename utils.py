import json
import os
import pprint
import re
import sys

def NormalAge(eli, age_list=["minimum_age","maximum_age"]):
    eli["minimum_age"] = NormAge(eli["minimum_age"], 0)
    eli["maximum_age"] = NormAge(eli["maximum_age"], 200*365)
                
    return eli

def NormAge(age_str, default_age):
    units = {
        'Year': 365,
        'Years': 365,
        'Month': 30,
        'Months': 30,
        'Week': 7,
        'Weeks': 7,
        'Day': 1,
        'Days': 1,
        'Hour': 1 / 24,
        'Hours': 1 / 24,
        'Minute': 1 / 24 / 60,
        'Minutes': 1 / 24 / 60,
    }

    pattern = "([1-9]*[0-9]+) (Year|Years|Month|Months|Week|Weeks|Day|Days|Hour|Hours|Minute|Minutes)"
    
    norm_age = default_age
    if age_str != 'N/A' and age_str:
        m = re.match(pattern, age_str)
        norm_age = str(int(m.group(1)) * units[m.group(2)])
    return norm_age


if __name__ == "__main__":
    eli = {
            "criteria": {
                "textblock": "Inclusion Criteria:\\n\\n          -  diagnosed with Congenital Adrenal Hyperplasia (CAH)\\n\\n      -  normal ECG during baseline evaluation\\n\\n        Exclusion Criteria:\\n\\n-  history of liver disease, or elevated liver function tests\\n\\n          -  history of cardiovascular disease"
            },
            "gender": "All",
            "minimum_age": "18 Hours",
            "maximum_age": "1 Year",
            "healthy_volunteers": "No"
        }

    print(NormalAge(eli))
            
