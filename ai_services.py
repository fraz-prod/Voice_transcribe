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
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    
    def extract_data(self, transcript: str) -> dict:
        """Extract structured data from transcript using Gemini 2.0 Flash with overflow capture"""
        
        prompt = ENHANCED_PROMPT_TEMPLATE.format(transcript=transcript)


        try:
            # Use temperature=0.7 for non-deterministic but still accurate extraction
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 3072,  # Increased for overflow content
                }
            )
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                # Find the first newline after ```
                start = response_text.find('\n')
                # Find the closing ```
                end = response_text.rfind('```')
                if start != -1 and end != -1:
                    response_text = response_text[start+1:end].strip()
            
            # Parse JSON
            data = json.loads(response_text)
            return data
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from Gemini response: {e}")
            print(f"Response text: {response_text}")
            raise
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise
