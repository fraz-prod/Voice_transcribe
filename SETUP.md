# Voice Transcribe - Setup Instructions

This document outlines the setup steps for the Voice Transcribe project.

## System Requirements

- **Python**: 3.13+
- **FFmpeg**: Required for audio processing with `pydub`

## Installation Steps

### 1. Install System Dependencies

#### macOS (using Homebrew)
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### Windows
Download and install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)

### 2. Install Python Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Download Vosk Model (for Local Mode)

```bash
python download_model.py
```

This will download the English language model (~1.8GB) required for offline transcription.

### 4. Configure API Keys (for Live Mode)

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Troubleshooting

### Python 3.13 Compatibility

This project includes a compatibility shim for the `audioop` module which was removed in Python 3.13. The `audioop-lts` package is automatically installed via `requirements.txt`.

### FFmpeg Not Found

If you see errors about `ffprobe` not being found, ensure FFmpeg is installed and available in your system PATH:

```bash
which ffprobe  # macOS/Linux
where ffprobe  # Windows
```
