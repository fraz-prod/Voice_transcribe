from datetime import datetime
from typing import List, Dict, Optional, Any
from utils import add_days

class WashoutCalculator:
    # Hardcoded fallback — used when no protocol document is provided
    DEFAULT_WASHOUT_PERIODS = {
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

    # Brand name → generic name aliases.
    # Protocols typically list the generic name; transcripts often use brand names.
    # This map lets the calculator match either form.
    BRAND_TO_GENERIC = {
        "takhzyro": "lanadelumab",
        "orladeyo": "berotralstat",
        "cinryze": "plasma-derived c1-inh",
        "haegarda": "plasma-derived c1-inh",
        "berinert": "plasma-derived c1-inh",
        "ruconest": "conestat alfa",
        "kalbitor": "ecallantide",
        "firazyr": "icatibant",
        "sajazir": "icatibant",
        "garadacimab": "garadacimab",   # same brand/generic
        "danazol": "danazol",
        "stanazolol": "stanazolol",
    }

    @staticmethod
    def _resolve_name(medication_name: str) -> list:
        """
        Return a list of name variants to try when matching.
        Includes the original name AND the generic equivalent (if brand name is known).
        E.g. 'Takhzyro' → ['takhzyro', 'lanadelumab']
        """
        med_lower = (medication_name or "").lower().strip()
        variants = [med_lower]
        generic = WashoutCalculator.BRAND_TO_GENERIC.get(med_lower)
        if generic and generic not in variants:
            variants.append(generic)
        return variants

    @staticmethod
    def get_washout_period(medication_name: str, protocol_washout_periods: list = None) -> Dict[str, Any]:
        """
        Look up washout period for a medication.

        Handles brand name ↔ generic name mismatches automatically.
        E.g. last_dose = 'Takhzyro' but protocol lists 'Lanadelumab' — still matches.

        Returns a dict with:
          - days (int or None)
          - source: 'protocol'             → found in uploaded protocol (gold standard)
                    'no_protocol_estimate' → no protocol uploaded, using hardcoded estimate
                    'not_in_protocol'      → protocol was uploaded but this med not found in it
          - matched_as: which name variant got the match (for display)
        """
        # Build list of name variants (brand + generic) to try
        variants = WashoutCalculator._resolve_name(medication_name)

        # CASE 1: Protocol was uploaded — use ONLY protocol-extracted periods
        if protocol_washout_periods is not None:
            for entry in protocol_washout_periods:
                proto_med = (entry.get("medication") or "").lower().strip()
                proto_days = entry.get("washout_days", 0)
                if not proto_med:
                    continue
                # Try every variant of the input medication name
                for variant in variants:
                    if proto_med in variant or variant in proto_med:
                        try:
                            return {
                                "days": int(proto_days),
                                "source": "protocol",
                                "matched_as": f"{medication_name} → {proto_med}"
                            }
                        except (ValueError, TypeError):
                            pass
            # Protocol was provided but this medication was not found in it (under any name)
            return {"days": None, "source": "not_in_protocol", "matched_as": None}

        # CASE 2: No protocol uploaded — use hardcoded defaults as rough estimate only
        for key, days in WashoutCalculator.DEFAULT_WASHOUT_PERIODS.items():
            for variant in variants:
                if key.lower() in variant or variant in key.lower():
                    return {"days": days, "source": "no_protocol_estimate", "matched_as": key}

        return {"days": 0, "source": "no_protocol_estimate", "matched_as": None}

    @staticmethod
    def calculate_end_date(medication_name: str, last_dose_date: datetime, protocol_washout_periods: list = None) -> Dict[str, Any]:
        result = WashoutCalculator.get_washout_period(medication_name, protocol_washout_periods)
        days = result["days"]
        source = result["source"]

        if days is not None:
            end_date = add_days(last_dose_date, days)
        else:
            end_date = None

        return {
            "medication": medication_name,
            "washout_days": days,
            "end_date": end_date,
            "source": source
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
        hae_type = (extracted_data.get("hae_type") or "").lower()
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
                if ace in (med or "").lower():
                    results.append({"criteria": "Exclusion #6: ACE inhibitor use", "status": "Fail", "notes": f"Taking {med}"})
                    found_ace = True
                    break
        if not found_ace:
             results.append({"criteria": "Exclusion #6: ACE inhibitor use", "status": "Pass", "notes": "No ACE inhibitors detected"})

        # Determine Overall Eligibility
        # Overall Pass if ALL criteria are "Pass"
        overall_status = all(r['status'] == 'Pass' for r in results)

        return results, overall_status
