import os
from openai import OpenAI
import base64
from dotenv import load_dotenv

load_dotenv()

def test_transcription_endpoint(client, model_name, audio_path):
    print(f"\n[Testing] Transcription Endpoint with model: {model_name}")
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model_name,
                file=audio_file
            )
        print(f"Success! Transcript: {transcript.text}")
        return True
    except Exception as e:
        print(f"Failed. Error: {e}")
        return False

def test_chat_audio_endpoint(client, model_name, audio_path):
    print(f"\n[Testing] Chat Completion (Audio Input) with model: {model_name}")
    try:
        # Read audio and encode to base64
        with open(audio_path, "rb") as audio_file:
            audio_b64 = base64.b64encode(audio_file.read()).decode("utf-8")

        response = client.chat.completions.create(
            model=model_name,
            modalities=["text"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you hear in this audio. If you hear a sine wave or beep, say that."},
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_b64,
                                "format": "wav"
                            }
                        }
                    ]
                }
            ]
        )
        print(f"Success! Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"Failed. Error: {e}")
        return False

if __name__ == "__main__":
    client = OpenAI()
    audio_path = "sample_recording.wav"
    target_model = "gpt-audio-mini-2025-12-15"
    
    if not os.path.exists(audio_path):
        print(f"Error: {audio_path} not found. Run generate_audio.py first.")
        exit(1)

    # 1. Try standard transcription endpoint (simplest, drop-in replacement)
    success = test_transcription_endpoint(client, target_model, audio_path)
    
    # 2. If failure, try Chat Audio input
    if not success:
        test_chat_audio_endpoint(client, target_model, audio_path)
