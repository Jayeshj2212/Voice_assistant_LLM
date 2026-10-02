import os
import requests


class OllamaService:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException:
            return "Local Ollama model unavailable. Please start ollama serve."
