# Manual Vosk Model Setup Instructions

## Quick Setup (recommended)

1. **Download the model** from:
   https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
   (Size: 1.8 GB - best accuracy)

2. **Save to this directory**:
   C:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\

3. **Extract the ZIP** - you'll get a folder named: `vosk-model-en-us-0.22`

4. **Rename that folder** to: `model`

5. **Final path should be**:
   ```
   C:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\model\
   C:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\model\am\
   C:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\model\graph\
   C:\Users\RagaAI_User\Desktop\vooo\Voice_transcribe\model\ivector\
   ```

## Alternative: Smaller/Faster Model (if you want to test quickly)

If you want a smaller download (128 MB instead of 1.8 GB):

1. **Download**: https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip

2. Follow the same steps above

**Note**: The smaller model is faster but less accurate. For medical transcription, the larger model is recommended.

## After Setup

Once the model is in place, just run the Streamlit app normally:
```bash
streamlit run app.py
```

The app will use the new model automatically and transcription quality should be much better (e.g., correctly hearing "seventy eight" instead of "seventy").
