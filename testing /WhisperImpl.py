import sounddevice as sd
import whisper
import numpy as np
import scipy.io.wavfile
import tempfile
import os

# === Settings ===
SAMPLE_RATE = 16000
MODEL_SIZE = "small"
CHANNELS = 1
DTYPE = 'float32'
print("Loading Whisper model...")
model = whisper.load_model(MODEL_SIZE)
print("Whisper model loaded.")

def record_audio():
    print("Recording... Press Ctrl+C to stop.")
    recording = []

    def callback(indata, frames, time, status):
        if status:
            print(f"[!] {status}")
        recording.append(indata.copy())

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype=DTYPE, callback=callback):
            sd.sleep(10000000)  # Effectively infinite
    except KeyboardInterrupt:
        print("Recording stopped.")
        return np.concatenate(recording, axis=0)

# === Transcribe Recorded Audio ===
def transcribe_audio(audio_data):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        filepath = tmpfile.name
        scipy.io.wavfile.write(filepath, SAMPLE_RATE,
                               (audio_data * 32767).astype(np.int16))

    result = model.transcribe(filepath, fp16=False)
    os.remove(filepath)
    return result["text"]

def main():
    audio = record_audio()
    transcript = transcribe_audio(audio)
    print("Final Transcript:")
    print(transcript.strip())

if __name__ == "__main__":
    main()
