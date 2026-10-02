# AI Telecaller Local Setup

This project is a FastAPI-based multilingual telecaller demo using an open-source local LLM and a speech workflow.

## 1) Python environment

Use the workspace venv:

```bash
cd /home/jayesh/voice_agent
/home/jayesh/voice_agent/.venv/bin/python -m pip install -r requirements.txt
```

## 2) Install Ollama

Download and install Ollama from the official site:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then start the service:

```bash
ollama serve
```

In another terminal, pull a local model:

```bash
ollama pull llama3.2
```

Optionally test it:

```bash
ollama run llama3.2 "Say hello in Hindi"
```

## 3) Install system voice tools

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y espeak-ng ffmpeg portaudio19-dev
```

## 4) Install Python voice packages

```bash
/home/jayesh/voice_agent/.venv/bin/python -m pip install openai-whisper sounddevice pydub
```

## 5) Configure environment

Edit config.py or export environment values:

```bash
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2
export DEFAULT_LANGUAGE=hi
export CRM_API_URL=""
export CRM_API_KEY=""
export APP_PORT=8000
```

## 6) Launch the app

```bash
cd /home/jayesh/voice_agent
/home/jayesh/voice_agent/.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Then open:

- http://localhost:8000

## 7) Run the live microphone demo

```bash
cd /home/jayesh/voice_agent
/home/jayesh/voice_agent/.venv/bin/python live_call_demo.py
```

This records audio for 8 seconds, transcribes it with Whisper, sends it to Ollama, and speaks the response back using espeak-ng.

## 8) Recommended production upgrades

- Replace `espeak-ng` with Piper for more natural TTS.
- Add Twilio or Plivo for real telephony dial-out.
- Add CRM sync via `CRM_API_URL` and `CRM_API_KEY`.
- Add lead flagging and call dispositions in the database.
