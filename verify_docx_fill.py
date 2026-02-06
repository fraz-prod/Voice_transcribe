from form_filler import FormFiller
from ai_services import MockAIService
import os

template_path = "[Internal] of Astria STAR 0215-301 Day 1.docx"
output_path = "test_output.docx"

if not os.path.exists(template_path):
    print(f"Error: Template {template_path} not found.")
    exit(1)

print("Template found. Generating form...")
filler = FormFiller(template_path)
data = MockAIService.extract_data("dummy transcript")
filled_buffer = filler.fill_form(data, is_eligible=True)

with open(output_path, "wb") as f:
    f.write(filled_buffer.read())

if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
    print(f"Success! Generated {output_path} ({os.path.getsize(output_path)} bytes)")
else:
    print("Error: Output file creation failed.")
