import re

# Read the file
with open(r'c:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\ai_services.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line to insert after (line 592, which is index 592 since we're 0-indexed for the file content)
# Actually, line 593 is index 592
insert_after_line_index = 592  # This is line 593 in 1-indexed

# Prepare the new code to insert
new_code = """        elif "Orladeyo" in meds:
             data["last_dose"]["medication"] = "Orladeyo"
             
        # Extract last dose date in various formats
        if data["last_dose"].get("medication"):
            date_patterns = [
                r'last dose\\s+(?:was\\s+)?([A-Za-z]+\\s+\\d{1,2},?\\s*\\d{4})',  # "last dose January 15, 2025"
                r'last dose\\s+(?:was\\s+)?(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})',  # "last dose 15 January 2025"
                r'last dose\\s+(?:was\\s+)?(\\d{4}-\\d{2}-\\d{2})',  # "last dose 2025-01-15"
                r'(?:took|received|given)\\s+(?:Takhzyro|Orladeyo|medication)\\s+(?:on\\s+)?([A-Za-z]+\\s+\\d{1,2}(?:st|nd|rd|th)?,?\\s*\\d{4})',  # "took Takhzyro on January 15th, 2025"
                r'(?:took|received|given)\\s+(?:Takhzyro|Orladeyo|medication)\\s+(?:on\\s+)?(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})',  # "took Takhzyro on 15 January 2025"
                r'(?:took|received|given)\\s+(?:Takhzyro|Orladeyo|medication)\\s+(?:on\\s+)?(\\d{4}-\\d{2}-\\d{2})',  # "took Takhzyro on 2025-01-15"
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, transcript_clean, re.IGNORECASE)
                if date_match:
                    # Clean up the date string (remove ordinals like 'st', 'nd', 'rd', 'th')
                    date_str = date_match.group(1).strip()
                    date_str = re.sub(r'(\\d+)(?:st|nd|rd|th)', r'\\1', date_str)
                    data["last_dose"]["date"] = date_str
                    break
"""

# Insert the new code
lines_with_insertion = lines[:insert_after_line_index] + [new_code] + lines[insert_after_line_index:]

# Write back
with open(r'c:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\ai_services.py', 'w', encoding='utf-8') as f:
    f.writelines(lines_with_insertion)

print("✅ Successfully added last_dose date extraction logic!")
