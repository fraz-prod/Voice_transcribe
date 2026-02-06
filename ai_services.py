import json
from datetime import datetime

class MockAIService:
    SCENARIOS = {
        "Eligible (Happy Path)": {
            "transcript": """
            Nurse: Hi, can you tell me your age?
            Patient: I'm 34 years old.
            Nurse: And do you know which type of HAE you have?
            Patient: I have Type 1 HAE.
            Nurse: What medications are you currently taking?
            Patient: I take Takhzyro. Last dose was Jan 15th, 2025.
            Nurse: Anything else?
            Patient: No other medications.
            """,
            "data": {
                "visit_date": datetime.today().strftime('%Y-%m-%d'),
                "age": 34,
                "hae_type": "Type 1",
                "medications": ["Takhzyro"],
                "last_dose": {"medication": "Takhzyro", "date": "2025-01-15"},
                "vitals_pre": {"weight": "75", "bp": "120/80", "hr": "72", "temp": "36.6", "rr": "16"},
                "injection": {"dose": "2 mL", "site": "Abdomen"},
                "hae_attacks_run_in": "Yes, 3 attacks",
                "continued_eligibility": "Yes"
            }
        },
        "Complete Happy Path (All Fields)": {
            "transcript": """
            Subject ID: SUBJ-00123
            Visit Date: 2025-02-04
            Patient Age: 34 years old
            HAE Type: Type 1
            HAE Attacks in Run-In: Yes, 3 confirmed attacks.
            Continued Eligibility: Yes.
            Current Medications: Takhzyro
            Last Dose: Takhzyro on 2025-01-15
            No ACE inhibitors.
            Pre-Dose Vitals: Weight 78 kg, BP 120/78, HR 72 bpm, Temp 36.7 C, RR 16 breaths.
            Injection 1: 300 mg in Abdomen Left.
            Injection 2: 300 mg in Abdomen Right.
            Post-Dose Vitals: Weight 78 kg, BP 118/76, HR 70 bpm, Temp 36.6 C, RR 16 breaths.
            ECG: Normal at 70 bpm.
            Labs: Collected at 09:50 AM.
            Adverse Events: None.
            """,
            "data": {
                "subject_id": "SUBJ-00123",
                "visit_date": "2025-02-04",
                "age": 34,
                "hae_type": "Type 1",
                "medications": ["Takhzyro"],
                "last_dose": {"medication": "Takhzyro", "date": "2025-01-15"},
                "vitals_pre": {"weight": "78", "bp": "120/78", "hr": "72", "temp": "36.7", "rr": "16"},
                "vitals_post": {"weight": "78", "bp": "118/76", "hr": "70", "temp": "36.6", "rr": "16"},
                "injection": {"dose": "300 mg (2 mL)", "site": "Abdomen Left Upper Quadrant"},
                "injection_2": {"dose": "300 mg (2 mL)", "site": "Abdomen Right Upper Quadrant"},
                "ecg": {"date": "2025-02-04", "hr": "70", "result": "Normal"},
                "labs": {"collected": True, "date": "2025-02-04", "time": "09:50 AM"},
                "hae_attacks_run_in": "Yes, 3 attacks",
                "continued_eligibility": "Yes",
                "adverse_events": "None"
            }
        },
        "Ineligible (Excluded Meds)": {
            "transcript": """
            Patient: I'm 34, Type 1 HAE.
            Nurse: Meds?
            Patient: Takhzyro and Lisinopril for BP.
            """,
            "data": {
                "visit_date": datetime.today().strftime('%Y-%m-%d'),
                "age": 34,
                "hae_type": "Type 1",
                "medications": ["Takhzyro", "lisinopril"],
                "last_dose": {"medication": "Takhzyro", "date": "2025-01-15"},
                "vitals_pre": {"weight": "78", "bp": "130/85", "hr": "75", "temp": "36.7", "rr": "18"},
                "injection": {"dose": "2 mL", "site": "Abdomen"},
                "hae_attacks_run_in": "Yes, 2 attacks",
                "continued_eligibility": "Yes"
            }
        },
        "Ineligible (Washout Fail)": {
            "transcript": """
            Patient: I took Takhzyro yesterday.
            """,
            "data": {
                "visit_date": datetime.today().strftime('%Y-%m-%d'),
                "age": 34,
                "hae_type": "Type 1",
                "medications": ["Takhzyro"],
                "last_dose": {"medication": "Takhzyro", "date": datetime.today().strftime('%Y-%m-%d')},
                "vitals_pre": {"weight": "75", "bp": "120/80", "hr": "72", "temp": "36.6", "rr": "16"},
                "injection": {"dose": "2 mL", "site": "Abdomen"},
                "hae_attacks_run_in": "Yes",
                "continued_eligibility": "Yes"
            }
        }
    }

    @staticmethod
    def transcribe_audio(audio_file, scenario="Eligible (Happy Path)") -> str:
        return MockAIService.SCENARIOS.get(scenario, MockAIService.SCENARIOS["Eligible (Happy Path)"])["transcript"]

    @staticmethod
    def extract_data(transcript: str, scenario="Eligible (Happy Path)") -> dict:
        # Start with the scenario baseline data
        data = MockAIService.SCENARIOS.get(scenario, MockAIService.SCENARIOS["Eligible (Happy Path)"])["data"].copy()
        
        # If the transcript is different from the scenario transcript (i.e. custom upload), 
        # try to perform basic regex extraction to update values.
        scenario_transcript = MockAIService.SCENARIOS.get(scenario, {}).get("transcript", "").strip()
        
        if transcript.strip() != scenario_transcript:
            import re
            
            # Age: "34 years old" or "Age: 34"
            age_match = re.search(r'(\d{2})\s*(years old|yo)', transcript, re.IGNORECASE)
            if age_match:
                data["age"] = int(age_match.group(1))
            
            # HAE Type: "Type 1" or "Type 2"
            type_match = re.search(r'Type\s*([12])', transcript, re.IGNORECASE)
            if type_match:
                data["hae_type"] = f"Type {type_match.group(1)}"
            
            # Meds: Check for keywords
            meds = []
            if re.search(r'Takhzyro', transcript, re.IGNORECASE):
                meds.append("Takhzyro")
            if re.search(r'Orladeyo', transcript, re.IGNORECASE):
                meds.append("Orladeyo")
            if re.search(r'Lisinopril', transcript, re.IGNORECASE):
                meds.append("lisinopril")

            if meds:
                data["medications"] = meds
            
            # Update last dose med name if changed
            if data.get("last_dose"):
                # Just assume first med is the injectable for this simple mock
                if meds and "Takhzyro" in meds:
                    data["last_dose"]["medication"] = "Takhzyro"

            # Vitals Extraction (Looking for digits)
            # Weight: "78 kg" or "Weight 78"
            w_match = re.search(r'(Weight.*?|)(\d{2,3})(\s*kg|\s*kilograms)', transcript, re.IGNORECASE)
            if w_match:
                data["vitals_pre"]["weight"] = str(w_match.group(2))

            # BP: "120/80" or "120 over 80"
            bp_match = re.search(r'(\d{2,3})\s*(/|over)\s*(\d{2,3})', transcript, re.IGNORECASE)
            if bp_match:
                data["vitals_pre"]["bp"] = f"{bp_match.group(1)}/{bp_match.group(3)}"

            # HR: "72 bpm" or "72 beats"
            hr_match = re.search(r'(\d{2,3})\s*(bpm|beats)', transcript, re.IGNORECASE)
            if hr_match:
                data["vitals_pre"]["hr"] = str(hr_match.group(1))

            # Temp: "36.6"
            t_match = re.search(r'(\d{2}\.?\d?)\s*(degrees|C|Celsius)', transcript, re.IGNORECASE)
            if t_match:
                data["vitals_pre"]["temp"] = str(t_match.group(1))

            # RR: "16 breaths"
            rr_match = re.search(r'(\d{2})\s*(breaths)', transcript, re.IGNORECASE)
            if rr_match:
                data["vitals_pre"]["rr"] = str(rr_match.group(1))
        
        return data

from openai import OpenAI
import os

class RealAIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def transcribe_audio(self, audio_file) -> str:
        # Save buffer to temp file for Whisper (needs path or file-like with name)
        # Streamlit file_uploader returns a BytesIO-like object. 
        # OpenAI client handles it if it has a filename.
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcript.text

    def extract_data(self, transcript: str) -> dict:
        prompt = """
        You are a medical assistant. Extract valid JSON from the transcript.
        JSON Structure:
        {
            "visit_date": "YYYY-MM-DD" (use today if not mentioned),
            "age": int,
            "hae_type": "string" (e.g. "Type 1", "Type 2"),
            "medications": ["string"],
            "last_dose": {"medication": "string", "date": "YYYY-MM-DD"},
            "vitals_pre": {
                "weight": "string",
                "bp": "string",
                "hr": "string",
                "temp": "string",
                "rr": "string"
            },
            "injection": {
                "dose": "string",
                "site": "string"
            },
            "hae_attacks_run_in": "string",
            "continued_eligibility": "string"
        }
        Transcript: 
        """ + transcript
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        return json.loads(content)
