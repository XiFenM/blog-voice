"""Generate per-sentence TTS using Chatterbox with a reference voice.

Output: one wav per sentence in OUT_DIR. Resumable — already-existing files are skipped.

Usage:
    uv run python generate_tts.py [--sentences FILE] [--ref WAV] [--out DIR] [--limit N]
"""

import argparse
import time
from pathlib import Path

import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sentences", default="pytorch_internals_sentences.txt")
    p.add_argument("--ref", default="voices/爱弥斯/022_自我介绍.wav")
    p.add_argument("--out", default="tts_out")
    p.add_argument("--limit", type=int, default=0, help="0 = all sentences")
    p.add_argument("--device", default="cpu")
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    sentences = [
        s.strip()
        for s in Path(args.sentences).read_text().split("\n\n")
        if s.strip()
    ]
    if args.limit:
        sentences = sentences[: args.limit]
    print(f"sentences: {len(sentences)}  device: {args.device}  ref: {args.ref}")

    print("loading model …")
    t0 = time.time()
    model = ChatterboxTTS.from_pretrained(device=args.device)
    print(f"model loaded in {time.time() - t0:.1f}s, sr={model.sr}")

    for i, sent in enumerate(sentences, 1):
        dest = out_dir / f"{i:04d}.wav"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        t0 = time.time()
        wav = model.generate(text=sent, audio_prompt_path=args.ref)
        torchaudio.save(str(dest), wav, model.sr)
        dur = wav.shape[-1] / model.sr
        elapsed = time.time() - t0
        print(
            f"[{i:03d}/{len(sentences)}] {elapsed:6.1f}s → {dur:5.1f}s audio "
            f"(rt×{elapsed/max(dur,0.01):.1f})  {sent[:60]}{'…' if len(sent)>60 else ''}"
        )


if __name__ == "__main__":
    main()
