from logic import WashoutCalculator, RuleEngine
from datetime import datetime

# Test Washout
date = datetime(2025, 1, 15)
res = WashoutCalculator.calculate_end_date("Takhzyro", date)
print(f"Washout: {res}")
assert res['washout_days'] == 70, "Washout days should be 70 for Takhzyro"
assert res['end_date'].strftime('%Y-%m-%d') == '2025-03-26', "End date calculation incorrect"

# Test Rules
data = {"age": 34, "hae_type": "Type 1", "medications": ["lisinopril"]}
res = RuleEngine.check_eligibility(data)
print(f"Rules: {res}")

# Check Exclusion #6
ace_result = next((r for r in res if "Exclusion #6" in r['criteria']), None)
assert ace_result is not None, "Exclusion #6 not found"
assert ace_result['status'] == 'Fail', "Lisinopril should trigger failure"

print("All tests passed!")
