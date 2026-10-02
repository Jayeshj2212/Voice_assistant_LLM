import os
from pathlib import Path


class WhisperService:
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def load_model(self):
        try:
            import whisper
            self._model = whisper.load_model(self.model_name)
            return self._model
        except Exception:
            self._model = None
            return None

    def transcribe_audio(self, audio_path: str) -> str:
        if self._model is None:
            self.load_model()
        if self._model is None:
            return "Transcription unavailable: local Whisper model not installed."

        result = self._model.transcribe(audio_path, fp16=False)
        return result.get("text", "").strip()

    def record_from_microphone(self, output_path: str, seconds: int = 10):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            import sounddevice as sd
            import numpy as np
            import wave

            sample_rate = 16000
            audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()

            with wave.open(str(output_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio.tobytes())

            return str(output_path)
        except Exception as exc:
            raise RuntimeError(f"Microphone capture unavailable: {exc}")
