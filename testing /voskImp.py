import sounddevice as sd
import queue
import sys
import json
from vosk import Model, KaldiRecognizer

# Set the path to your Vosk model folder
MODEL_PATH = "../models/vosk-model-small-en-us-0.15"

# Audio settings
SAMPLE_RATE = 16000  # 16kHz is standard for STT
DEVICE = None        # Default input device

# Load the model
try:
    model = Model(MODEL_PATH)
except Exception as e:
    print(f"Could not load the model from {MODEL_PATH}: {e}")
    sys.exit(1)

# Prepare recognizer and audio stream
recognizer = KaldiRecognizer(model, SAMPLE_RATE)
audio_queue = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(f"[!] Audio input status: {status}", file=sys.stderr)
    audio_queue.put(bytes(indata))

def main():
    print("🎙️ Speak into your mic. Press Ctrl+C to stop.")

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, device=DEVICE,
                           dtype='int16', channels=1, callback=callback):
        try:
            while True:
                data = audio_queue.get()
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    print("📝", result.get("text", ""))
                else:
                    partial = json.loads(recognizer.PartialResult())
                    print("...", partial.get("partial", ""))
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")

if __name__ == "__main__":
    main()
