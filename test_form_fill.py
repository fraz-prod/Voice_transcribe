"""Test form filling with Gemini-extracted data"""
import os
from dotenv import load_dotenv
from ai_services import GeminiAIService
from form_filler import FormFiller
import json

load_dotenv()

# Read sample transcript
with open('sample.txt', 'r') as f:
    transcript = f.read()

# Extract with Gemini
gemini_api_key = os.getenv('GEMINI_API_KEY')
service = GeminiAIService(gemini_api_key)

print("Extracting data with Gemini...")
extracted_data = service.extract_data(transcript)

print("\nExtracted injection data:")
print(json.dumps(extracted_data.get("injection", {}), indent=2))
print(json.dumps(extracted_data.get("injection_2", {}), indent=2))

print("\nExtracted notes:")
print(extracted_data.get("notes", "NOT FOUND"))

# Fill form
template_path = "[Internal] of Astria STAR 0215-301 Day 1.docx"
if os.path.exists(template_path):
    print(f"\nFilling form with template: {template_path}")
    filler = FormFiller(template_path)
    filled_doc = filler.fill_form(extracted_data, is_eligible=True)
    
    # Save to test file
    test_output = "test_gemini_filled.docx"
    with open(test_output, 'wb') as f:
        f.write(filled_doc.read())
    
    print(f"\n✓ Form saved to: {test_output}")
    print("\nPlease open the document and check:")
    print("  1. Are injection 1 and 2 fields filled?")
    print("  2. Is the Notes section filled?")
else:
    print(f"\nERROR: Template not found: {template_path}")
