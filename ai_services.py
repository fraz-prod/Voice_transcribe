# Python 3.13 Compatibility Shim for audioop
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        import sys
        sys.modules['audioop'] = audioop
    except ImportError:
        pass


import json
from datetime import datetime
from gemini_prompt_template import ENHANCED_PROMPT_TEMPLATE

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
        # Use GPT-4o Audio for transcription to get better formatting (Speaker labels)
        import base64
        
        # Read file bytes
        # Streamlit uploaded_buffer needs to be read
        if hasattr(audio_file, 'read'):
            audio_file.seek(0)
            file_bytes = audio_file.read()
        else:
            # Assume path
            with open(audio_file, "rb") as f:
                file_bytes = f.read()
                
        b64_audio = base64.b64encode(file_bytes).decode('utf-8')
        
        # Determine format
        fmt = "wav"
        if hasattr(audio_file, 'name') and audio_file.name.lower().endswith(".mp3"):
            fmt = "mp3"
        elif isinstance(audio_file, str) and audio_file.lower().endswith(".mp3"):
            fmt = "mp3"

        response = self.client.chat.completions.create(
            model="gpt-4o-transcribe",
            modalities=["text"],
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert medical transcriptionist. Transcribe the dialogue verbatim. Identify speakers as 'Nurse:' and 'Patient:'. details like ECG parameters, doses, and times must be transcribed accurately. Format clearly."
                },
                {
                    "role": "user",
                    "content": [
                        { 
                            "type": "input_audio", 
                            "input_audio": {
                                "data": b64_audio,
                                "format": fmt 
                            }
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content

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

try:
    import vosk
except ImportError:
    vosk = None
import json
import os
import re
import wave

class LocalAIService:
    @staticmethod
    def transcribe_audio(audio_file) -> str:
        model_path = "model"
        if not os.path.exists(model_path):
             return "Error: Vosk model not found. Please run download_model.py."

        try:
            from pydub import AudioSegment
            from pydub.utils import make_chunks
            import soundfile as sf
            import io
            import tempfile
            
            model = vosk.Model(model_path)
            
            # Read the uploaded audio file
            # First, save to temporary file for pydub processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                audio_file.seek(0)
                tmp_file.write(audio_file.read())
            
            # Load audio with pydub
            audio = AudioSegment.from_file(tmp_path)
            
            # Convert to required format: mono, 16kHz
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            
            # Split into chunks (30 seconds each = 30000 ms)
            chunk_length_ms = 30000  # 30 seconds
            chunks = make_chunks(audio, chunk_length_ms)
            
            print(f"Processing audio in {len(chunks)} chunks...")
            
            all_transcripts = []
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"Processing chunk {i+1}/{len(chunks)}...")
                
                # Export chunk to WAV bytes
                chunk_io = io.BytesIO()
                chunk.export(chunk_io, format="wav")
                chunk_io.seek(0)
                
                # Open with wave for Vosk
                wf = wave.open(chunk_io, "rb")
                
                # Create recognizer for this chunk
                rec = vosk.KaldiRecognizer(model, wf.getframerate())
                rec.SetWords(True)
                
                # Process chunk
                chunk_results = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        part_result = json.loads(rec.Result())
                        chunk_results.append(part_result.get("text", ""))
                
                # Get final result for this chunk
                part_result = json.loads(rec.FinalResult())
                chunk_results.append(part_result.get("text", ""))
                
                # Combine chunk results
                chunk_transcript = " ".join([r for r in chunk_results if r])
                all_transcripts.append(chunk_transcript)
                
                wf.close()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            # Combine all chunk transcripts
            full_transcript = " ".join(all_transcripts)
            print(f"Transcription complete! Total length: {len(full_transcript)} characters")
            
            # Post-process: Add speaker labels and formatting
            formatted_transcript = LocalAIService._format_transcript_with_speakers(full_transcript)
            
            return formatted_transcript
            
        except Exception as e:
            return f"Error transcribing with Vosk: {e}"

    @staticmethod
    def _format_transcript_with_speakers(raw_transcript: str) -> str:
        """
        Format raw continuous transcript into structured dialogue with speaker labels.
        The audio contains spoken words "Nurse" and "Patient" which Vosk transcribes.
        We detect these keywords and use them to split and format the conversation.
        """
        import re
        
        # The transcript contains "nurse" and "patient" as spoken words
        # We'll use these as markers to split the dialogue
        
        # Replace common variations
        text = raw_transcript
        text = re.sub(r'\bnurse\s+', '\nNurse: ', text, flags=re.IGNORECASE)
        text = re.sub(r'\bpatient\s+', '\nPatient: ', text, flags=re.IGNORECASE)
        
        # Split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Clean up lines - capitalize first letter after speaker label
        formatted_lines = []
        for line in lines:
            if line.startswith('Nurse:') or line.startswith('Patient:'):
                # Split on the colon
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0]
                    content = parts[1].strip()
                    # Capitalize first letter
                    if content:
                        content = content[0].upper() + content[1:]
                    formatted_lines.append(f"{speaker}: {content}")
                else:
                    formatted_lines.append(line)
            else:
                # Line doesn't start with speaker, might be continuation
                # or the first line before any speaker was mentioned
                if formatted_lines:
                    # Append to previous line
                    formatted_lines[-1] += ' ' + line
                else:
                    # First line, assume it's Nurse
                    formatted_lines.append(f"Nurse: {line}")
        
        result = '\n'.join(formatted_lines)
        
        # If we didn't find any nurse/patient markers, return original with basic formatting
        if 'Nurse:' not in result and 'Patient:' not in result:
            print("Warning: No 'Nurse' or 'Patient' keywords found in transcription.")
            print("The audio should contain spoken words 'Nurse' and 'Patient' as labels.")
            return raw_transcript
        
        return result

    @staticmethod
    def extract_data(transcript: str, scenario="Eligible (Happy Path)") -> dict:
        # Helper to convert word numbers to digits
        def word_to_num(text):
            result = text
            import re
            
            # Handle ordinals (including multi-word like "twenty sixth") - DO THIS FIRST
            ordinals = {
                'first': '1', 'second': '2', 'third': '3', 'fourth': '4', 'fifth': '5',
                'sixth': '6', 'seventh': '7', 'eighth': '8', 'ninth': '9', 'tenth': '10',
                'eleventh': '11', 'twelfth': '12', 'thirteenth': '13', 'fourteenth': '14',
                'fifteenth': '15', 'sixteenth': '16', 'seventeenth': '17', 'eighteenth': '18',
                'nineteenth': '19', 'twentieth': '20', 'twenty-first': '21', 'twenty-second': '22',
                'twenty-third': '23', 'twenty-fourth': '24', 'twenty-fifth': '25',
                'twenty-sixth': '26', 'twenty-seventh': '27', 'twenty-eighth': '28',
                'twenty-ninth': '29', 'thirtieth': '30', 'thirty-first': '31'
            }
            for word, val in ordinals.items():
                # Allow hyphen or space
                pattern = r'\b' + word.replace('-', r'[-\s]+') + r'\b'
                result = re.sub(pattern, val, result, flags=re.IGNORECASE)

            # Fix common Vosk transcription errors for medical terminology
            result = re.sub(r'\blater\s+reality\b', 'laterality', result, flags=re.IGNORECASE)
            result = re.sub(r'\bmilliliters?\b', 'ml', result, flags=re.IGNORECASE)
            result = re.sub(r'\bmilliliter\b', 'ml', result, flags=re.IGNORECASE)
            result = re.sub(r'\bkilograms?\b', 'kg', result, flags=re.IGNORECASE)
            result = re.sub(r'\bmilliseconds?\b', 'msec', result, flags=re.IGNORECASE)
            result = re.sub(r'\bday\s+performed\b', 'Date performed', result, flags=re.IGNORECASE)
            result = re.sub(r'\bday\s+collected\b', 'Date collected', result, flags=re.IGNORECASE)
            
            # Fix spacing issues (ec g -> ecg, b p m -> bpm, etc.)
            result = re.sub(r'\b ec\s+g\b', 'ecg', result, flags=re.IGNORECASE)
            result = re.sub(r'\bb\s+p\s+m\b', 'bpm', result, flags=re.IGNORECASE)
            result = re.sub(r'\bp\s+r\b', 'pr', result, flags=re.IGNORECASE)
            result = re.sub(r'\bm\s+l\b', 'ml', result, flags=re.IGNORECASE)
            result = re.sub(r'\bq\s+t\b', 'qt', result, flags=re.IGNORECASE)
            result = re.sub(r'\bq\s+r\s+s\b', 'qrs', result, flags=re.IGNORECASE)
            
            # Handle special compound numbers from Vosk
            # "one sixty" -> "160", "one eighty" -> "180"
            result = re.sub(r'\bone\s+sixty\b', '160', result, flags=re.IGNORECASE)
            result = re.sub(r'\bone\s+seventy\b', '170', result, flags=re.IGNORECASE)
            result = re.sub(r'\bone\s+eighty\b', '180', result, flags=re.IGNORECASE)
            result = re.sub(r'\bone\s+ninety\b', '190', result, flags=re.IGNORECASE)
            
            # "eight thirty three" -> "833", "three eighty" -> "380"
            result = re.sub(r'\beight\s+thirty\s+three\b', '833', result, flags=re.IGNORECASE)
            result = re.sub(r'\beight\s+thirty\b', '830', result, flags=re.IGNORECASE)
            result = re.sub(r'\bthree\s+eighty\b', '380', result, flags=re.IGNORECASE)
            result = re.sub(r'\bthree\s+hundred\b', '300', result, flags=re.IGNORECASE)
            
            # Handle special patterns like "one eighteen" -> "118", "one twenty" -> "120"
            result = re.sub(r'\bone\s+eighteen\b', '118', result, flags=re.IGNORECASE)
            result = re.sub(r'\bone\s+twenty\b', '120', result, flags=re.IGNORECASE)
            result = re.sub(r'\bone\s+hundred\b', '100', result, flags=re.IGNORECASE)
            result = re.sub(r'\btwo\s+hundred\b', '200', result, flags=re.IGNORECASE)
            
            # Handle "thirty six point eight" -> "36 point 8" -> "36.8"
            # First handle tens + unit for the integer part
            for tens_word, tens_val in [('twenty', '2'), ('thirty', '3'), ('forty', '4'), 
                                          ('fifty', '5'), ('sixty', '6'), ('seventy', '7'),
                                          ('eighty', '8'), ('ninety', '9')]:
                for unit_word, unit_val in [('one', '1'), ('two', '2'), ('three', '3'), 
                                              ('four', '4'), ('five', '5'), ('six', '6'),
                                              ('seven', '7'), ('eight', '8'), ('nine', '9')]:
                    pattern = tens_word + r'\s+' + unit_word
                    replacement = tens_val + unit_val
                    result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
            # Handle standalone number words
            word_nums = {
                'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
                'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
                'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
                'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
                'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
                'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
                'eighty': '80', 'ninety': '90',
            }
            for word, val in word_nums.items():
                result = re.sub(r'\b' + word + r'\b', val, result, flags=re.IGNORECASE)
            
            # Handle "X over Y" for BP
            result = re.sub(r'(\d+)\s+over\s+(\d+)', r'\1/\2', result)
            
            # Handle "X point Y" for decimals
            result = re.sub(r'(\d+)\s+point\s+(\d+)', r'\1.\2', result)
            
            # Handle years: "twenty twenty six" -> "2026", "20 26" -> "2026"
            result = re.sub(r'\b(19|20)\s+(\d{2})\b', r'\1\2', result)
            
            return result

        # Normalize transcript
        transcript_clean = transcript.replace("subject to", "subject id").replace("slash", "/")
        transcript_clean = word_to_num(transcript_clean)
        
        # Helper to extract time
        def extract_time(pattern, text):
            # Flexible time pattern: "9:25" or "9 25" or "10 o 5"
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                h = match.group(1)
                m = match.group(2)
                if len(h) == 1: h = "0" + h
                if len(m) == 1: m = "0" + m
                return f"{h}:{m}"
            return None

        data = MockAIService.SCENARIOS["Eligible (Happy Path)"]["data"].copy()
        
        # Reset specific fields
        data["medications"] = []
        data["vitals_pre"] = {}
        data["injection"] = {}
        data["last_dose"] = {}
        
        # === Extraction Logic ===
        
        # === Extraction Logic ===
        
        # Visit Date: Supports "26 January 2026" or "January 26, 2026"
        date_match = re.search(r'(Date|today\'s date)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4}|[A-Za-z]+\s+\d{1,2},?\s*\d{4})', transcript_clean, re.IGNORECASE)
        if date_match:
             data["visit_date"] = date_match.group(2)

        # Subject ID: "Subject ID 0215 dash 301" or "0215-301"
        sid_match = re.search(r'Subject ID\s*([\w\d\-\s]+?)(,|\.|Date)', transcript_clean, re.IGNORECASE)
        if sid_match:
            sid = sid_match.group(1).replace("dash", "-").replace(" ", "")
            data["subject_id"] = sid

        # Initials: "Initials A.K." or "initials JK"
        init_match = re.search(r'Initials\s*([A-Za-z\.]+)', transcript_clean, re.IGNORECASE)
        if init_match:
             pass

        # Age
        age_match = re.search(r'(\d{2})\s*(years old|yo)', transcript_clean, re.IGNORECASE)
        if age_match:
            data["age"] = int(age_match.group(1))

        # HAE Type
        type_match = re.search(r'Type\s*([12])', transcript_clean, re.IGNORECASE)
        if type_match:
            data["hae_type"] = f"Type {type_match.group(1)}"
        
        # Meds
        meds = []
        if re.search(r'Takhzyro', transcript_clean, re.IGNORECASE):
            meds.append("Takhzyro")
        if re.search(r'Orladeyo', transcript_clean, re.IGNORECASE):
            meds.append("Orladeyo")
        if re.search(r'Lisinopril', transcript_clean, re.IGNORECASE):
            meds.append("lisinopril")
        if meds:
            data["medications"] = meds
            
        if "Takhzyro" in meds:
             data["last_dose"]["medication"] = "Takhzyro"
        elif "Orladeyo" in meds:
             data["last_dose"]["medication"] = "Orladeyo"
             
        # Extract last dose date in various formats
        if data["last_dose"].get("medication"):
            date_patterns = [
                r'last dose\s+(?:was\s+)?([A-Za-z]+\s+\d{1,2},?\s*\d{4})',  # "last dose January 15, 2025"
                r'last dose\s+(?:was\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "last dose 15 January 2025"
                r'last dose\s+(?:was\s+)?(\d{4}-\d{2}-\d{2})',  # "last dose 2025-01-15"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})',  # "took Takhzyro on January 15th, 2025"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "took Takhzyro on 15 January 2025"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})',  # "took Takhzyro on 2025-01-15"
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, transcript_clean, re.IGNORECASE)
                if date_match:
                    # Clean up the date string (remove ordinals like 'st', 'nd', 'rd', 'th')
                    date_str = date_match.group(1).strip()
                    date_str = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_str)
                    data["last_dose"]["date"] = date_str
                    break
        elif "Orladeyo" in meds:
             data["last_dose"]["medication"] = "Orladeyo"
             
        # Extract last dose date in various formats
        if data["last_dose"].get("medication"):
            date_patterns = [
                r'last dose\s+(?:was\s+)?([A-Za-z]+\s+\d{1,2},?\s*\d{4})',  # "last dose January 15, 2025"
                r'last dose\s+(?:was\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "last dose 15 January 2025"
                r'last dose\s+(?:was\s+)?(\d{4}-\d{2}-\d{2})',  # "last dose 2025-01-15"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})',  # "took Takhzyro on January 15th, 2025"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # "took Takhzyro on 15 January 2025"
                r'(?:took|received|given)\s+(?:Takhzyro|Orladeyo|medication)\s+(?:on\s+)?(\d{4}-\d{2}-\d{2})',  # "took Takhzyro on 2025-01-15"
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, transcript_clean, re.IGNORECASE)
                if date_match:
                    # Clean up the date string (remove ordinals like 'st', 'nd', 'rd', 'th')
                    date_str = date_match.group(1).strip()
                    date_str = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_str)
                    data["last_dose"]["date"] = date_str
                    break

        # Vitals Extraction (Looking for digits)
        
        # Time Collected (Pre-dose)
        time_pre = extract_time(r'(?:Physical examination pre dose|Visual).*?Time collected\s*(\d{1,2})[\s:o\.]+(\d{1,2})', transcript_clean)
        if time_pre:
            data["vitals_pre"]["time_collected"] = time_pre
        
        # Weight
        w_match = re.search(r'(weight|weigh)\s*(\d{2,3})\s*(kg|kilo|kilogram)?', transcript_clean, re.IGNORECASE)
        if w_match:
            data["vitals_pre"]["weight"] = str(w_match.group(2))

        # BP
        bp_match = re.search(r'(blood pressure|pressure|push)\s*(\d{2,3})[/\.](\d{2,3})', transcript_clean, re.IGNORECASE)
        if bp_match:
            data["vitals_pre"]["bp"] = f"{bp_match.group(2)}/{bp_match.group(3)}"
        
        # HR
        hr_match = re.search(r'(heart rate|rate)\s*(\d{2,3})\s*(bpm|bpl|be p m)?', transcript_clean, re.IGNORECASE)
        if not hr_match:
            hr_match = re.search(r'(\d{2,3})\s*(bpm|bpl|be p m)', transcript_clean, re.IGNORECASE)
            if hr_match:
                data["vitals_pre"]["hr"] = str(hr_match.group(1))
        else:
            data["vitals_pre"]["hr"] = str(hr_match.group(2))

        # Temp
        t_match = re.search(r'(temperature|temp)\s*(\d{2})[.\s]*(\d{1,2})?', transcript_clean, re.IGNORECASE)
        if t_match:
            temp_val = t_match.group(2)
            if t_match.group(3):
                temp_val += "." + t_match.group(3)
            data["vitals_pre"]["temp"] = temp_val

        # RR
        rr_match = re.search(r'(respiratory rate|respiratory|breaths)\s*(\d{2})', transcript_clean, re.IGNORECASE)
        if not rr_match:
            rr_match = re.search(r'(\d{2})\s*breaths', transcript_clean, re.IGNORECASE)
            if rr_match:
                data["vitals_pre"]["rr"] = str(rr_match.group(1))
        else:
            data["vitals_pre"]["rr"] = str(rr_match.group(2))
        
        # === Post-Dose Vitals ===
        post_section = re.search(r'(post.?dose|1 hour post)(.*?)($|Notes:|Participant)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if post_section:
            post_text = post_section.group(2)
            data["vitals_post"] = {}
            
            w_post = re.search(r'Weight\s*(\d{2,3})', post_text, re.IGNORECASE)
            if w_post:
                data["vitals_post"]["weight"] = str(w_post.group(1))
            
            bp_post = re.search(r'Blood pressure\s*(\d{2,3})[\./](\d{2,3})', post_text, re.IGNORECASE)
            if bp_post:
                data["vitals_post"]["bp"] = f"{bp_post.group(1)}/{bp_post.group(2)}"
            
            hr_post = re.search(r'Heart rate\s*(\d{2,3})', post_text, re.IGNORECASE)
            if hr_post:
                data["vitals_post"]["hr"] = str(hr_post.group(1))
            
            t_post = re.search(r'Temperature\s*(\d{2}[\.,]\d{1,2})', post_text, re.IGNORECASE)
            if t_post:
                data["vitals_post"]["temp"] = str(t_post.group(1)).replace(",", ".")
            
            rr_post = re.search(r'Respiratory rate\s*(\d{2})', post_text, re.IGNORECASE)
            if rr_post:
                data["vitals_post"]["rr"] = str(rr_post.group(1))

        # === ECG Extraction ===
        data["ecg"] = {}
        # Relaxed regex to handle "PR1" or extra spaces
        # Look for ECG section first
        ecg_section_match = re.search(r'ECG.*?(?:PI slash sub-I|Laboratory)', transcript_clean, re.IGNORECASE | re.DOTALL)
        ecg_text = ecg_section_match.group(0) if ecg_section_match else transcript_clean

        ecg_hr = re.search(r'Heart rate\s*(\d{2,3})', ecg_text, re.IGNORECASE)
        if ecg_hr: data["ecg"]["hr"] = ecg_hr.group(1)

        ecg_pr = re.search(r'PR\w*\s*(\d{2,3})\s*msec', ecg_text, re.IGNORECASE)
        if ecg_pr: data["ecg"]["pr"] = ecg_pr.group(1)

        ecg_rr = re.search(r'RR\s*(\d{2,4})\s*msec', ecg_text, re.IGNORECASE)
        if ecg_rr: data["ecg"]["rr"] = ecg_rr.group(1)
        
        ecg_qrs = re.search(r'QRS\s*(\d{2,3})\s*msec', ecg_text, re.IGNORECASE)
        if ecg_qrs: data["ecg"]["qrs"] = ecg_qrs.group(1)

        ecg_qt = re.search(r'QT\s*(\d{2,3})\s*msec', ecg_text, re.IGNORECASE)
        if ecg_qt: data["ecg"]["qt"] = ecg_qt.group(1)
        
        # ECG Result
        if re.search(r'Result\s*Normal', ecg_text, re.IGNORECASE):
            data["ecg"]["result"] = "Normal"
        
        # ECG Date
        ecg_date = re.search(r'(?:Date|Day) performed\s*([A-Za-z0-9,\s]+?)(?:\.|\s+Time)', ecg_text, re.IGNORECASE | re.DOTALL)
        if ecg_date:
            data["ecg"]["date"] = ecg_date.group(1).strip()

        # === Labs Extraction ===
        data["labs"] = {"collected": True}
        labs_date = re.search(r'Lab.*?(Date|Day) collected\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4}|[A-Za-z]+\s+\d{1,2},?\s*\d{4})', transcript_clean, re.IGNORECASE | re.DOTALL)
        if labs_date:
            data["labs"]["date"] = labs_date.group(2)
        
        labs_time = extract_time(r'Lab.*?Time collected\s*(\d{1,2})[\s:o\.]+(\d{1,2})', transcript_clean)
        if labs_time:
            data["labs"]["time"] = labs_time
        
        urine_time = extract_time(r'Urine collection time\s*(\d{1,2})[\s:o\.]+(\d{1,2})', transcript_clean)
        if urine_time:
            data["labs"]["urine_time"] = urine_time

        # === Notes Extraction ===
        notes_match = re.search(r'Notes[:\s]+(.*?)(Nurse|$)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if notes_match:
            data["notes"] = notes_match.group(1).strip()

        # === Pregnancy Test Extraction ===
        data["pregnancy"] = {}
        preg_potential = re.search(r'childbearing potential\?.*?(Yes|No)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if preg_potential:
            data["pregnancy"]["potential"] = preg_potential.group(1).capitalize() == "Yes"
        
        preg_result = re.search(r'Pregnancy.*?Result\s*(Positive|Negative)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if preg_result:
            data["pregnancy"]["result"] = preg_result.group(1).capitalize()
        
        preg_date = re.search(r'Collection date\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4}|[A-Za-z]+\s+\d{1,2},?\s*\d{4})', transcript_clean, re.IGNORECASE)
        if preg_date:
            data["pregnancy"]["date"] = preg_date.group(1)
        
        preg_time = extract_time(r'Collection time\s*(\d{1,2})[\s:o\.]+(\d{1,2})', transcript_clean)
        if preg_time:
            data["pregnancy"]["time"] = preg_time

        # === Injection 1 Extraction ===
        # Split text into Injection sections
        inj1_text = ""
        inj2_text = ""
        
        parts = re.split(r'Injection\s*\d', transcript_clean, flags=re.IGNORECASE)
        # parts[0] is pre-injection, parts[1] is Inj 1, parts[2] is Inj 2 (if exists)
        if len(parts) > 1:
            inj1_text = parts[1]
        
        if len(parts) > 2:
            inj2_text = parts[2]
            
        # Helper for injection fields
        def extract_injection(text):
            inj_data = {}
            dose_m = re.search(r'Dose administered\s*(\d+[\.]?\d*)\s*mL', text, re.IGNORECASE)
            if dose_m: inj_data["dose"] = dose_m.group(1) + " mL"
            
            site_m = re.search(r'location\s+([A-Za-z]+)', text, re.IGNORECASE)
            if site_m: inj_data["site"] = site_m.group(1)
            
            lat_m = re.search(r'Laterality\s+([A-Za-z\s]+?)(?:\.|Route|Start)', text, re.IGNORECASE)
            if lat_m: inj_data["laterality"] = lat_m.group(1).strip()
            
            date_m = re.search(r'Start date\s*([A-Za-z0-9,\s]+)', text, re.IGNORECASE)
            if date_m: inj_data["start_date"] = date_m.group(1).strip()
            
            time_m = extract_time(r'Start time\s*(\d{1,2})[\s:o\.]+(\d{1,2})', text)
            if time_m: inj_data["start_time"] = time_m
            
            return inj_data

        if inj1_text:
            data["injection"] = extract_injection(inj1_text)

        # === Injection 2 Extraction ===
        if inj2_text:
            data["injection_2"] = extract_injection(inj2_text)
            
        return data

class LocalWhisperService:
    @staticmethod
    def transcribe_audio(audio_file, model=None, streaming_callback=None) -> str:
        try:
            from faster_whisper import WhisperModel
            import tempfile
            import os
            
            # Configuration
            model_size = "medium" # or "large-v3"
            # Check for CUDA
            import logging
            from tqdm import tqdm
            import time

            # Configure Logging
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            logger = logging.getLogger(__name__)

            if model is None:
                # Configuration
                model_size = "medium" # or "large-v3"
                # Check for CUDA
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                
                logger.info(f"Loading local Faster-Whisper model ({model_size}) on {device} with {compute_type}...")
                model = WhisperModel(model_size, device=device, compute_type=compute_type)
            else:
                logger.info("Using cached Faster-Whisper model.")

            # Helper to save uploaded file to temp path
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                if hasattr(audio_file, 'seek'):
                     audio_file.seek(0)
                     file_bytes = audio_file.read()
                     tmp_file.write(file_bytes)
                elif isinstance(audio_file, str):
                    # If it's a path string
                    with open(audio_file, 'rb') as f:
                        tmp_file.write(f.read())
            
            logger.info(f"Transcribing {tmp_path} with Faster-Whisper...")
            
            # Using beam_size 5 as requested implicitly by earlier context or default
            segments, info = model.transcribe(tmp_path, beam_size=5)
            
            logger.info(f"Detected language '{info.language}' with probability {info.language_probability:.2f}")
            logger.info(f"Audio duration: {info.duration}s")

            # Collect segments with progress bar and streaming
            transcript_parts = []
            
            # We can use the duration to estimate progress if we wanted, but simple count is safer
            total_duration = int(info.duration) if info.duration else None
            with tqdm(total=total_duration, unit="sec", desc="Transcription Progress") as pbar:
                last_pos = 0
                for segment in segments:
                    transcript_parts.append(segment.text)
                    
                    # Call streaming callback with accumulated transcript
                    if streaming_callback:
                        accumulated_text = "".join(transcript_parts).strip()
                        try:
                            streaming_callback(accumulated_text)
                        except Exception as e:
                            logger.warning(f"Streaming callback error: {e}")
                    
                    # Update progress bar based on segment end time
                    current_pos = segment.end
                    pbar.update(int(current_pos - last_pos))
                    last_pos = current_pos
                
                # Ensure progress bar reaches 100% even if last segment ends early
                if total_duration and last_pos < total_duration:
                    pbar.update(total_duration - int(last_pos))
                    
            full_transcript = "".join(transcript_parts).strip()
            logger.info(f"Transcription complete. Length: {len(full_transcript)} chars.")
            
            # Cleanup
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            # Format transcript with speakers (reuse LocalAIService helper)
            formatted = LocalAIService._format_transcript_with_speakers(full_transcript)
            
            # Final callback with formatted transcript
            if streaming_callback:
                try:
                    streaming_callback(formatted)
                except Exception as e:
                    logger.warning(f"Final streaming callback error: {e}")
            
            return formatted
            
        except ImportError:
            return "Error: faster-whisper not installed. Please run: pip install faster-whisper"
        except Exception as e:
            return f"Error running local Faster-Whisper: {e}"

    @staticmethod
    def extract_data(transcript: str) -> dict:
        # Reuse the Regex/rule-based extraction from LocalAIService
        # This ensures we don't need an LLM for this step.
        return LocalAIService.extract_data(transcript)

class GeminiAIService:
    """Service for using Google Gemini 2.0 Flash for accurate, non-deterministic form extraction"""
    
    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Use gemini-2.0-flash - confirmed available via list_models
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    
    @staticmethod
    def parse_protocol_pdf(pdf_file) -> str:
        """Extract text from an uploaded protocol PDF using pypdf."""
        from pypdf import PdfReader
        import io as _io
        pdf_file.seek(0)
        reader = PdfReader(_io.BytesIO(pdf_file.read()))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()

    @staticmethod
    def parse_protocol_md(md_file) -> str:
        """
        Extract clinically relevant sections from an OCR-generated protocol Markdown file.

        Instead of sending the full document (which can be 200KB+), this function
        uses regex-based section detection to extract only the parts Gemini needs:
          - Inclusion / Exclusion criteria
          - Washout periods
          - Prohibited medications
          - Schedule of Assessments (visit-specific requirements)
          - Synopsis (for visit type context)

        No LLM is used — this is pure text processing. The result is a focused
        ~30-60K char excerpt that fits comfortably in the context window.
        """
        import re

        md_file.seek(0)
        full_text = md_file.read().decode("utf-8", errors="replace")

        # Section headings to look for (case-insensitive, partial match)
        RELEVANT_SECTIONS = [
            r"synopsis",
            r"inclusion.{0,20}criteria",
            r"exclusion.{0,20}criteria",
            r"washout",
            r"prohibited.{0,20}med",
            r"schedule.{0,20}assessment",
            r"visit.{0,20}procedure",
            r"eligibility",
            r"contraception",
            r"run.?in.{0,20}period",
        ]

        # Split the document into sections by markdown headings (# ## ###)
        # Pattern: a line starting with one or more # characters
        heading_pattern = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)
        matches = list(heading_pattern.finditer(full_text))

        extracted_sections = []

        for i, match in enumerate(matches):
            heading_text = match.group(2).strip()
            # Check if this heading is relevant
            is_relevant = any(
                re.search(pattern, heading_text, re.IGNORECASE)
                for pattern in RELEVANT_SECTIONS
            )
            if is_relevant:
                # Extract from this heading to the next same-or-higher-level heading
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                section_text = full_text[start:end].strip()
                # Cap each section at 15,000 chars to prevent any single section dominating
                extracted_sections.append(section_text[:15000])

        if extracted_sections:
            combined = "\n\n---\n\n".join(extracted_sections)
        else:
            # Fallback: if no headings matched, take the first 60K chars
            combined = full_text[:60000]

        # Final cap: 80,000 chars (much higher than PDF cap since MD is already clean text)
        MAX_MD_CHARS = 80000
        if len(combined) > MAX_MD_CHARS:
            combined = combined[:MAX_MD_CHARS] + "\n\n[Protocol text truncated at 80,000 characters]"

        return combined
    
    def extract_data(self, transcript: str, protocol_text: str = "") -> dict:
        """Extract structured data from transcript using Gemini Flash with overflow capture.
        
        Args:
            transcript: The clinical visit transcript text.
            protocol_text: Optional protocol document text for cross-referencing.
        """
        import re

        # Cap protocol text to avoid consuming the entire context window
        MAX_PROTOCOL_CHARS = 30000
        if protocol_text and len(protocol_text) > MAX_PROTOCOL_CHARS:
            protocol_text = protocol_text[:MAX_PROTOCOL_CHARS] + "\n\n[... protocol truncated for context limit ...]"

        def _build_prompt(proto_text: str) -> str:
            return ENHANCED_PROMPT_TEMPLATE.format(
                transcript=transcript,
                protocol_context=proto_text if proto_text else "No protocol document provided."
            )

        def _call_gemini(prompt_text: str, temperature=0.7):
            return self.model.generate_content(
                prompt_text,
                generation_config={
                    'temperature': temperature,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 16384,
                    'response_mime_type': 'application/json',
                }
            )

        def _extract_json(raw: str) -> str:
            """Pull JSON out of any markdown-wrapped response."""
            raw = raw.strip()
            if not raw:
                return ""
            fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if fence_match:
                return fence_match.group(1).strip()
            if raw.startswith('```'):
                lines = raw.split('\n')
                inner = '\n'.join(lines[1:])
                last_fence = inner.rfind('```')
                if last_fence != -1:
                    inner = inner[:last_fence]
                return inner.strip()
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1 and end > start:
                return raw[start:end+1].strip()
            return raw

        def _repair_json(text: str) -> str:
            """Attempt to repair common Gemini JSON issues."""
            # Remove trailing commas before } or ]
            text = re.sub(r',\s*([\]}])', r'\1', text)
            
            # Count open/close braces and brackets
            open_braces = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')
            
            # If truncated mid-string, close the string
            # Find if we have an unclosed quote
            in_string = False
            escape_next = False
            for ch in text:
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
            
            if in_string:
                text = text.rstrip()
                text += '"'
            
            # Close any unclosed brackets/braces
            text = text.rstrip().rstrip(',')
            for _ in range(open_brackets):
                text += ']'
            for _ in range(open_braces):
                text += '}'
            
            return text

        def _try_parse(raw_text: str) -> dict:
            """Try to parse JSON from raw response, with repair fallback."""
            response_text = _extract_json(raw_text)
            if not response_text:
                raise ValueError(f"No JSON found in response.\nRaw: {raw_text[:500]}")

            # First try: direct parse
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                pass

            # Second try: repair and parse
            repaired = _repair_json(response_text)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"JSON parse failed even after repair: {e}\n\n"
                    f"Response snippet: {response_text[:500]}"
                ) from e

        # === Main extraction flow ===
        prompt = _build_prompt(protocol_text)

        try:
            response = _call_gemini(prompt, temperature=0.7)
            raw_text = response.text if response.text else ""

            if not raw_text.strip():
                print("Warning: empty response. Retrying with temperature=0.3...")
                response = _call_gemini(prompt, temperature=0.3)
                raw_text = response.text if response.text else ""

            if not raw_text.strip():
                raise ValueError("Gemini returned an empty response after retry.")

            # Try to parse
            try:
                return _try_parse(raw_text)
            except ValueError:
                # If protocol was included, retry WITHOUT it (protocol may be too large)
                if protocol_text:
                    print("Warning: JSON parse failed with protocol. Retrying without protocol text...")
                    fallback_prompt = _build_prompt("")
                    response = _call_gemini(fallback_prompt, temperature=0.3)
                    raw_text = response.text if response.text else ""
                    if raw_text.strip():
                        return _try_parse(raw_text)
                raise

        except Exception as e:
            print(f"Error in Gemini extraction: {e}")
            raise


class Chirp3GeminiService:
    """
    Service using Google Cloud Speech-to-Text V2 (Chirp 3) for STT
    and Gemini 2.5 Flash for data extraction with overflow capture.

    Requirements:
        pip install google-cloud-speech google-generativeai

    Authentication (one of):
        - Set GOOGLE_APPLICATION_CREDENTIALS env var to path of service account JSON
        - Pass credentials_json (path or dict) to __init__
        - Use Application Default Credentials (gcloud auth application-default login)
    """

    SUPPORTED_REGIONS = ["us", "eu", "asia-northeast1", "asia-southeast1",
                         "asia-south1", "europe-west2", "europe-west3",
                         "northamerica-northeast1"]

    def __init__(self, gemini_api_key: str, project_id: str,
                 region: str = "us", credentials_path: str = None):
        """
        Args:
            gemini_api_key: Gemini API key for extraction
            project_id: Google Cloud project ID
            region: GCP region for Speech-to-Text (default: "us")
            credentials_path: Optional path to service account JSON file
        """
        self.project_id = project_id
        self.region = region

        # --- Set up Google Cloud credentials ---
        if credentials_path:
            import os
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # --- Set up Speech client ---
        try:
            from google.cloud.speech_v2 import SpeechClient
            from google.api_core.client_options import ClientOptions
            self.speech_client = SpeechClient(
                client_options=ClientOptions(
                    api_endpoint=f"{region}-speech.googleapis.com"
                )
            )
        except ImportError:
            raise ImportError(
                "google-cloud-speech not installed. Run: pip install google-cloud-speech"
            )

        # --- Set up Gemini 2.5 Flash ---
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. Run: pip install google-generativeai"
            )

    def transcribe_audio(self, audio_file, progress_callback=None) -> str:
        """
        Transcribe audio using Chirp 3 via Google Cloud Speech-to-Text V2.

        Args:
            audio_file: File-like object or path string to audio file
            progress_callback: Optional callable(status_str) for UI updates

        Returns:
            Full transcript as a string (with speaker labels if diarization enabled)
        """
        from google.cloud.speech_v2.types import cloud_speech

        if progress_callback:
            progress_callback("Reading audio file...")

        # Read audio bytes
        if hasattr(audio_file, 'read'):
            audio_bytes = audio_file.read()
            # Reset if possible
            if hasattr(audio_file, 'seek'):
                audio_file.seek(0)
        else:
            with open(audio_file, 'rb') as f:
                audio_bytes = f.read()

        file_size_mb = len(audio_bytes) / (1024 * 1024)
        print(f"[Chirp3] Audio size: {file_size_mb:.2f} MB")

        if progress_callback:
            progress_callback(f"Sending to Chirp 3 ({file_size_mb:.1f} MB)...")

        # Build recognition config with diarization
        recognition_config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="chirp_3",
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=True,
                diarization_config=cloud_speech.SpeakerDiarizationConfig(
                    enable_speaker_diarization=True,
                    min_speaker_count=2,
                    max_speaker_count=5,
                ),
            ),
        )

        recognizer_path = (
            f"projects/{self.project_id}/locations/{self.region}/recognizers/_"
        )

        # Use synchronous Recognize for files up to ~60s,
        # streaming chunked approach for longer audio
        if len(audio_bytes) <= 10 * 1024 * 1024:  # <= 10 MB → sync
            if progress_callback:
                progress_callback("Transcribing with Chirp 3 (sync)...")

            request = cloud_speech.RecognizeRequest(
                recognizer=recognizer_path,
                config=recognition_config,
                content=audio_bytes,
            )
            response = self.speech_client.recognize(request=request)
            transcript = self._build_transcript_from_recognize(response)

        else:
            # Streaming for larger files
            if progress_callback:
                progress_callback("Transcribing with Chirp 3 (streaming)...")
            transcript = self._transcribe_streaming(
                audio_bytes, recognition_config, recognizer_path, progress_callback
            )

        if progress_callback:
            progress_callback("Transcription complete!")

        print(f"[Chirp3] Transcript length: {len(transcript)} chars")
        return transcript

    def _build_transcript_from_recognize(self, response) -> str:
        """Build a readable transcript from sync Recognize response with speaker labels."""
        lines = []
        for result in response.results:
            alt = result.alternatives[0]
            # Try to get speaker tag from words
            if alt.words:
                current_speaker = None
                current_text = []
                for word in alt.words:
                    speaker = getattr(word, 'speaker_label', None) or \
                              getattr(word, 'speaker_tag', None)
                    if speaker != current_speaker:
                        if current_text:
                            label = f"Speaker {current_speaker}" if current_speaker else "Speaker"
                            lines.append(f"{label}: {' '.join(current_text)}")
                        current_speaker = speaker
                        current_text = [word.word]
                    else:
                        current_text.append(word.word)
                if current_text:
                    label = f"Speaker {current_speaker}" if current_speaker else "Speaker"
                    lines.append(f"{label}: {' '.join(current_text)}")
            else:
                lines.append(alt.transcript)
        return "\n".join(lines)

    def _transcribe_streaming(self, audio_bytes: bytes, recognition_config,
                               recognizer_path: str, progress_callback=None) -> str:
        """Stream large audio in chunks to Chirp 3."""
        from google.cloud.speech_v2.types import cloud_speech

        CHUNK_SIZE = 32768  # 32 KB chunks

        streaming_config = cloud_speech.StreamingRecognitionConfig(
            config=recognition_config,
        )

        config_request = cloud_speech.StreamingRecognizeRequest(
            recognizer=recognizer_path,
            streaming_config=streaming_config,
        )

        def audio_generator():
            yield config_request
            total = len(audio_bytes)
            for i in range(0, total, CHUNK_SIZE):
                chunk = audio_bytes[i:i + CHUNK_SIZE]
                yield cloud_speech.StreamingRecognizeRequest(audio=chunk)
                if progress_callback:
                    pct = min(100, int((i / total) * 100))
                    progress_callback(f"Transcribing... {pct}%")

        responses = self.speech_client.streaming_recognize(requests=audio_generator())

        lines = []
        for response in responses:
            for result in response.results:
                if result.is_final:
                    alt = result.alternatives[0]
                    lines.append(alt.transcript)

        return "\n".join(lines)

    def extract_data(self, transcript: str) -> dict:
        """
        Extract structured data from transcript using Gemini 2.5 Flash
        with overflow capture and validation metrics.
        """
        prompt = ENHANCED_PROMPT_TEMPLATE.format(transcript=transcript)

        try:
            response = self.gemini_model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,   # Lower temp for more consistent extraction
                    'top_p': 0.95,
                    'max_output_tokens': 4096,
                }
            )

            response_text = response.text.strip()

            # Strip markdown code fences if present
            if response_text.startswith('```'):
                start = response_text.find('\n')
                end = response_text.rfind('```')
                if start != -1 and end != -1:
                    response_text = response_text[start + 1:end].strip()

            data = json.loads(response_text)
            return data

        except json.JSONDecodeError as e:
            print(f"[Chirp3Gemini] JSON parse error: {e}")
            print(f"Response: {response_text[:500]}")
            raise
        except Exception as e:
            print(f"[Chirp3Gemini] Gemini API error: {e}")
            raise


class LiveSessionService:
    """
    Service for real-time I/E categorization during a live pre-screen phone call.

    Workflow:
      1. Ninna records a ~15-30s audio chunk via st.audio_input()
      2. Call transcribe_chunk() -> Whisper transcribes it locally
      3. Accumulate the returned text into session state
      4. Every 3 chunks, call run_ie_check() -> Gemini updates the I/E panel

    Gemini is only called every ~90 seconds, keeping cost very low.
    """

    IE_CHECK_EVERY_N_CHUNKS = 3  # Run Gemini I/E check every N recorded chunks

    def __init__(self, api_key: str):
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

    # -- Script Generator (structured JSON) ----------------------------------

    def generate_script_structured(self, protocol_text: str) -> list:
        """
        Generate the pre-screening call script as STRUCTURED JSON — a list of
        question cards Ninna reads during the call.

        Each card contains:
          id, section, criterion, ninna_says, pass_condition, fail_condition,
          answer (null initially), status (open), source (auto/manual/none)

        Returns a list of card dicts, or [] on error.
        """
        MAX_PROTO = 25000
        if len(protocol_text) > MAX_PROTO:
            protocol_text = protocol_text[:MAX_PROTO] + "\n\n[Protocol truncated]"

        prompt = f"""You are a clinical research coordinator.

Based on the following study protocol, generate a PRE-SCREENING PHONE CALL SCRIPT as structured JSON.

PROTOCOL:
{protocol_text}

Return a JSON object with this exact structure:

{{
  "opening": "Exact words Ninna says to open the call",
  "closing_eligible": "Exact words Ninna says if patient IS eligible",
  "closing_ineligible": "Exact words Ninna says if patient is NOT eligible",
  "questions": [
    {{
      "id": "inc_1",
      "section": "inclusion",
      "criterion": "Short name of the criterion",
      "ninna_says": "Exact conversational question Ninna reads aloud to the patient",
      "pass_condition": "What answer qualifies the patient (e.g. YES, Age >= 18)",
      "fail_condition": "What answer disqualifies the patient",
      "washout_days": null,
      "answer": null,
      "status": "open",
      "source": "none"
    }}
  ]
}}

Rules:
- section must be one of: "inclusion", "exclusion", "washout", "general"
- For exclusion: pass_condition = "NO / Not present", fail_condition = "YES / Present"
- For washout questions: set washout_days to the integer number of days from protocol
- ninna_says must be plain English — NO medical jargon — a patient must understand it
- id format: inc_1, inc_2 for inclusion; exc_1, exc_2 for exclusion; wash_1 for washout
- Cover EVERY inclusion criterion, EVERY exclusion criterion, and ALL prohibited medications with washout periods
- answer, status, source start as: null, "open", "none"
- Return ONLY valid JSON — no markdown fences, no explanation
"""
        import re as _re

        def _repair(text: str) -> str:
            text = _re.sub(r',\s*([\]}])', r'\1', text)          # trailing commas
            open_b = text.count('{') - text.count('}')
            open_k = text.count('[') - text.count(']')
            # close unclosed string
            in_s = esc = False
            for ch in text:
                if esc:   esc = False; continue
                if ch == '\\': esc = True; continue
                if ch == '"':  in_s = not in_s
            if in_s:
                text = text.rstrip() + '"'
            text = text.rstrip().rstrip(',')
            text += ']' * open_k + '}' * open_b
            return text

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.3,
                    'top_p': 0.95,
                    'max_output_tokens': 8192,
                    'response_mime_type': 'application/json',
                }
            )
            raw = (response.text or "").strip()
            # Extract outer { ... }
            start, end = raw.find('{'), raw.rfind('}')
            if start != -1 and end != -1:
                raw = raw[start:end+1]
            # Try direct parse first, then repair
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return json.loads(_repair(raw))
        except Exception as e:
            print(f"[LiveSessionService] Script generation error: {e}")
            return {}


    # -- Answer Extractor -----------------------------------------------------

    def extract_script_answers(self, questions: list, transcript: str, manual_notes: str = "") -> list:
        """
        Given the current list of script question cards and the accumulated
        transcript (plus any manual notes Ninna typed), ask Gemini to fill in
        the 'answer' and 'status' fields for every question.

        Returns an updated copy of the questions list.
        """
        if not questions or not transcript.strip():
            return questions

        # Build a compact representation of questions for the prompt
        q_summary = []
        for q in questions:
            q_summary.append({
                "id":       q.get("id"),
                "section":  q.get("section"),
                "criterion": q.get("criterion"),
                "pass_condition": q.get("pass_condition"),
                "fail_condition": q.get("fail_condition"),
                "washout_days": q.get("washout_days"),
            })

        context = transcript
        if manual_notes.strip():
            context += f"\n\n[MANUAL NOTES FROM NINNA]: {manual_notes}"

        prompt = f"""You are reviewing a live pre-screening phone call transcript.

For each question below, find the patient's answer in the transcript (or manual notes) and classify the outcome.

TRANSCRIPT / NOTES:
{context}

QUESTIONS (as JSON):
{json.dumps(q_summary, indent=2)}

For EACH question, return updated fields. Return a JSON array where each element is:
{{
  "id": "same id as input",
  "answer": "Exact quote or summary of what patient said, or null if not discussed",
  "status": "open | confirmed_met | confirmed_failed | needs_clarification",
  "source": "auto | manual | none"
}}

Rules:
- "source": "auto" if answer came from the transcript, "manual" if from [MANUAL NOTES], "none" if not found
- For inclusion: status="confirmed_met" means patient PASSED this criterion
- For exclusion: status="confirmed_met" means exclusion IS triggered (BAD for patient)
- If not discussed at all: answer=null, status="open", source="none"
- Return ONLY valid JSON array — no explanation
"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,
                    'max_output_tokens': 8192,
                    'response_mime_type': 'application/json',
                }
            )
            raw = (response.text or "").strip()
            # Extract the JSON array (handles markdown fences etc.)
            start, end = raw.find('['), raw.rfind(']')
            if start != -1 and end != -1:
                raw = raw[start:end+1]

            def _repair_json(s: str) -> str:
                """Best-effort repair for truncated/malformed JSON from Gemini."""
                import re as _re
                # Remove trailing commas before ] or }
                s = _re.sub(r',\s*([\]}])', r'\1', s)
                # Close any open string by finding the last unclosed "
                if s.count('"') % 2 != 0:
                    s = s.rstrip() + '"'
                # Close open objects/arrays
                opens   = s.count('{') - s.count('}')
                s += '}' * max(opens, 0)
                opens_a = s.count('[') - s.count(']')
                s += ']' * max(opens_a, 0)
                return s

            try:
                updates = json.loads(raw)
            except json.JSONDecodeError:
                try:
                    updates = json.loads(_repair_json(raw))
                except json.JSONDecodeError as e2:
                    print(f"[LiveSessionService] JSON repair failed: {e2}")
                    return questions   # Return unchanged on total failure

            # Merge updates back into questions list — always apply when Gemini
            # returns a definitive answer; preserve existing auto-fills otherwise.
            update_map = {u["id"]: u for u in updates}
            updated = []
            for q in questions:
                q = dict(q)
                upd = update_map.get(q.get("id"), {})
                # Apply if Gemini found something new, or if field is still empty
                if upd.get("answer") is not None:
                    q["answer"] = upd["answer"]
                if upd.get("status") and upd["status"] != "open":
                    q["status"] = upd["status"]
                elif upd.get("status") == "open" and q.get("status") == "open":
                    q["status"] = "open"  # keep open
                if upd.get("source") and upd["source"] != "none":
                    q["source"] = upd["source"]
                updated.append(q)
            return updated
        except Exception as e:
            print(f"[LiveSessionService] Answer extraction error: {e}")
            return questions  # Return unchanged on error

    # -- I/E → Script Sync ---------------------------------------------------

    @staticmethod
    def sync_ie_to_script(questions: list, ie_status: dict) -> list:
        """
        Map the results of run_ie_check() back into the script question cards.

        This is the primary way script cards get filled — the I/E check is
        already accurate; we just need to copy its criterion-level results
        (status + evidence) into the matching script card.

        Matching is done by fuzzy keyword lookup on criterion name.
        Returns an updated copy of questions.
        """
        if not questions or not ie_status:
            return questions

        import re as _re

        def _tokens(text: str) -> set:
            """Lower-case word tokens for fuzzy matching."""
            return set(_re.findall(r'[a-z0-9]+', (text or "").lower()))

        # Build lookup lists from I/E check output
        ie_items = (
            [("inclusion", i) for i in ie_status.get("inclusion_criteria", [])]
            + [("exclusion", i) for i in ie_status.get("exclusion_criteria", [])]
        )
        washout_items = ie_status.get("washout_flags", [])

        def _best_match(q_criterion: str, section: str):
            """Return the best-matching ie_item for this criterion."""
            q_tok = _tokens(q_criterion)
            best, best_score = None, 0
            for ie_sec, item in ie_items:
                if section == "washout" or (
                    ie_sec == "inclusion" and section == "inclusion"
                ) or (
                    ie_sec == "exclusion" and section == "exclusion"
                ) or section == "general":
                    i_tok = _tokens(item.get("criterion", ""))
                    if not i_tok:
                        continue
                    common = len(q_tok & i_tok)
                    score  = common / max(len(q_tok | i_tok), 1)
                    if score > best_score and common >= 1:
                        best, best_score = item, score
            return best

        # Status mapping — same convention as I/E check
        STATUS_MAP = {
            "confirmed_met":       "confirmed_met",
            "confirmed_failed":    "confirmed_failed",
            "needs_clarification": "needs_clarification",
            "open":                "open",
        }

        updated = []
        for q in questions:
            q = dict(q)
            section   = q.get("section", "general")
            criterion = q.get("criterion", "")

            if section == "washout":
                # Match against washout flags by medication name
                q_tok = _tokens(criterion)
                for w in washout_items:
                    w_tok = _tokens(w.get("medication", ""))
                    if q_tok & w_tok:
                        wstatus = w.get("status", "unclear")
                        q["status"] = (
                            "confirmed_failed" if wstatus == "compliant"
                            else "confirmed_met" if wstatus == "non_compliant"
                            else "needs_clarification"
                        )
                        q["answer"] = w.get("note") or f"Last dose: {w.get('last_dose_date','unknown')}"
                        q["source"] = "auto"
                        break
            else:
                match = _best_match(criterion, section)
                if match:
                    ie_status_val = match.get("status", "open")
                    mapped = STATUS_MAP.get(ie_status_val, "open")
                    # Only upgrade (open → something definitive), never downgrade
                    current = q.get("status", "open")
                    if current == "open" or mapped != "open":
                        q["status"] = mapped
                    evidence = match.get("evidence")
                    if evidence and not q.get("answer"):
                        q["answer"] = evidence
                        q["source"] = "auto"

            updated.append(q)
        return updated

    # -- Transcription --------------------------------------------------------

    @staticmethod
    def transcribe_chunk(audio_bytes: bytes, whisper_model=None) -> str:
        """
        Transcribe a single audio chunk (bytes) using Faster-Whisper.
        Returns the transcribed text, or an error string.

        Args:
            audio_bytes:   Raw audio bytes from st.audio_input()
            whisper_model: Cached WhisperModel instance (from st.cache_resource)
        """
        import tempfile
        import os

        try:
            from faster_whisper import WhisperModel

            if whisper_model is None:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                whisper_model = WhisperModel("medium", device=device, compute_type=compute_type)

            # Write bytes to a temp file -- Whisper needs a file path
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                segments, _ = whisper_model.transcribe(tmp_path, beam_size=5)
                text = " ".join(seg.text for seg in segments).strip()
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            return text

        except ImportError:
            return "[Error: faster-whisper not installed]"
        except Exception as e:
            return f"[Transcription error: {e}]"

    # -- I/E Evaluation -------------------------------------------------------

    def run_ie_check(self, transcript_so_far: str, protocol_text: str) -> dict:
        """
        Call Gemini with the lightweight I/E prompt and return the structured status dict.

        Uses the same robust JSON repair pipeline as GeminiAIService.extract_data to
        handle Gemini occasionally returning trailing commas or unclosed brackets.
        """
        from live_ie_prompt import LIVE_IE_PROMPT_TEMPLATE
        import re as _re

        # Cap protocol text to keep the prompt manageable
        MAX_PROTO = 25000
        if len(protocol_text) > MAX_PROTO:
            protocol_text = protocol_text[:MAX_PROTO] + "\n\n[Protocol truncated]"

        prompt = LIVE_IE_PROMPT_TEMPLATE.format(
            protocol_context=protocol_text if protocol_text else "No protocol provided.",
            transcript_so_far=transcript_so_far or "(No transcript yet)"
        )

        # ── JSON helpers (same pattern as GeminiAIService.extract_data) ────────

        def _extract_json(raw: str) -> str:
            """Pull JSON object out of any markdown-wrapped response."""
            raw = raw.strip()
            if not raw:
                return ""
            # Try to find ```json ... ``` block
            fence = _re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, _re.DOTALL)
            if fence:
                return fence.group(1).strip()
            if raw.startswith('```'):
                lines = raw.split('\n')
                inner = '\n'.join(lines[1:])
                last = inner.rfind('```')
                if last != -1:
                    inner = inner[:last]
                return inner.strip()
            # Fall back: find outermost { ... }
            start, end = raw.find('{'), raw.rfind('}')
            if start != -1 and end != -1 and end > start:
                return raw[start:end+1].strip()
            return raw

        def _repair_json(text: str) -> str:
            """Close unclosed brackets, remove trailing commas."""
            # Remove trailing commas before } or ]
            text = _re.sub(r',\s*([\]}])', r'\1', text)

            # Count unclosed braces and brackets
            open_braces   = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')

            # Close any unclosed string
            in_string   = False
            escape_next = False
            for ch in text:
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"':
                    in_string = not in_string
            if in_string:
                text = text.rstrip() + '"'

            # Close brackets/braces
            text = text.rstrip().rstrip(',')
            for _ in range(open_brackets):
                text += ']'
            for _ in range(open_braces):
                text += '}'
            return text

        def _safe_parse(raw: str) -> dict:
            """Extract → try parse → try repair → raise."""
            json_str = _extract_json(raw)
            if not json_str:
                raise ValueError(f"No JSON in Gemini response. Raw snippet: {raw[:300]}")
            # First try: direct parse
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            # Second try: repaired
            repaired = _repair_json(json_str)
            return json.loads(repaired)   # Let this raise if still broken

        # ── Gemini call ──────────────────────────────────────────────────────────

        _SAFE_DEFAULT = {
            "inclusion_criteria": [],
            "exclusion_criteria": [],
            "washout_flags": [],
            "summary": {
                "overall_status": "too_early_to_tell",
                "open_count": 0,
                "failed_count": 0,
                "key_concerns": []
            }
        }

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'top_p': 0.9,
                    'max_output_tokens': 4096,
                    'response_mime_type': 'application/json',
                }
            )
            raw = (response.text or "").strip()
            if not raw:
                # Retry once with lower temperature
                print("[LiveSessionService] Empty response, retrying...")
                response = self.model.generate_content(
                    prompt,
                    generation_config={'temperature': 0.1, 'max_output_tokens': 4096,
                                       'response_mime_type': 'application/json'}
                )
                raw = (response.text or "").strip()
            if not raw:
                raise ValueError("Gemini returned empty response after retry")

            return _safe_parse(raw)

        except Exception as e:
            print(f"[LiveSessionService] I/E check error: {e}")
            default = dict(_SAFE_DEFAULT)
            default["summary"] = dict(_SAFE_DEFAULT["summary"])
            default["summary"]["key_concerns"] = [f"I/E check failed: {e}"]
            return default

