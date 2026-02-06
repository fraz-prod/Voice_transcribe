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
            model="gpt-4o-audio-preview",
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
        
        # Visit Date: "Date 26 January 2026" or "26/01/2026" etc.
        # Simple extraction for "YYYY-MM-DD" conversion might be complex without a lib, 
        # so let's capture the string first. The form filler might handle string dates if format matches.
        # User sample: "26 January 26" -> This could mean 2026.
        # Let's try to find a date pattern.
        date_match = re.search(r'(Date|today\'s date)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4})', transcript_clean, re.IGNORECASE)
        if date_match:
             # Basic parsing: "26 January 2026"
             raw_date = date_match.group(2)
             # Basic normalization attempt could go here, but passing raw string might be safer for now
             # if the form filler just puts it in.
             data["visit_date"] = raw_date

        # Subject ID: "Subject ID 0215 dash 301" or "0215-301"
        sid_match = re.search(r'Subject ID\s*([\w\d\-\s]+?)(,|\.|Date)', transcript_clean, re.IGNORECASE)
        if sid_match:
            sid = sid_match.group(1).replace("dash", "-").replace(" ", "")
            data["subject_id"] = sid

        # Initials: "Initials A.K." or "initials JK"
        init_match = re.search(r'Initials\s*([A-Za-z\.]+)', transcript_clean, re.IGNORECASE)
        if init_match:
             # We assume there isn't a field in the mock data for initials, but good to extract if needed.
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

        # Vitals Extraction (Looking for digits)
        
        # Time Collected (Pre-dose)
        # Look for "Time collected" before vitals or related context
        time_pre = extract_time(r'(?:Physical examination pre dose|Visual).*?Time collected\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
        if time_pre:
            data["vitals_pre"]["time_collected"] = time_pre
        
        # Weight: "78 kg" or "78 kilograms" or just "78" after weight context
        w_match = re.search(r'(weight|weigh)\s*(\d{2,3})\s*(kg|kilo|kilogram)?', transcript_clean, re.IGNORECASE)
        if w_match:
            data["vitals_pre"]["weight"] = str(w_match.group(2))

        # BP: "118/76" or "118 over 76" (now converted) or "118.76"
        # Also handle "push you" which Vosk might interpret as "pressure"
        bp_match = re.search(r'(blood pressure|pressure|push)\s*(\d{2,3})[/\.](\d{2,3})', transcript_clean, re.IGNORECASE)
        if bp_match:
            data["vitals_pre"]["bp"] = f"{bp_match.group(2)}/{bp_match.group(3)}"
        
        # HR: "72 bpm" or "heart rate 72" or "bpl" (Vosk misheard bpm)
        hr_match = re.search(r'(heart rate|rate)\s*(\d{2,3})\s*(bpm|bpl|be p m)?', transcript_clean, re.IGNORECASE)
        if not hr_match:
            # Try standalone "XX bpm" pattern
            hr_match = re.search(r'(\d{2,3})\s*(bpm|bpl|be p m)', transcript_clean, re.IGNORECASE)
            if hr_match:
                data["vitals_pre"]["hr"] = str(hr_match.group(1))
        else:
            data["vitals_pre"]["hr"] = str(hr_match.group(2))

        # Temp: "36.8" or "six point eight" (converted) or "36 point 8"
        t_match = re.search(r'(temperature|temp)\s*(\d{2})[.\s]*(\d{1,2})?', transcript_clean, re.IGNORECASE)
        if t_match:
            temp_val = t_match.group(2)
            if t_match.group(3):
                temp_val += "." + t_match.group(3)
            data["vitals_pre"]["temp"] = temp_val

        # RR: "16 breaths" or "respiratory rate 16"
        rr_match = re.search(r'(respiratory rate|respiratory|breaths)\s*(\d{2})', transcript_clean, re.IGNORECASE)
        if not rr_match:
            rr_match = re.search(r'(\d{2})\s*breaths', transcript_clean, re.IGNORECASE)
            if rr_match:
                data["vitals_pre"]["rr"] = str(rr_match.group(1))
        else:
            data["vitals_pre"]["rr"] = str(rr_match.group(2))
        
        # === Post-Dose Vitals (look for "post" context) ===
        # Find vitals after "post-dose" or "1 hour post"
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
        ecg_match = re.search(r'ECG.*?Heart rate\s*(\d{2,3})\s*BPM.*?PR\s*(\d{2,3})\s*msec.*?RR\s*(\d{2,4})\s*msec.*?QRS\s*(\d{2,3})\s*msec.*?QT\s*(\d{2,3})\s*msec', transcript_clean, re.IGNORECASE | re.DOTALL)
        if ecg_match:
            data["ecg"]["hr"] = ecg_match.group(1)
            data["ecg"]["pr"] = ecg_match.group(2)
            data["ecg"]["rr"] = ecg_match.group(3)
            data["ecg"]["qrs"] = ecg_match.group(4)
            data["ecg"]["qt"] = ecg_match.group(5)
        
        # ECG Result
        if re.search(r'Result\s*Normal', transcript_clean, re.IGNORECASE):
            data["ecg"]["result"] = "Normal"
        
        # ECG Date
        ecg_date = re.search(r'ECG.*?(?:Date|Day) performed\s*(.*?)\s+(?:Time|Tom)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if ecg_date:
            data["ecg"]["date"] = ecg_date.group(1).strip()

        # === Labs Extraction ===
        data["labs"] = {"collected": True}
        labs_date = re.search(r'Lab.*?(Date|Day) collected\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4})', transcript_clean, re.IGNORECASE | re.DOTALL)
        if labs_date:
            data["labs"]["date"] = labs_date.group(2)
        
        labs_time = extract_time(r'Lab.*?Time collected\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
        if labs_time:
            data["labs"]["time"] = labs_time
        
        urine_time = extract_time(r'Urine collection time\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
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
        
        preg_date = re.search(r'Collection date\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4})', transcript_clean, re.IGNORECASE)
        if preg_date:
            data["pregnancy"]["date"] = preg_date.group(1)
        
        preg_time = extract_time(r'Collection time\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
        if preg_time:
            data["pregnancy"]["time"] = preg_time

        # === Injection 1 Extraction ===
        # More flexible pattern: "anatomic" or "anatomical", flexible spacing
        inj1_match = re.search(r'Injection\s*1.*?dose administered\s*(\d+)\s*ml.*?anatom\w+\s+location\s+(\w+).*?laterality\s+([\w\s]+?)\s+(route|start)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if inj1_match:
            data["injection"] = {
                "dose": inj1_match.group(1) + " mL",
                "site": inj1_match.group(2),
                "laterality": inj1_match.group(3).strip()
            }
        
        inj1_time_str = extract_time(r'Injection\s*1.*?Start time\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
        if inj1_time_str and "injection" in data:
            data["injection"]["start_time"] = inj1_time_str
        
        inj1_date = re.search(r'Injection\s*1.*?Start date\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4})', transcript_clean, re.IGNORECASE | re.DOTALL)
        if inj1_date and "injection" in data:
            data["injection"]["start_date"] = inj1_date.group(1)

        # === Injection 2 Extraction ===
        # More flexible pattern: "anatomic" or "anatomical", flexible spacing
        inj2_match = re.search(r'Injection\s*2.*?dose administered\s*(\d+)\s*ml.*?anatom\w+\s+location\s+(\w+).*?laterality\s+([\w\s]+?)\s+(route|start)', transcript_clean, re.IGNORECASE | re.DOTALL)
        if inj2_match:
            data["injection_2"] = {
                "dose": inj2_match.group(1) + " mL",
                "site": inj2_match.group(2),
                "laterality": inj2_match.group(3).strip()
            }
        
        inj2_time_str = extract_time(r'Injection\s*2.*?Start time\s*(\d{1,2})[\s:o]+(\d{1,2})', transcript_clean)
        if inj2_time_str and "injection_2" in data:
            data["injection_2"]["start_time"] = inj2_time_str
        
        inj2_date = re.search(r'Injection 2.*?Start date\s*(\d{1,2}\s+[A-Za-z]+\s+\d{2,4})', transcript_clean, re.IGNORECASE | re.DOTALL)
        if inj2_date and "injection_2" in data:
            data["injection_2"]["start_date"] = inj2_date.group(1)
            
        return data
