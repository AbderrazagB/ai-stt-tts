import sounddevice as sd
import numpy as np
import scipy.io.wavfile
import tempfile
import os
from faster_whisper import WhisperModel

# === Settings ===
SAMPLE_RATE = 16000
MODEL_SIZE = "small"  # Can be: tiny, base, small, medium, large-v1, large-v2
CHANNELS = 1
DTYPE = 'float32'
COMPUTE_TYPE = "int8"  # Options: int8, float16, float32

print("🔄 Loading Faster-Whisper model...")
model = WhisperModel(MODEL_SIZE, compute_type=COMPUTE_TYPE)
print("✅ Model loaded.")

def record_audio():
    print("🎙️ Recording... Press Ctrl+C to stop.")
    recording = []

    def callback(indata, frames, time, status):
        if status:
            print(f"[!] {status}")
        recording.append(indata.copy())

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype=DTYPE, callback=callback):
            sd.sleep(10000000)
    except KeyboardInterrupt:
        print("🛑 Recording stopped.")
        return np.concatenate(recording, axis=0)

def transcribe_audio(audio_data):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        filepath = tmpfile.name
        scipy.io.wavfile.write(filepath, SAMPLE_RATE,
                               (audio_data * 32767).astype(np.int16))

    segments, _ = model.transcribe(filepath)

    # Collect full transcript
    transcript = ""
    for segment in segments:
        transcript += segment.text + " "

    os.remove(filepath)
    return transcript.strip()

def main():
    audio = record_audio()
    transcript = transcribe_audio(audio)
    print("\n📝 Final Transcript:\n")
    print(transcript)

if __name__ == "__main__":
    main()
