import queue
import wave

import numpy as np


_SAMPLE_RATE = 16000
_CHANNELS = 1


class RecorderError(Exception):
    pass


class PushToTalkRecorder:
    def __init__(self, sample_rate: int = _SAMPLE_RATE):
        self._sample_rate = sample_rate

    def record_interactive(self) -> np.ndarray:
        """ENTER to start, ENTER to stop. Returns 16kHz mono float32 numpy array."""
        try:
            import sounddevice as sd
        except ImportError as e:
            raise RecorderError(f"sounddevice not installed: {e}\nRun: pip install sounddevice") from e

        input("Press ENTER to start speaking...")
        print("Recording... press ENTER to stop.")

        audio_queue: queue.Queue = queue.Queue()

        def _callback(indata, frames, time, status):
            if status:
                print(f"[recorder warning] {status}")
            audio_queue.put(indata.copy())

        try:
            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=_CHANNELS,
                dtype="float32",
                callback=_callback,
            ):
                input()
        except sd.PortAudioError as e:
            if "Invalid input device" in str(e) or "No Default Input Device" in str(e):
                raise RecorderError(
                    "Microphone not accessible.\n"
                    "Grant Terminal microphone permission:\n"
                    "  System Settings → Privacy & Security → Microphone"
                ) from e
            raise RecorderError(f"Audio device error: {e}") from e

        chunks = []
        while not audio_queue.empty():
            chunks.append(audio_queue.get())

        if not chunks:
            return np.zeros(0, dtype=np.float32)

        return np.concatenate(chunks, axis=0).flatten()

    def save_wav(self, buffer: np.ndarray, path: str) -> None:
        """Write a float32 mono buffer to a 16kHz 16-bit WAV file."""
        audio_int16 = np.clip(buffer * 32767, -32768, 32767).astype(np.int16)
        with wave.open(path, "w") as wf:
            wf.setnchannels(_CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio_int16.tobytes())
