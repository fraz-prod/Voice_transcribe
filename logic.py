from datetime import datetime
from typing import List, Dict, Optional, Any
from utils import add_days

class WashoutCalculator:
    # Guidelines from the user prompt
    WASHOUT_PERIODS = {
        "Oral androgens/antifibrinolytics": 3,
        "Tranexamic acid": 3,
        "Danazol": 3,
        "Stanazolol": 3,
        "Plasma-derived C1-INH": 14,
        "Cinryze": 14,
        "Haegarda": 14,
        "Berinert": 14,
        "Berotralstat": 21,
        "Orladeyo": 21,
        "Lanadelumab": 70,
        "Takhzyro": 70,
        "Garadacimab": 90
    }

    @staticmethod
    def get_washout_period(medication_name: str) -> int:
        for key, days in WashoutCalculator.WASHOUT_PERIODS.items():
            if key.lower() in medication_name.lower():
                return days
        return 0 # Default if found

    @staticmethod
    def calculate_end_date(medication_name: str, last_dose_date: datetime) -> Dict[str, Any]:
        days = WashoutCalculator.get_washout_period(medication_name)
        end_date = add_days(last_dose_date, days)
        return {
            "medication": medication_name,
            "washout_days": days,
            "end_date": end_date
        }

class RuleEngine:
    @staticmethod
    def check_eligibility(extracted_data: Dict[str, Any]) -> List[Dict[str, str]]:
        results = []
        
        # Inclusion #2: Age >= 12
        age = extracted_data.get("age")
        if age is not None:
            if age >= 12:
                results.append({"criteria": "Inclusion #2: Age ≥12", "status": "Pass", "notes": f"Age is {age}"})
            else:
                results.append({"criteria": "Inclusion #2: Age ≥12", "status": "Fail", "notes": f"Age is {age}"})
        
        # Inclusion #3: HAE Type 1 or 2
        hae_type = extracted_data.get("hae_type", "").lower()
        if "type 1" in hae_type or "type 2" in hae_type:
            results.append({"criteria": "Inclusion #3: HAE Type 1 or 2", "status": "Pass", "notes": f"Type is {hae_type}"})
        elif hae_type:
             results.append({"criteria": "Inclusion #3: HAE Type 1 or 2", "status": "Fail", "notes": f"Type is {hae_type}"})

        # Exclusion #6: ACE inhibitor use
        meds = extracted_data.get("medications", [])
        ace_inhibitors = ["lisinopril", "enalapril", "ramipril", "benazepril"]
        found_ace = False
        for med in meds:
            for ace in ace_inhibitors:
                if ace in med.lower():
                    results.append({"criteria": "Exclusion #6: ACE inhibitor use", "status": "Fail", "notes": f"Taking {med}"})
                    found_ace = True
                    break
        if not found_ace:
             results.append({"criteria": "Exclusion #6: ACE inhibitor use", "status": "Pass", "notes": "No ACE inhibitors detected"})

        # Determine Overall Eligibility
        # Overall Pass if ALL criteria are "Pass"
        overall_status = all(r['status'] == 'Pass' for r in results)

        return results, overall_status
