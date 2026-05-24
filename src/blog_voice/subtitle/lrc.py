"""Generate an LRC file from per-sentence wav durations + sentences.

If `--translate-zh` is set, calls an LLM via ZenMux to translate each English
sentence into Simplified Chinese and writes the translation as a second line
under each timestamped sentence. Translations are cached on disk so re-runs
are free.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import soundfile as sf

from blog_voice.llm.zenmux import chat_completion


def format_lrc_time(seconds: float) -> str:
    total_centis = round(seconds * 100)
    minutes, centis = divmod(total_centis, 6000)
    secs, centis = divmod(centis, 100)
    return f"{minutes:02d}:{secs:02d}.{centis:02d}"


def wav_duration_seconds(path: Path) -> float:
    info = sf.info(str(path))
    return info.frames / info.samplerate


def _system_prompt() -> str:
    return (
        "You are a professional subtitle translator for AI technology articles. "
        "Translate English sentences into natural Simplified Chinese in the context of AI, machine learning, "
        "deep learning, programming, and software engineering. Preserve content that should not be translated, "
        "including proper nouns, product names, model names, framework names, code, commands, APIs, file paths, "
        "identifiers, quoted code-like text, and technical terms that are normally used in English. "
        "Keep the meaning accurate and suitable for subtitles. Return strict JSON only, with no markdown, "
        "using a top-level key 'translation' whose value is a string."
    )


def _user_prompt(sentence: str) -> str:
    return f"Translate this sentence:\n{json.dumps({'sentence': sentence}, ensure_ascii=False)}"


def _translate_one(model: str, sentence: str) -> str:
    response = chat_completion(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(sentence)},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    data = json.loads(content)
    translation = data.get("translation")
    if not isinstance(translation, str):
        raise ValueError(f"unexpected translation response: {content}")
    return translation.strip()


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def translate_sentences(
    sentences: list[str],
    cache_path: Path,
    concurrency: int,
    model: str,
) -> dict[str, str]:
    cache = _load_cache(cache_path)
    pending = [s for s in sentences if s not in cache]
    if not pending:
        return cache
    if concurrency < 1:
        raise SystemExit("concurrency must be at least 1")

    print(f"translating {len(pending)} sentences via {model} (concurrency={concurrency})")
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_translate_one, model, sentence): sentence
            for sentence in pending
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                cache[source] = future.result()
            except Exception as exc:
                _save_cache(cache_path, cache)
                raise SystemExit(f"failed to translate: {source}\n{exc}") from exc
            completed += 1
            print(f"translated {completed} / {len(pending)}")
            _save_cache(cache_path, cache)
    return cache


def write_lrc(
    sentences: list[str],
    timestamps: list[float] | None,
    audio_files: list[Path] | None,
    out_path: Path,
    title: str,
    artist: str,
    album: str,
    include_metadata: bool,
    translations: dict[str, str] | None,
) -> None:
    if timestamps is None:
        if audio_files is None:
            raise SystemExit("either timestamps or audio_files is required")
        if len(sentences) != len(audio_files):
            raise SystemExit(
                f"sentence/audio mismatch: {len(sentences)} vs {len(audio_files)}"
            )
        elapsed = 0.0
        timestamps = []
        for f in audio_files:
            elapsed += wav_duration_seconds(f)
            timestamps.append(elapsed)

    if len(timestamps) != len(sentences):
        raise SystemExit(
            f"timestamp/sentence mismatch: {len(timestamps)} vs {len(sentences)}"
        )

    blocks: list[str] = []
    if include_metadata:
        blocks.append(
            "\n".join([
                f"[ti:{title}]",
                f"[ar:{artist}]",
                f"[al:{album}]",
                "[by:blog-voice]",
            ])
        )

    start = 0.0
    for sentence, end in zip(sentences, timestamps, strict=True):
        block_lines = [f"[{format_lrc_time(start)}]{sentence}"]
        if translations is not None:
            block_lines.append(translations.get(sentence, ""))
        blocks.append("\n".join(block_lines))
        start = end

    out_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    print(f"wrote {len(sentences)} lines to {out_path}; duration={timestamps[-1]:.2f}s")
