import os
import re
import subprocess
import tempfile
import wave
from pathlib import Path


_DEFAULT_BINARY = str(Path.home() / "AI-Projects/whisper.cpp/build/bin/whisper-cli")
_DEFAULT_MODEL = str(Path.home() / "AI-Projects/whisper.cpp/models/ggml-large-v3-turbo.bin")

_TIMESTAMP_RE = re.compile(r"\[\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\]\s+(.*)")


class SpeechToTextError(Exception):
    pass


class SpeechToText:
    def __init__(self, config: dict = None):
        cfg = (config or {}).get("voice", {})
        self._binary = cfg.get("whisper_binary", _DEFAULT_BINARY)
        self._model = cfg.get("whisper_model", _DEFAULT_MODEL)
        self._validate_setup()

    def _validate_setup(self) -> None:
        if not os.path.isfile(self._binary):
            raise SpeechToTextError(
                f"whisper-cli binary not found at: {self._binary}\n"
                "Run the Block 0.2 setup:\n"
                "  cd ~/AI-Projects && git clone https://github.com/ggml-org/whisper.cpp\n"
                "  cd whisper.cpp && cmake -B build -DWHISPER_METAL=ON && cmake --build build -j\n"
                "  bash ./models/download-ggml-model.sh large-v3-turbo"
            )
        if not os.path.isfile(self._model):
            raise SpeechToTextError(
                f"whisper model not found at: {self._model}\n"
                "Download it with:\n"
                "  cd ~/AI-Projects/whisper.cpp && bash ./models/download-ggml-model.sh large-v3-turbo"
            )

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an existing WAV file and return the text."""
        result = subprocess.run(
            [self._binary, "-m", self._model, "-f", audio_path, "--no-prints"],
            capture_output=True,
            text=True,
        )
        return self._parse_output(result.stdout + result.stderr)

    def record_and_transcribe(self, audio_buffer, sample_rate: int = 16000) -> str:
        """Transcribe a numpy audio buffer. Saves to a temp WAV, transcribes, cleans up."""
        import numpy as np

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            audio_int16 = np.clip(audio_buffer * 32767, -32768, 32767).astype(np.int16)
            with wave.open(tmp_path, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_int16.tobytes())
            return self.transcribe_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _parse_output(self, output: str) -> str:
        """Extract transcribed text from whisper-cli stdout."""
        lines = []
        for line in output.splitlines():
            m = _TIMESTAMP_RE.match(line.strip())
            if m:
                text = m.group(1).strip()
                if text:
                    lines.append(text)
        return " ".join(lines).strip()
