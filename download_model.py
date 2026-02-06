import os
import requests
import zipfile
from tqdm import tqdm

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
MODEL_ZIP = "vosk-model-en-us-0.22.zip"
MODEL_DIR = "vosk-model-en-us-0.22"
TARGET_DIR = "model"

def download_file(url, filename):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    print(f"Downloading {filename}...")
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)

def setup_model():
    # Check if target model directory exists
    if os.path.exists(TARGET_DIR):
        print(f"Model directory '{TARGET_DIR}' already exists. Skipping download.")
        return

    # Check if unzipped folder exists (maybe renamed)
    if os.path.exists(MODEL_DIR):
        print(f"Found unzipped model folder '{MODEL_DIR}'. Renaming to '{TARGET_DIR}'...")
        os.rename(MODEL_DIR, TARGET_DIR)
        return

    # Download if zip doesn't exist
    if not os.path.exists(MODEL_ZIP):
        download_file(MODEL_URL, MODEL_ZIP)
    
    # Unzip
    print(f"Unzipping {MODEL_ZIP}...")
    with zipfile.ZipFile(MODEL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Rename to 'model' for simplicity in code
    if os.path.exists(MODEL_DIR):
        os.rename(MODEL_DIR, TARGET_DIR)
        print("Model setup complete.")
        
        # Cleanup zip
        os.remove(MODEL_ZIP)
    else:
        print("Error: Extracted directory not found.")

if __name__ == "__main__":
    setup_model()
