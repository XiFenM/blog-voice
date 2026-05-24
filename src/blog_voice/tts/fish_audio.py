"""Fish Audio API TTS backend.

Two reference modes:

1. `reference_id` — a voice clone model registered in your fish.audio account.
   This is the fastest and most consistent option for long runs.

2. Local wav file — uploaded inline as a `ReferenceAudio` with a transcript.
   The transcript must match the spoken content of the reference clip; we
   obtain it via fish.audio's ASR and cache the result next to the wav as
   `<name>.transcript.txt` so we only pay for the transcription once.

API key is read from $FISH_API_KEY (or $FISH_AUDIO_API_KEY for backwards
compatibility with older docs).
"""

import os
import wave
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv


def _read_api_key() -> str:
    load_dotenv()
    key = os.environ.get("FISH_API_KEY") or os.environ.get("FISH_AUDIO_API_KEY")
    if not key:
        raise SystemExit(
            "FISH_API_KEY is missing. Get one at https://fish.audio/app/api-keys "
            "and put it in .env."
        )
    return key


def _transcribe_reference(client, ref_voice: Path, language: str) -> str:
    cache = ref_voice.with_suffix(ref_voice.suffix + ".transcript.txt")
    if cache.exists() and cache.read_text(encoding="utf-8").strip():
        return cache.read_text(encoding="utf-8").strip()

    print(f"fish: transcribing reference {ref_voice.name} via ASR (lang={language})…")
    result = client.asr.transcribe(audio=ref_voice.read_bytes(), language=language)
    transcript = (result.text or "").strip()
    if not transcript:
        raise SystemExit(f"ASR returned empty transcript for {ref_voice}")
    cache.write_text(transcript + "\n", encoding="utf-8")
    print(f"fish: cached transcript ({len(transcript)} chars) → {cache.name}")
    return transcript


class FishAudioBackend:
    name = "fish"

    def __init__(
        self,
        ref_voice: Path | None = None,
        reference_id: str = "",
        ref_language: str = "zh",
        model: str = "s2-pro",
        audio_format: str = "wav",
        sample_rate: int = 44100,
    ):
        try:
            from fishaudio import FishAudio
            from fishaudio.types import ReferenceAudio, TTSConfig
        except ImportError as exc:
            raise SystemExit(
                "fish-audio-sdk is not installed. Run `uv sync` to install it."
            ) from exc

        self._FishAudio = FishAudio
        self._ReferenceAudio = ReferenceAudio
        self._TTSConfig = TTSConfig
        self.client = FishAudio(api_key=_read_api_key())
        self.reference_id = reference_id.strip()
        self.ref_voice = ref_voice
        self.ref_language = ref_language
        self.model = model
        self.audio_format = audio_format
        self._sample_rate = sample_rate
        self._references = None

        if not self.reference_id and ref_voice is None:
            raise SystemExit(
                "fish backend needs either --fish-reference-id or --ref <wav>"
            )
        if not self.reference_id and ref_voice is not None and not ref_voice.exists():
            raise SystemExit(f"reference voice not found: {ref_voice}")

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _build_references(self):
        if self._references is not None or self.reference_id:
            return self._references
        transcript = _transcribe_reference(self.client, self.ref_voice, self.ref_language)
        self._references = [
            self._ReferenceAudio(audio=self.ref_voice.read_bytes(), text=transcript)
        ]
        return self._references

    def synthesize(self, text: str, dest: Path) -> None:
        # SDK v1.3.0: format / sample_rate live inside TTSConfig.
        # reference_id / references stay as top-level convert() kwargs.
        config = self._TTSConfig(
            format=self.audio_format,
            sample_rate=self._sample_rate,
        )
        kwargs = dict(text=text, model=self.model, config=config)
        if self.reference_id:
            kwargs["reference_id"] = self.reference_id
        else:
            kwargs["references"] = self._build_references()

        audio = self.client.tts.convert(**kwargs)
        audio_bytes = audio if isinstance(audio, (bytes, bytearray)) else bytes(audio)
        dest.write_bytes(audio_bytes)
        self._sample_rate = _peek_wav_sample_rate(audio_bytes) or self._sample_rate


def _peek_wav_sample_rate(data: bytes) -> int | None:
    if len(data) < 44 or data[:4] != b"RIFF":
        return None
    try:
        with wave.open(BytesIO(data), "rb") as wav_file:
            return wav_file.getframerate()
    except wave.Error:
        return None
