import wave
import math
import struct

def generate_silent_wav(filename, duration_sec=3):
    sample_rate = 44100
    n_frames = sample_rate * duration_sec
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Write silence (0)
        data = struct.pack('<h', 0) * n_frames
        wav_file.writeframes(data)
    
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_silent_wav("sample_recording.wav")
