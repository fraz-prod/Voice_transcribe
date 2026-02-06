"""Debug word-to-num conversion"""
import re

def word_to_num(text):
    result = text
    # Handle "one eighteen" -> "118"
    result = re.sub(r'\bone hundred\b', '100', result, flags=re.IGNORECASE)
    result = re.sub(r'\bone eighteen\b', '118', result, flags=re.IGNORECASE)
    result = re.sub(r'\bone twenty\b', '120', result, flags=re.IGNORECASE)
    
    # Handle tens + units: "seventy eight" -> "78"
    for tens_word, tens_val in [('twenty', '2'), ('thirty', '3'), ('forty', '4'), 
                                  ('fifty', '5'), ('sixty', '6'), ('seventy', '7'),
                                  ('eighty', '8'), ('ninety', '9')]:
        for unit_word, unit_val in [('one', '1'), ('two', '2'), ('three', '3'), 
                                      ('four', '4'), ('five', '5'), ('six', '6'),
                                      ('seven', '7'), ('eight', '8'), ('nine', '9')]:
            pattern = tens_word + r'\s*' + unit_word
            replacement = tens_val + unit_val
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Handle standalone tens
    word_nums = {
        'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50', 
        'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'sixteen': '16'
    }
    for word, val in word_nums.items():
        result = re.sub(r'\b' + word + r'\b', val, result, flags=re.IGNORECASE)
    
    # Handle "X over Y" for BP
    result = re.sub(r'(\d+)\s+over\s+(\d+)', r'\1/\2', result)
    
    return result

# Test with live transcript
live = open("live.txt").read()
converted = word_to_num(live)

# Show a section to see conversion
print("=== SAMPLE OF CONVERTED TEXT ===")
print(converted[1000:2000])

print("\n=== KEY PATTERNS ===")
# Look for weight
w = re.search(r'(\d{2,3})\s*(kilograms|kg)', converted, re.IGNORECASE)
print(f"Weight pattern: {w.group() if w else 'NOT FOUND'}")

# Look for BP
bp = re.search(r'(\d{2,3})/(\d{2,3})', converted)
print(f"BP pattern: {bp.group() if bp else 'NOT FOUND'}")

# Look for temp
t = re.search(r'(\d{2})\s*point\s*(\d)', converted, re.IGNORECASE)
print(f"Temp pattern: {t.group() if t else 'NOT FOUND'}")
