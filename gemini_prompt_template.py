"""
Enhanced Gemini extraction prompt template with overflow capture
"""

ENHANCED_PROMPT_TEMPLATE = """You are a medical data extraction AI. Extract all relevant information from this clinical visit transcript into a structured JSON format.

TRANSCRIPT:
{transcript}

Extract the following information in THREE PARTS:

PART 1: PROTOCOL-REQUIRED FIELDS (standard form data)
PART 2: OVERFLOW INFORMATION (medical content not fitting standard fields)
PART 3: VALIDATION METRICS

Return JSON in this exact structure:

{{
  "subject_id": "string - Subject/Patient ID if mentioned",
  "visit_date": "string - Visit date in format 'DD Month YYYY' or 'YYYY-MM-DD'",
  "age": "integer - Patient age in years",
  "hae_type": "string - HAE Type (e.g., 'Type 1', 'Type 2')",
  "medications": ["array of medication names currently taking"],
  "last_dose": {{
    "medication": "string - Name of last medication taken",
    "date": "string - Date of last dose in format 'DD Month YYYY' or 'Month DD, YYYY'"
  }},
  "vitals_pre": {{
    "time_collected": "string - Time in HH:MM format",
    "weight": "string - Weight in kg (number only)",
    "bp": "string - Blood pressure as 'systolic/diastolic'",
    "hr": "string - Heart rate in bpm (number only)",
    "temp": "string - Temperature in Celsius (e.g., '36.8')",
    "rr": "string - Respiratory rate per minute (number only)"
  }},
  "vitals_post": {{
    "weight": "string",
    "bp": "string",
    "hr": "string",
    "temp": "string",
    "rr": "string"
  }},
  "ecg": {{
    "date": "string - Date performed",
    "hr": "string - Heart rate in BPM",
    "pr": "string - PR interval in msec",
    "rr": "string - RR interval in msec",
    "qrs": "string - QRS duration in msec",
    "qt": "string - QT interval in msec",
    "result": "string - Result (e.g., 'Normal', 'Abnormal')"
  }},
  "labs": {{
    "collected": "boolean - Were labs collected?",
    "date": "string - Collection date",
    "time": "string - Collection time in HH:MM format",
    "urine_time": "string - Urine collection time in HH:MM format"
  }},
  "pregnancy": {{
    "potential": "boolean - Is subject of childbearing potential?",
    "date": "string - Collection date",
    "time": "string - Collection time",
    "result": "string - 'Positive' or 'Negative'"
  }},
  "injection": {{
    "dose": "string - Dose administered (e.g., '2 mL')",
    "site": "string - Anatomical location",
    "laterality": "string - Laterality (e.g., 'left lower quadrant', 'right upper quadrant')",
    "start_date": "string - Start date",
    "start_time": "string - Start time in HH:MM format"
  }},
  "injection_2": {{
    "dose": "string",
    "site": "string",
    "laterality": "string",
    "start_date": "string",
    "start_time": "string"
  }},
  "hae_attacks_run_in": "string - Information about HAE attacks during run-in period",
  "continued_eligibility": "string - 'Yes' or 'No'",
  "adverse_events": "string - Description of adverse events or 'None'",
  "notes": "string - Any additional notes from the visit",
  
  "overflow_information": {{
    "patient_concerns": ["array of concerns expressed by patient not captured in standard fields"],
    "medication_questions": ["array of medication-related questions or queries"],
    "unreported_symptoms": ["array of symptoms mentioned but not reported as adverse events"],
    "safety_observations": ["array of safety-relevant observations not fitting other fields"],
    "other_clinical_notes": ["array of other medical information discussed"]
  }},
  
  "validation": {{
    "protocol_compliance": "boolean - Are all required protocol fields present?",
    "completeness_score": "integer 0-100 - Percentage of medical conversation captured in structured fields",
    "overflow_detected": "boolean - Was extra medical information found beyond standard fields?",
    "requires_review": "boolean - Does this transcript need human review?",
    "flags": ["array of any warnings or concerns about the transcript"]
  }}
}}

IMPORTANT INSTRUCTIONS:
1. Extract ALL medical information - nothing should be lost
2. Standard protocol fields go in their designated sections
3. Medical information that doesn't fit standard fields goes in overflow_information
4. Non-medical conversation (greetings, parking, weather) should be excluded
5. Calculate completeness_score: % of medical discussion captured vs total medical content
6. Set requires_review=true if completeness_score < 90 or if safety concerns found
7. If a field is not mentioned, omit it from the JSON

Return ONLY valid JSON. Be precise with numerical values and dates. Use the exact formats specified above.
"""
