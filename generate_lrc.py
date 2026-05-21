"""Generate an LRC file from per-sentence WAV files and sentence text."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def build_translation_system_prompt() -> str:
    return (
        "You are a professional subtitle translator for AI technology articles. "
        "Translate English sentences into natural Simplified Chinese in the context of AI, machine learning, "
        "deep learning, programming, and software engineering. Preserve content that should not be translated, "
        "including proper nouns, product names, model names, framework names, code, commands, APIs, file paths, "
        "identifiers, quoted code-like text, and technical terms that are normally used in English. "
        "Keep the meaning accurate and suitable for subtitles. Return strict JSON only, with no markdown, "
        "using a top-level key 'translation' whose value is a string."
    )


def build_translation_prompt(sentence: str) -> str:
    return f"Translate this sentence:\n{json.dumps({'sentence': sentence}, ensure_ascii=False)}"


def translate_one_sentence(client: OpenAI, model: str, sentence: str) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": build_translation_system_prompt(),
            },
            {
                "role": "user",
                "content": build_translation_prompt(sentence),
            },
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    data = json.loads(content)
    translation = data.get("translation")
    if not isinstance(translation, str):
        raise ValueError(f"unexpected translation response: {content}")
    return translation.strip()


def translate_missing_sentences(
    sentences: list[str],
    cache_path: Path,
    concurrency: int,
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
    if concurrency < 1:
        raise SystemExit("--translation-concurrency must be at least 1")

    client = OpenAI(api_key=api_key, base_url=base_url)
    print(f"translating {len(pending)} missing sentences with concurrency={concurrency}")
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(translate_one_sentence, client, model, sentence): sentence
            for sentence in pending
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                cache[source] = future.result()
            except Exception as exc:
                save_translation_cache(cache_path, cache)
                raise SystemExit(f"failed to translate sentence: {source}\n{exc}") from exc
            completed += 1
            print(f"translated {completed} / {len(pending)}")
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
    parser.add_argument("--translation-concurrency", type=int, default=20)
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
    blocks = []
    if args.include_metadata:
        blocks.append(
            "\n".join([
                f"[ti:{args.title}]",
                f"[ar:{args.artist}]",
                f"[al:{args.album}]",
                "[by:generate_lrc.py]",
            ])
        )

    translations = None
    if args.translate_zh:
        translations = translate_missing_sentences(
            sentences=sentences,
            cache_path=Path(args.translation_cache),
            concurrency=args.translation_concurrency,
            base_url=args.deepseek_base_url,
            model=args.deepseek_model,
        )

    for sentence, audio_file in zip(sentences, audio_files, strict=True):
        block_lines = [f"[{format_lrc_time(elapsed)}]{sentence}"]
        if translations is not None:
            block_lines.append(translations[sentence])
        blocks.append("\n".join(block_lines))
        elapsed += wav_duration_seconds(audio_file)

    Path(args.out).write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    print(f"wrote {len(sentences)} lines to {args.out}; duration={elapsed:.2f}s")


if __name__ == "__main__":
    main()
