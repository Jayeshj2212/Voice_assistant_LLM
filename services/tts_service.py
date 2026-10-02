import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class TTSService:
    def __init__(self, engine: str = "f5", voice: str = "hi"):
        self.engine = engine.lower()
        self.voice = voice
        self._f5_model = None

    def synthesize(self, text: str, output_path: str, ref_audio: str | None = None, ref_text: str | None = None) -> str:
        if self.engine == "piper":
            return self._synthesize_with_piper(text, output_path)
        if self.engine == "espeak":
            return self._synthesize_with_espeak(text, output_path)
        if self.engine == "f5":
            try:
                return self._synthesize_with_f5(text, output_path, ref_audio=ref_audio, ref_text=ref_text)
            except TimeoutError:
                fallback_engine = os.getenv("F5_TTS_FALLBACK_ENGINE", "espeak")
                if fallback_engine == "espeak":
                    return self._synthesize_with_espeak(text, output_path)
                return self._synthesize_with_fallback(text, output_path)
        return self._synthesize_with_fallback(text, output_path)

    def _synthesize_with_piper(self, text: str, output_path: str) -> str:
        piper_bin = os.getenv("PIPER_BIN", "/usr/local/bin/piper")
        voice_path = os.getenv("PIPER_VOICE_PATH", "")
        if not voice_path:
            raise FileNotFoundError("Set PIPER_VOICE_PATH for Piper TTS voice files.")

        model_path = os.path.join(voice_path, f"{self.voice}.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model missing: {model_path}")

        cmd = [piper_bin, "--model", model_path, "--output_file", output_path]
        subprocess.run(cmd, input=text, text=True, check=True)
        return output_path

    def _synthesize_with_espeak(self, text: str, output_path: str) -> str:
        lang_map = {"hi": "hi+f3", "bn": "bn+f3", "en": "en-us+f3"}
        lang = lang_map.get(self.voice, "en-us+f3")
        subprocess.run([
            "espeak-ng",
            "-v",
            lang,
            "-s",
            "150",
            "-p",
            "50",
            "-g",
            "5",
            "-w",
            output_path,
            text,
        ], check=True)
        return output_path

    def _synthesize_with_f5(self, text: str, output_path: str, ref_audio: str | None = None, ref_text: str | None = None) -> str:
        from f5_tts.api import F5TTS

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        ref_audio = ref_audio or os.getenv(
            "F5_TTS_REF_AUDIO",
            "/home/jayesh/voice_agent/.venv/lib/python3.11/site-packages/f5_tts/infer/examples/basic/basic_ref_en.wav",
        )
        ref_text = ref_text or os.getenv(
            "F5_TTS_REF_TEXT",
            "Some call me nature, others call me mother nature.",
        )

        if not os.path.exists(ref_audio):
            raise FileNotFoundError(f"F5-TTS reference audio is missing: {ref_audio}")

        timeout_seconds = int(os.getenv("F5_TTS_TIMEOUT_SECONDS", "45"))

        def run_inference():
            if self._f5_model is None:
                self._f5_model = F5TTS(device="cpu")
            self._f5_model.infer(
                ref_file=ref_audio,
                ref_text=ref_text,
                gen_text=text,
                file_wave=output_path,
                remove_silence=True,
                seed=42,
            )
            return output_path

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_inference)
            try:
                future.result(timeout=timeout_seconds)
            except TimeoutError as exc:
                executor.shutdown(wait=False, cancel_futures=True)
                raise TimeoutError(
                    f"F5-TTS inference exceeded {timeout_seconds}s on this CPU environment. "
                    "Set F5_TTS_FALLBACK_ENGINE=espeak or use a CUDA-enabled machine for live calls."
                ) from exc
        return output_path

    def _synthesize_with_fallback(self, text: str, output_path: str) -> str:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path
