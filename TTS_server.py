from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import io
from TTS.api import TTS
import soundfile as sf
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tts_models = {
    "en": TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False),
    "fr": TTS(model_name="tts_models/fr/css10/vits", progress_bar=False),
}

class TTSRequest(BaseModel):
    text: str
    language: str

@app.post("/speak")
async def generate_tts(req: TTSRequest):
    if req.language not in tts_models:
        return {"error": "Unsupported language"}

    tts = tts_models[req.language]
    audio_array = tts.tts(req.text)
    sample_rate = tts.synthesizer.output_sample_rate

    buffer = io.BytesIO()
    sf.write(buffer, audio_array, sample_rate, format='WAV')
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="audio/wav")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)