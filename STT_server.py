from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from faster_whisper import WhisperModel
import numpy as np
import scipy.io.wavfile
import soundfile as sf
import tempfile
import os
import requests
import subprocess
from io import BytesIO
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

import datetime

# === Settings ===
SAMPLE_RATE = 16000
MODEL_SIZE = "small"
COMPUTE_TYPE = "int8"

# === Initialize Model ===
print("🔄 Loading Faster-Whisper model...")
model = WhisperModel(MODEL_SIZE, compute_type=COMPUTE_TYPE)
print("✅ Model loaded.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def load_and_resample_audio(input_bytes: bytes) -> np.ndarray:
    # FFmpeg: WebM (Opus) -> WAV (mono, 16kHz)
    process = subprocess.Popen(
        [
            "ffmpeg",
            "-f", "webm",
            "-i", "pipe:0",
            "-f", "wav",
            "-ar", str(SAMPLE_RATE),
            "-ac", "1",
            "-loglevel", "error",
            "pipe:1"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output, err = process.communicate(input=input_bytes)

    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err.decode()}")

    # Read WAV bytes as float32 PCM
    audio_bytes = BytesIO(output)
    audio_data, sr = sf.read(audio_bytes)

    if sr != SAMPLE_RATE:
        raise ValueError(f"Unexpected sample rate {sr}, expected {SAMPLE_RATE}")

    return audio_data.astype(np.float32)



def transcribe_audio(audio_data: np.ndarray) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        scipy.io.wavfile.write(tmpfile.name, SAMPLE_RATE,
                               (audio_data * 32767).astype(np.int16))
        filepath = tmpfile.name

    segments, _ = model.transcribe(filepath)

    transcript = " ".join(segment.text for segment in segments)
    os.remove(filepath)
    return transcript.strip()

@app.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    try:
        # Step 1: Read uploaded audio content
        content = await file.read()
        print(f"📦 Received file size: {len(content)} bytes")

        # Optional: Save a debug copy
        with open("debug_recording.webm", "wb") as f:
            f.write(content)

        # Step 2: Load & resample audio, then transcribe
        audio_data = await load_and_resample_audio(content)
        transcript = transcribe_audio(audio_data)
        print(f"📝 Transcript: {transcript}")

        # ✅ Return only the transcript
        return JSONResponse(content={"transcript": transcript})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)