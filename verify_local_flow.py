import sys
import os

# Ensure we can import from the directory
sys.path.append(os.getcwd())

from ai_services import LocalAIService
from form_filler import FormFiller

def test_local_flow():
    print("Testing Local Flow with sample.txt...")
    
    # Read sample.txt
    with open("sample.txt", "r") as f:
        transcript = f.read()
    
    print("\n--- Testing Extraction ---")
    data = LocalAIService.extract_data(transcript)
    
    print("\n=== EXTRACTED DATA ===")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    # Key field verification
    print("\n=== KEY FIELD VERIFICATION ===")
    checks = [
        ("Visit Date", data.get("visit_date"), "26 January 2026"),
        ("ECG HR", data.get("ecg", {}).get("hr"), "72"),
        ("ECG PR", data.get("ecg", {}).get("pr"), "160"),
        ("ECG RR", data.get("ecg", {}).get("rr"), "833"),
        ("ECG QRS", data.get("ecg", {}).get("qrs"), "90"),
        ("ECG QT", data.get("ecg", {}).get("qt"), "380"),
        ("Pregnancy Potential", data.get("pregnancy", {}).get("potential"), True),
        ("Pregnancy Result", data.get("pregnancy", {}).get("result"), "Negative"),
        ("Labs Date", data.get("labs", {}).get("date"), "26 January 2026"),
        ("Injection 1 Dose", data.get("injection", {}).get("dose"), "2 mL"),
        ("Injection 1 Laterality", data.get("injection", {}).get("laterality"), "left lower quadrant"),
        ("Injection 2 Dose", data.get("injection_2", {}).get("dose"), "2 mL"),
        ("Injection 2 Laterality", data.get("injection_2", {}).get("laterality"), "right lower quadrant"),
    ]
    
    for name, actual, expected in checks:
        status = "[OK]" if str(actual).lower() == str(expected).lower() else "[FAIL]"
        print(f"  {status} {name}: Expected '{expected}', Got '{actual}'")

if __name__ == "__main__":
    test_local_flow()
