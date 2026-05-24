"""Chatterbox local TTS backend.

Downloads model weights once into `.model-cache/chatterbox/` and reuses them.
Always passes the same reference clip to every sentence to prevent voice
drift on the autoregressive model (see voice.md §2).
"""

import os
from pathlib import Path

import httpx
import torchaudio
from chatterbox.tts import ChatterboxTTS

REPO_ID = "ResembleAI/chatterbox"
MODEL_FILES = [
    "ve.safetensors",
    "t3_cfg.safetensors",
    "s3gen.safetensors",
    "tokenizer.json",
    "conds.pt",
]


def _ensure_model_files(model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
    with httpx.Client(timeout=None, follow_redirects=True) as client:
        for filename in MODEL_FILES:
            dest = model_dir / filename
            if dest.exists() and dest.stat().st_size > 0:
                print(f"model [skip] {filename} ({dest.stat().st_size // (1024 * 1024)} MiB)")
                continue

            url = f"{endpoint}/{REPO_ID}/resolve/main/{filename}"
            tmp = dest.with_suffix(dest.suffix + ".part")
            if tmp.exists():
                tmp.unlink()

            print(f"model [get ] {filename} from {url}")
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", "0"))
                downloaded = 0
                next_report = 5
                with tmp.open("wb") as fh:
                    for chunk in resp.iter_bytes(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        fh.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            percent = downloaded * 100 // total
                            while percent >= next_report:
                                print(
                                    f"model [dl  ] {filename} {next_report}% "
                                    f"({downloaded // (1024 * 1024)} / {total // (1024 * 1024)} MiB)"
                                )
                                next_report += 5

            tmp.replace(dest)
            print(f"model [ok  ] {filename} -> {dest}")


def _load_model(model_dir: Path, device: str) -> ChatterboxTTS:
    if not all((model_dir / filename).exists() for filename in MODEL_FILES):
        _ensure_model_files(model_dir)
    print(f"loading model from local dir {model_dir}")
    return ChatterboxTTS.from_local(model_dir, device)


class ChatterboxBackend:
    name = "chatterbox"

    def __init__(self, ref_voice: Path, device: str = "cpu", model_dir: Path | None = None):
        if not ref_voice.exists():
            raise SystemExit(f"reference voice not found: {ref_voice}")
        self.ref_voice = ref_voice
        self.device = device
        self.model_dir = model_dir or Path(".model-cache/chatterbox")
        self._model: ChatterboxTTS | None = None

    @property
    def model(self) -> ChatterboxTTS:
        if self._model is None:
            self._model = _load_model(self.model_dir, self.device)
        return self._model

    @property
    def sample_rate(self) -> int:
        return self.model.sr

    def synthesize(self, text: str, dest: Path) -> None:
        wav = self.model.generate(text=text, audio_prompt_path=str(self.ref_voice))
        torchaudio.save(str(dest), wav, self.model.sr)
