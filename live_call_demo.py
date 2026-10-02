import os
import subprocess
import time
from pathlib import Path

import sounddevice as sd
import whisper
from pydub import AudioSegment

from services.ollama_service import OllamaService


OUTPUT_DIR = Path("./live_demo")
OUTPUT_DIR.mkdir(exist_ok=True)

ollama = OllamaService()


def record_audio(path: str, seconds: int = 8, sr: int = 16000) -> str:
    audio = sd.rec(int(seconds * sr), samplerate=sr, channels=1, dtype='int16')
    sd.wait()
    wav_path = Path(path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    # save to WAV
    audio_segment = AudioSegment(
        audio.tobytes(),
        frame_rate=sr,
        sample_width=audio.dtype.itemsize,
        channels=1,
    )
    audio_segment.export(wav_path, format='wav')
    return str(wav_path)


def transcribe(path: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(path, fp16=False)
    return result.get("text", "").strip()


def speak(text: str, out_path: str):
    subprocess.run([
        "espeak-ng",
        "-v",
        "hi",
        "-w",
        out_path,
        text,
    ], check=True)


if __name__ == '__main__':
    print("Recording for 8 seconds...")
    rec_path = OUTPUT_DIR / "incoming.wav"
    record_audio(str(rec_path), seconds=8)

    print("Transcribing with Whisper...")
    transcript = transcribe(str(rec_path))
    print("Transcript:", transcript)

    prompt = (
        "You are a friendly Indian sales telecaller. "
        "Answer in Hindi if the user speaks Hindi. "
        "Keep it conversational and brief.\n\n"
        f"Customer said: {transcript}"
    )
    reply = ollama.generate(prompt, system_prompt="You are multilingual sales agent")
    print("AI reply:", reply)

    out_path = OUTPUT_DIR / "reply.wav"
    print("Generating speech...")
    speak(reply, str(out_path))
    print(f"Saved reply at: {out_path}")
