try:
    from faster_whisper import WhisperModel
    print("SUCCESS: faster-whisper is installed and importable.")
    print("You can now run the app with 'streamlit run app.py' and select 'Local Whisper Mode'.")
except ImportError:
    print("ERROR: faster-whisper is NOT installed.")
    print("Please run: pip install -r requirements.txt")
except Exception as e:
    print(f"An error occurred: {e}")
