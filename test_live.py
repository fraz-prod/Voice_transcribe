"""Test extraction with live Vosk output"""
import sys
import os
sys.path.append(os.getcwd())

from ai_services import LocalAIService

# Read live transcript
with open("live.txt", "r") as f:
    live = f.read()

print("="*60)
print("TESTING EXTRACTION ON LIVE VOSK OUTPUT")
print("="*60)

data = LocalAIService.extract_data(live)

print("\n=== EXTRACTED VITALS ===")
print(f"vitals_pre: {data.get('vitals_pre')}")
print(f"vitals_post: {data.get('vitals_post')}")
print(f"ecg: {data.get('ecg')}")
print(f"labs: {data.get('labs')}")
print(f"pregnancy: {data.get('pregnancy')}")
print(f"injection: {data.get('injection')}")
print(f"injection_2: {data.get('injection_2')}")
