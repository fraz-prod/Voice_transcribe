import pyttsx3
from pydub import AudioSegment
import tempfile
import os

INPUT_FILE = "sample.txt"   # your script file
OUTPUT_FILE = "day1_clean.wav"

# Initialize TTS engine
engine = pyttsx3.init()
engine.setProperty("rate", 165)
engine.setProperty("volume", 1.0)

voices = engine.getProperty("voices")

# Print available voices (first run only — optional)
# for v in voices:
#     print(v.id, v.name)

# Usually on Windows:
# voices[0] = Male (David)
# voices[1] = Female (Zira)
male_voice = voices[0].id
female_voice = voices[1].id

combined_audio = AudioSegment.empty()

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    text = line.strip()
    if not text:
        continue

    # Remove speaker label but keep content exact
    if text.startswith("Nurse:"):
        engine.setProperty("voice", female_voice)
        spoken_text = text.replace("Nurse:", "").strip()

    elif text.startswith("Patient:"):
        engine.setProperty("voice", male_voice)
        spoken_text = text.replace("Patient:", "").strip()

    else:
        engine.setProperty("voice", female_voice)
        spoken_text = text

    # Create temporary file per line
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        temp_path = tmpfile.name

    engine.save_to_file(spoken_text, temp_path)
    engine.runAndWait()

    segment = AudioSegment.from_wav(temp_path)
    combined_audio += segment + AudioSegment.silent(duration=250)

    os.remove(temp_path)

# Export final combined WAV
combined_audio.export(OUTPUT_FILE, format="wav")

print("✅ Audio file generated successfully:", OUTPUT_FILE)
