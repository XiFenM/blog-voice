"""TTS backend protocol.

A backend takes a list of sentences and writes one wav per sentence into
audio_dir, named `0001.wav`, `0002.wav`, … The runner is responsible for
resumability (skipping already-existing files), so backends just need to
synthesize on demand.
"""

from pathlib import Path
from typing import Protocol


class TTSBackend(Protocol):
    name: str
    sample_rate: int

    def synthesize(self, text: str, dest: Path) -> None:
        """Write `text` rendered in the backend's reference voice to `dest`."""
        ...
