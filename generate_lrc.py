"""Generate an LRC file from per-sentence WAV files and sentence text."""

import argparse
import json
import os
import wave
from pathlib import Path

from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime when translation is requested.
    OpenAI = None


def format_lrc_time(seconds: float) -> str:
    total_centis = round(seconds * 100)
    minutes, centis = divmod(total_centis, 6000)
    secs, centis = divmod(centis, 100)
    return f"{minutes:02d}:{secs:02d}.{centis:02d}"


def wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
    return frames / sample_rate


def load_translation_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_translation_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_translation_prompt(sentences: list[str]) -> str:
    payload = {"sentences": sentences}
    return (
        "Translate the following English technical-blog sentences into natural Simplified Chinese. "
        "Keep the meaning accurate, preserve technical terms such as PyTorch, and return only JSON "
        "with a top-level key 'translations' whose value is an array of strings in the same order.\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def translate_missing_sentences(
    sentences: list[str],
    cache_path: Path,
    batch_size: int,
    base_url: str,
    model: str,
) -> dict[str, str]:
    load_dotenv()
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is missing. Put it in .env before using --translate-zh.")
    if OpenAI is None:
        raise SystemExit("openai package is not installed. Run `uv sync` before using --translate-zh.")

    cache = load_translation_cache(cache_path)
    pending = [sentence for sentence in sentences if sentence not in cache]
    if not pending:
        return cache

    client = OpenAI(api_key=api_key, base_url=base_url)
    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        print(f"translating {start + 1}-{start + len(batch)} / {len(pending)}")
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional subtitle translator. Return strict JSON only, with no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": build_translation_prompt(batch),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        data = json.loads(content)
        translations = data.get("translations")
        if not isinstance(translations, list) or len(translations) != len(batch):
            raise SystemExit(f"unexpected translation response: {content}")
        for source, translated in zip(batch, translations, strict=True):
            cache[source] = translated.strip()
        save_translation_cache(cache_path, cache)

    return cache


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sentences", default="pytorch_internals_sentences.txt")
    parser.add_argument("--audio-dir", default="tts_out")
    parser.add_argument("--title", default="PyTorch internals")
    parser.add_argument("--artist", default="爱弥斯")
    parser.add_argument("--album", default="blog-voice")
    parser.add_argument("--out", default="pytorch_internals_full.lrc")
    parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="include ti/ar/al/by header lines in the LRC output",
    )
    parser.add_argument(
        "--translate-zh",
        action="store_true",
        help="add one translated Simplified Chinese line under each original line",
    )
    parser.add_argument("--translation-cache", default="translations_zh.json")
    parser.add_argument("--translation-batch-size", type=int, default=20)
    parser.add_argument("--deepseek-base-url", default="https://api.deepseek.com")
    parser.add_argument("--deepseek-model", default="deepseek-v4-flash")
    args = parser.parse_args()

    sentences = [
        sentence.strip()
        for sentence in Path(args.sentences).read_text(encoding="utf-8").split("\n\n")
        if sentence.strip()
    ]
    audio_files = sorted(Path(args.audio_dir).glob("*.wav"))

    if len(sentences) != len(audio_files):
        raise SystemExit(
            f"sentence/audio count mismatch: {len(sentences)} sentences vs {len(audio_files)} wav files"
        )

    elapsed = 0.0
    lines = []
    if args.include_metadata:
        lines.extend([
            f"[ti:{args.title}]",
            f"[ar:{args.artist}]",
            f"[al:{args.album}]",
            "[by:generate_lrc.py]",
        ])

    translations = None
    if args.translate_zh:
        translations = translate_missing_sentences(
            sentences=sentences,
            cache_path=Path(args.translation_cache),
            batch_size=args.translation_batch_size,
            base_url=args.deepseek_base_url,
            model=args.deepseek_model,
        )

    for sentence, audio_file in zip(sentences, audio_files, strict=True):
        lines.append(f"[{format_lrc_time(elapsed)}]{sentence}")
        if translations is not None:
            lines.append(translations[sentence])
        elapsed += wav_duration_seconds(audio_file)

    Path(args.out).write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(sentences)} lines to {args.out}; duration={elapsed:.2f}s")


if __name__ == "__main__":
    main()
