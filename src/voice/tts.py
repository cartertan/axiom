import os
import tempfile

import numpy as np

_VOXTRAL_REPO = "mlx-community/Voxtral-4B-TTS-2603-mlx-4bit"
_DEFAULT_VOICE = "neutral_male"


class TextToSpeechError(Exception):
    pass


class TextToSpeech:
    def __init__(self, config: dict = None):
        cfg = (config or {}).get("voice", {})
        self._repo = cfg.get("tts_model", _VOXTRAL_REPO)
        self._voice = cfg.get("voice_name", _DEFAULT_VOICE)
        self._speed = cfg.get("speed", 1.0)
        self._model = None  # loaded on first use

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from mlx_audio.tts.utils import load
            print(f"[TTS] Loading {self._repo} (first run will download ~2.5GB)...")
            self._model = load(self._repo)
        except ImportError as e:
            raise TextToSpeechError(
                f"mlx-audio not installed: {e}\nRun: pip install mlx-audio"
            ) from e
        except Exception as e:
            raise TextToSpeechError(f"Failed to load TTS model: {e}") from e

    def speak(self, text: str) -> None:
        """Clean text, generate audio with Voxtral, and play it through speakers."""
        from mlx_audio.tts.generate import generate_audio
        from src.voice.text_cleaner import clean_for_speech

        self._load_model()
        cleaned = clean_for_speech(text)
        if not cleaned.strip():
            return

        generate_audio(
            text=cleaned,
            model=self._model,
            voice=self._voice,
            speed=self._speed,
            stream=True,
            play=True,
            verbose=False,
        )

    def save_audio(self, text: str, path: str) -> None:
        """Generate speech for text and save to the given WAV path."""
        from mlx_audio.tts.generate import generate_audio
        from src.voice.text_cleaner import clean_for_speech

        self._load_model()
        cleaned = clean_for_speech(text)
        if not cleaned.strip():
            return

        out_dir = os.path.dirname(os.path.abspath(path))
        file_prefix = os.path.splitext(os.path.basename(path))[0]

        generate_audio(
            text=cleaned,
            model=self._model,
            voice=self._voice,
            speed=self._speed,
            output_path=out_dir,
            file_prefix=file_prefix,
            join_audio=True,
            play=False,
            verbose=False,
        )
