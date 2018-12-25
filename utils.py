import json
import os
import pprint
import re
import sys

def NormalAge(eli, age_list=["minimum_age","maximum_age"]):
    for age in age_list:
        if age in eli:
            if eli[age] == "N/A":
                eli[age] = 0
            else:
                ageset = eli[age].split(" ")
                if ageset[1] == "Years":
                    eli[age] = str(round(float(ageset[0]), 3))
                elif ageset[1] == "Months":
                    eli[age] == str(round(float(ageset[0])/12, 3))
    return eli

if __name__ == "__main__":
    eli = {
            "criteria": {
                "textblock": "Inclusion Criteria:\\n\\n          -  diagnosed with Congenital Adrenal Hyperplasia (CAH)\\n\\n      -  normal ECG during baseline evaluation\\n\\n        Exclusion Criteria:\\n\\n-  history of liver disease, or elevated liver function tests\\n\\n          -  history of cardiovascular disease"
            },
            "gender": "All",
            "minimum_age": "14 Years",
            "maximum_age": "35 Years",
            "healthy_volunteers": "No"
        }

    print(NormalAge(eli))
            
