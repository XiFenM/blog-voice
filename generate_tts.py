"""Generate per-sentence TTS using Chatterbox with a reference voice.

Output: one wav per sentence in OUT_DIR. Resumable — already-existing files are skipped.

Usage:
    uv run python generate_tts.py [--sentences FILE] [--ref WAV] [--out DIR] [--limit N]
"""

import argparse
import os
import time
from pathlib import Path

import httpx
import torch
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


def ensure_model_files(model_dir: Path) -> None:
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


def load_model(model_dir: Path, device: str) -> ChatterboxTTS:
    if all((model_dir / filename).exists() for filename in MODEL_FILES):
        print(f"loading model from local dir {model_dir}")
        return ChatterboxTTS.from_local(model_dir, device)

    ensure_model_files(model_dir)
    print(f"loading model from local dir {model_dir}")
    return ChatterboxTTS.from_local(model_dir, device)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sentences", default="pytorch_internals_sentences.txt")
    p.add_argument("--ref", default="voices/爱弥斯/104_滑翔.wav")
    p.add_argument("--out", default="tts_out")
    p.add_argument("--model-dir", default=".model-cache/chatterbox")
    p.add_argument("--limit", type=int, default=0, help="0 = all sentences")
    p.add_argument("--device", default="cpu")
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_dir = Path(args.model_dir)

    sentences = [
        s.strip()
        for s in Path(args.sentences).read_text().split("\n\n")
        if s.strip()
    ]
    if args.limit:
        sentences = sentences[: args.limit]
    print(
        f"sentences: {len(sentences)}  device: {args.device}  ref: {args.ref}  "
        f"model_dir: {model_dir}"
    )

    print("loading model …")
    t0 = time.time()
    model = load_model(model_dir, args.device)
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
