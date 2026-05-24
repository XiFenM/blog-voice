"""Run a TTS backend over every sentence in an article.

Resumability: a wav already on disk with non-zero size is skipped, so
Ctrl-C and restart is safe.
"""

import time
from pathlib import Path

from blog_voice.tts.base import TTSBackend


def read_sentences(sentences_path: Path) -> list[str]:
    return [
        s.strip()
        for s in sentences_path.read_text(encoding="utf-8").split("\n\n")
        if s.strip()
    ]


def run(
    backend: TTSBackend,
    sentences: list[str],
    audio_dir: Path,
    limit: int = 0,
    suffix: str = ".wav",
) -> None:
    audio_dir.mkdir(parents=True, exist_ok=True)
    if limit:
        sentences = sentences[:limit]
    print(f"sentences: {len(sentences)}  backend: {backend.name}  out: {audio_dir}")

    for i, sent in enumerate(sentences, 1):
        dest = audio_dir / f"{i:04d}{suffix}"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        t0 = time.time()
        backend.synthesize(sent, dest)
        elapsed = time.time() - t0
        preview = sent[:60] + ("…" if len(sent) > 60 else "")
        print(f"[{i:04d}/{len(sentences)}] {elapsed:6.1f}s  {preview}")
