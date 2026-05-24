"""Unified blog-voice CLI.

Subcommands grouped by domain:

  voice scrape <id-or-url>     download a character's voice clips from kurobbs wiki
  voice classify [...]         unsupervised KMeans classification of voice modes
  voice split [...]            supervised split using voice_labels.json

  article add <slug> --source FILE [--title T] [--artist A] [--backend ...]
                               create articles/<slug>/ and copy in source.txt
  article split-text <slug>    split source.txt into sentences.txt
  article tts <slug> [...]     run the TTS backend over every sentence
  article merge <slug>         concatenate per-sentence wavs into merged.wav
  article lrc <slug> [...]     emit subtitle.lrc, optionally bilingual
  article pipeline <slug> [...] run split-text + tts + merge + lrc end-to-end
"""

import argparse
import shutil
from pathlib import Path

from blog_voice.audio.merge import merge_wavs
from blog_voice.paths import ArticleMeta, article_paths
from blog_voice.subtitle.lrc import translate_sentences, write_lrc
from blog_voice.text.sentences import split_file
from blog_voice.tts.runner import read_sentences, run as run_tts


def _add_voice_subcommands(sub: argparse._SubParsersAction) -> None:
    p_scrape = sub.add_parser("scrape", help="download a character's voice clips from kurobbs wiki")
    p_scrape.add_argument("target", help="character id or wiki url")
    p_scrape.add_argument("--out", default="voices", help="output root directory")
    p_scrape.set_defaults(func=_cmd_voice_scrape)

    p_classify = sub.add_parser("classify", help="unsupervised KMeans classification of voice modes")
    p_classify.add_argument("--voice-dir", default="voices/爱弥斯")
    p_classify.add_argument("--out", default="voice_mode_report.tsv")
    p_classify.add_argument("--split-dir", default="voices_split/爱弥斯")
    p_classify.add_argument("--split", action="store_true", help="write segments by predicted mode")
    p_classify.add_argument("--sr", type=int, default=22050)
    p_classify.add_argument("--normal-anchor-max-index", type=int, default=31)
    p_classify.add_argument("--normal-threshold", type=float, default=0.8)
    p_classify.add_argument("--mecha-threshold", type=float, default=0.2)
    p_classify.set_defaults(func=_cmd_voice_classify)

    p_split = sub.add_parser("split", help="supervised split using voice_labels.json")
    p_split.add_argument("--labels", default="voice_labels.json")
    p_split.add_argument("--sr", type=int, default=22050)
    p_split.set_defaults(func=_cmd_voice_split)


def _add_article_subcommands(sub: argparse._SubParsersAction) -> None:
    p_add = sub.add_parser("add", help="create a new article from a local source file")
    p_add.add_argument("slug")
    p_add.add_argument("--source", required=True, help="path to a local raw text file")
    p_add.add_argument("--title", default="")
    p_add.add_argument("--artist", default="")
    p_add.add_argument("--album", default="blog-voice")
    p_add.add_argument("--ref-voice", default="", help="default reference wav for this article")
    p_add.add_argument("--backend", default="chatterbox", choices=["chatterbox", "fish"])
    p_add.add_argument("--fish-reference-id", default="")
    p_add.set_defaults(func=_cmd_article_add)

    p_split = sub.add_parser("split-text", help="split source.txt into sentences.txt")
    p_split.add_argument("slug")
    p_split.set_defaults(func=_cmd_article_split_text)

    p_tts = sub.add_parser("tts", help="run the TTS backend over every sentence")
    _add_tts_args(p_tts)
    p_tts.set_defaults(func=_cmd_article_tts)

    p_merge = sub.add_parser("merge", help="concatenate per-sentence wavs into merged.wav")
    p_merge.add_argument("slug")
    p_merge.add_argument("--gap", type=float, default=0.0, help="silence seconds between sentences")
    p_merge.set_defaults(func=_cmd_article_merge)

    p_lrc = sub.add_parser("lrc", help="emit subtitle.lrc (optionally bilingual)")
    p_lrc.add_argument("slug")
    p_lrc.add_argument("--translate-zh", action="store_true")
    p_lrc.add_argument("--include-metadata", action="store_true")
    p_lrc.add_argument("--translation-concurrency", type=int, default=20)
    p_lrc.add_argument("--deepseek-base-url", default="https://api.deepseek.com")
    p_lrc.add_argument("--deepseek-model", default="deepseek-v4-flash")
    p_lrc.set_defaults(func=_cmd_article_lrc)

    p_pipe = sub.add_parser(
        "pipeline",
        help="run split-text + tts + merge + lrc in one shot",
    )
    _add_tts_args(p_pipe)
    p_pipe.add_argument("--gap", type=float, default=0.0)
    p_pipe.add_argument("--translate-zh", action="store_true")
    p_pipe.add_argument("--include-metadata", action="store_true")
    p_pipe.add_argument("--translation-concurrency", type=int, default=20)
    p_pipe.add_argument("--deepseek-base-url", default="https://api.deepseek.com")
    p_pipe.add_argument("--deepseek-model", default="deepseek-v4-flash")
    p_pipe.set_defaults(func=_cmd_article_pipeline)


def _add_tts_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("slug")
    p.add_argument("--backend", default="", choices=["", "chatterbox", "fish"], help="default: meta.json")
    p.add_argument("--ref", default="", help="reference wav (default: meta.json)")
    p.add_argument("--limit", type=int, default=0, help="0 = all sentences")
    p.add_argument("--device", default="cpu", help="chatterbox only: cpu | cuda")
    p.add_argument("--model-dir", default=".model-cache/chatterbox", help="chatterbox only")
    p.add_argument("--fish-reference-id", default="", help="fish only: pre-saved voice model id")
    p.add_argument("--fish-model", default="s2-pro", help="fish only: s2-pro | s1")
    p.add_argument("--fish-ref-language", default="zh", help="fish only: language code for ASR of reference wav")
    p.add_argument("--fish-format", default="wav", choices=["wav", "mp3", "pcm", "opus"])
    p.add_argument("--fish-sample-rate", type=int, default=44100)


def _cmd_voice_scrape(args: argparse.Namespace) -> None:
    from blog_voice.voices.scrape import scrape

    scrape(args.target, Path(args.out))


def _cmd_voice_classify(args: argparse.Namespace) -> None:
    from blog_voice.voices.classify import classify

    classify(
        voice_dir=Path(args.voice_dir),
        report_path=Path(args.out),
        split_dir=Path(args.split_dir) if args.split else None,
        sr=args.sr,
        normal_anchor_max_index=args.normal_anchor_max_index,
        normal_threshold=args.normal_threshold,
        mecha_threshold=args.mecha_threshold,
    )


def _cmd_voice_split(args: argparse.Namespace) -> None:
    from blog_voice.voices.split import split_voices

    split_voices(Path(args.labels), args.sr)


def _cmd_article_add(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    paths.ensure()
    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"source not found: {src}")
    shutil.copyfile(src, paths.source)
    meta = ArticleMeta.load(paths.meta)
    if args.title:
        meta.title = args.title
    if args.artist:
        meta.artist = args.artist
    if args.album:
        meta.album = args.album
    if args.ref_voice:
        meta.ref_voice = args.ref_voice
    if args.backend:
        meta.backend = args.backend
    if args.fish_reference_id:
        meta.fish_reference_id = args.fish_reference_id
    if not meta.title:
        meta.title = args.slug
    meta.dump(paths.meta)
    print(f"article created: {paths.root}")
    print(f"  source: {paths.source}")
    print(f"  meta:   {paths.meta}")


def _cmd_article_split_text(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    if not paths.source.exists():
        raise SystemExit(f"missing source file: {paths.source}")
    split_file(paths.source, paths.sentences)


def _build_backend(args: argparse.Namespace, meta: ArticleMeta):
    backend_name = args.backend or meta.backend or "chatterbox"
    ref_path = Path(args.ref or meta.ref_voice) if (args.ref or meta.ref_voice) else None
    reference_id = args.fish_reference_id or meta.fish_reference_id

    if backend_name == "chatterbox":
        from blog_voice.tts.chatterbox import ChatterboxBackend

        if ref_path is None:
            raise SystemExit("chatterbox backend needs --ref or meta.ref_voice")
        return ChatterboxBackend(
            ref_voice=ref_path,
            device=args.device,
            model_dir=Path(args.model_dir),
        )
    if backend_name == "fish":
        from blog_voice.tts.fish_audio import FishAudioBackend

        return FishAudioBackend(
            ref_voice=ref_path,
            reference_id=reference_id,
            ref_language=args.fish_ref_language,
            model=args.fish_model,
            audio_format=args.fish_format,
            sample_rate=args.fish_sample_rate,
        )
    raise SystemExit(f"unknown backend: {backend_name}")


def _cmd_article_tts(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    if not paths.sentences.exists():
        raise SystemExit(f"missing sentences file: {paths.sentences} (run `article split-text` first)")
    meta = ArticleMeta.load(paths.meta)
    backend = _build_backend(args, meta)
    sentences = read_sentences(paths.sentences)
    suffix = ".wav"
    if backend.name == "fish":
        suffix = f".{args.fish_format}"
    run_tts(backend, sentences, paths.audio_dir, limit=args.limit, suffix=suffix)


def _audio_files(paths) -> list[Path]:
    files = sorted(paths.audio_dir.glob("*"))
    return [f for f in files if f.is_file() and f.suffix in {".wav"}]


def _cmd_article_merge(args: argparse.Namespace) -> list[float]:
    paths = article_paths(args.slug)
    files = _audio_files(paths)
    if not files:
        raise SystemExit(f"no .wav files under {paths.audio_dir} (run `article tts` first)")
    return merge_wavs(files, paths.merged, gap_seconds=args.gap)


def _cmd_article_lrc(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    meta = ArticleMeta.load(paths.meta)
    if not paths.sentences.exists():
        raise SystemExit(f"missing sentences file: {paths.sentences}")
    sentences = read_sentences(paths.sentences)
    audio_files = _audio_files(paths)
    if len(audio_files) > len(sentences):
        raise SystemExit(
            f"more audio files than sentences: {len(audio_files)} vs {len(sentences)}"
        )
    if len(audio_files) < len(sentences):
        print(
            f"note: only {len(audio_files)} of {len(sentences)} sentences have audio; "
            "writing LRC for the rendered prefix"
        )
        sentences = sentences[: len(audio_files)]

    translations = None
    if args.translate_zh:
        translations = translate_sentences(
            sentences=sentences,
            cache_path=paths.translation_cache,
            concurrency=args.translation_concurrency,
            base_url=args.deepseek_base_url,
            model=args.deepseek_model,
        )

    write_lrc(
        sentences=sentences,
        timestamps=None,
        audio_files=audio_files,
        out_path=paths.lrc,
        title=meta.title or args.slug,
        artist=meta.artist,
        album=meta.album,
        include_metadata=args.include_metadata,
        translations=translations,
    )


def _cmd_article_pipeline(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    meta = ArticleMeta.load(paths.meta)
    if not paths.source.exists():
        raise SystemExit(f"missing source: {paths.source}")
    split_file(paths.source, paths.sentences)

    backend = _build_backend(args, meta)
    sentences = read_sentences(paths.sentences)
    suffix = ".wav"
    if backend.name == "fish":
        suffix = f".{args.fish_format}"
    run_tts(backend, sentences, paths.audio_dir, limit=args.limit, suffix=suffix)

    files = _audio_files(paths)
    if not files:
        return
    timestamps = merge_wavs(files, paths.merged, gap_seconds=args.gap)

    translations = None
    if args.translate_zh:
        translations = translate_sentences(
            sentences=sentences[: len(files)],
            cache_path=paths.translation_cache,
            concurrency=args.translation_concurrency,
            base_url=args.deepseek_base_url,
            model=args.deepseek_model,
        )

    write_lrc(
        sentences=sentences[: len(files)],
        timestamps=timestamps,
        audio_files=None,
        out_path=paths.lrc,
        title=meta.title or args.slug,
        artist=meta.artist,
        album=meta.album,
        include_metadata=args.include_metadata,
        translations=translations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="blog-voice")
    top = parser.add_subparsers(dest="domain", required=True)

    voice = top.add_parser("voice", help="character voice library: scrape / classify / split")
    voice_sub = voice.add_subparsers(dest="action", required=True)
    _add_voice_subcommands(voice_sub)

    article = top.add_parser("article", help="article pipeline: add / split-text / tts / merge / lrc / pipeline")
    article_sub = article.add_subparsers(dest="action", required=True)
    _add_article_subcommands(article_sub)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
