"""
Test script to verify Gemini 2.0 Flash integration for form extraction
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
from dotenv import load_dotenv
from ai_services import GeminiAIService
import json

# Load environment variables
load_dotenv()

# Read sample transcript
with open('sample.txt', 'r') as f:
    transcript = f.read()

# Initialize Gemini service
gemini_api_key = os.getenv('GEMINI_API_KEY')
if not gemini_api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

print("Initializing Gemini service...")
service = GeminiAIService(gemini_api_key)

print("\nExtracting data from transcript...")
print("=" * 80)

try:
    extracted_data = service.extract_data(transcript)
    
    print("\n[SUCCESS] EXTRACTION SUCCESSFUL!")
    print("\nExtracted Data:")
    print(json.dumps(extracted_data, indent=2))
    
    # Verify key fields
    print("\n" + "=" * 80)
    print("KEY FIELD VERIFICATION:")
    print("=" * 80)
    
    checks = {
        "Subject ID": extracted_data.get("subject_id"),
        "Visit Date": extracted_data.get("visit_date"),
        "Pre-dose Weight": extracted_data.get("vitals_pre", {}).get("weight"),
        "Pre-dose BP": extracted_data.get("vitals_pre", {}).get("bp"),
        "Post-dose Weight": extracted_data.get("vitals_post", {}).get("weight"),
        "ECG HR": extracted_data.get("ecg", {}).get("hr"),
        "ECG PR": extracted_data.get("ecg", {}).get("pr"),
        "Injection 1 Dose": extracted_data.get("injection", {}).get("dose"),
        "Injection 2 Dose": extracted_data.get("injection_2", {}).get("dose"),
        "Notes": extracted_data.get("notes"),
    }
    
    for field, value in checks.items():
        status = "[OK]" if value else "[MISSING]"
        print(f"{status} {field}: {value}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR]: {e}")
    import traceback
    traceback.print_exc()
