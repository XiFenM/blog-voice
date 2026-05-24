"""Concatenate per-sentence wavs into a single merged wav.

Reads via `soundfile` so the input can be either PCM or float-encoded
(chatterbox writes IEEE_FLOAT, fish-audio writes PCM). The output is
always 16-bit PCM mono at the input's sample rate.

Optionally inserts a short silence gap between sentences for a more
natural read.

Returns the per-sentence end-timestamps (seconds, relative to the start
of the merged file), so the LRC generator can use the exact same timing
as what listeners will hear.
"""

from pathlib import Path

import numpy as np
import soundfile as sf


def merge_wavs(
    audio_files: list[Path],
    out_path: Path,
    gap_seconds: float = 0.0,
) -> list[float]:
    if not audio_files:
        raise SystemExit("no audio files to merge")

    base_data, base_sr = sf.read(str(audio_files[0]), always_2d=False, dtype="float32")
    base_channels = 1 if base_data.ndim == 1 else base_data.shape[1]
    silence_frames = int(gap_seconds * base_sr)
    silence = np.zeros(silence_frames, dtype="float32") if silence_frames > 0 else None

    out_path.parent.mkdir(parents=True, exist_ok=True)
    timestamps: list[float] = []
    elapsed_frames = 0
    parts: list[np.ndarray] = []

    for i, path in enumerate(audio_files):
        data, sr = sf.read(str(path), always_2d=False, dtype="float32")
        if sr != base_sr:
            raise SystemExit(
                f"{path} sample rate {sr} != first file {base_sr}; "
                "re-run TTS so all clips share the same format"
            )
        if data.ndim > 1:
            data = data.mean(axis=1)
        if base_channels != 1:
            data = data.mean(axis=1) if data.ndim > 1 else data
        parts.append(data)
        elapsed_frames += len(data)
        timestamps.append(elapsed_frames / base_sr)
        if i < len(audio_files) - 1 and silence is not None:
            parts.append(silence)
            elapsed_frames += silence_frames

    merged = np.concatenate(parts) if parts else np.zeros(0, dtype="float32")
    sf.write(str(out_path), merged, base_sr, subtype="PCM_16")

    total = elapsed_frames / base_sr
    print(f"merged {len(audio_files)} files -> {out_path} ({total:.1f}s)")
    return timestamps
