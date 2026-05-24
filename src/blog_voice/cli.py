"""Unified blog-voice CLI.

Subcommands grouped by domain:

  voice scrape <id-or-url>     download a character's voice clips from kurobbs wiki
  voice classify [...]         unsupervised KMeans classification of voice modes
  voice split [...]            supervised split using voice_labels.json

  article add <slug> --source FILE [--title T] [--artist A] [--backend ...]
                               create articles/<slug>/ and copy in source.txt
  article split-text <slug>    split source.txt into sentences.txt
  article enhance <slug>       inject Fish prosody/emotion tags into sentences (fish backend only)
  article tts <slug> [...]     run the TTS backend over every sentence
  article merge <slug>         concatenate per-sentence wavs into merged.wav
  article lrc <slug> [...]     emit subtitle.lrc, optionally bilingual
  article verify <slug> [...]  use a multimodal LLM to QA each generated wav
  article pipeline <slug> [...] run split-text + (enhance) + tts + merge + lrc + (verify) end-to-end
"""

import argparse
import shutil
from pathlib import Path

from blog_voice.audio.merge import merge_wavs
from blog_voice.llm.zenmux import (
    DEFAULT_ENHANCEMENT_MODEL,
    DEFAULT_TRANSLATION_MODEL,
    DEFAULT_VERIFY_MODEL,
)
from blog_voice.paths import ArticleMeta, article_paths
from blog_voice.subtitle.lrc import translate_sentences, write_lrc
from blog_voice.text.enhance import enhance_sentences, write_enhanced_file
from blog_voice.text.sentences import split_file
from blog_voice.tts.runner import read_sentences, run as run_tts
from blog_voice.verify.audio import verify_article


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

    p_enhance = sub.add_parser(
        "enhance",
        help="inject Fish Audio prosody/emotion tags into each sentence via LLM (fish backend only)",
    )
    _add_enhance_args(p_enhance)
    p_enhance.set_defaults(func=_cmd_article_enhance)

    p_tts = sub.add_parser("tts", help="run the TTS backend over every sentence")
    _add_tts_args(p_tts)
    p_tts.set_defaults(func=_cmd_article_tts)

    p_merge = sub.add_parser("merge", help="concatenate per-sentence wavs into merged.wav")
    p_merge.add_argument("slug")
    p_merge.add_argument("--gap", type=float, default=0.0, help="silence seconds between sentences")
    p_merge.set_defaults(func=_cmd_article_merge)

    p_lrc = sub.add_parser("lrc", help="emit subtitle.lrc (optionally bilingual)")
    _add_lrc_args(p_lrc)
    p_lrc.set_defaults(func=_cmd_article_lrc)

    p_verify = sub.add_parser(
        "verify",
        help="audio QA via multimodal LLM (writes verify_report.json)",
    )
    _add_verify_args(p_verify)
    p_verify.set_defaults(func=_cmd_article_verify)

    p_pipe = sub.add_parser(
        "pipeline",
        help="run split-text + (enhance) + tts + merge + lrc + (verify) in one shot",
    )
    _add_tts_args(p_pipe)
    p_pipe.add_argument("--gap", type=float, default=0.0)
    _add_lrc_extra_args(p_pipe)
    p_pipe.add_argument("--enhance", action="store_true", help="run sentence-tag enhancement before fish TTS")
    p_pipe.add_argument("--enhance-model", default=DEFAULT_ENHANCEMENT_MODEL)
    p_pipe.add_argument("--enhance-concurrency", type=int, default=10)
    p_pipe.add_argument("--verify", action="store_true", help="run audio QA after merging")
    p_pipe.add_argument("--verify-model", default=DEFAULT_VERIFY_MODEL)
    p_pipe.add_argument("--verify-concurrency", type=int, default=5)
    p_pipe.add_argument("--verify-language", default="English")
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
    p.add_argument(
        "--use-enhanced",
        default="auto",
        choices=["auto", "yes", "no"],
        help="fish: read sentences_enhanced.txt if present (auto=yes when file exists)",
    )


def _add_enhance_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("slug")
    p.add_argument("--model", default=DEFAULT_ENHANCEMENT_MODEL, help="ZenMux model id")
    p.add_argument("--concurrency", type=int, default=10)


def _add_lrc_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("slug")
    _add_lrc_extra_args(p)


def _add_lrc_extra_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--translate-zh", action="store_true")
    p.add_argument("--include-metadata", action="store_true")
    p.add_argument("--translation-concurrency", type=int, default=20)
    p.add_argument("--translation-model", default=DEFAULT_TRANSLATION_MODEL, help="ZenMux model id")


def _add_verify_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("slug")
    p.add_argument("--model", default=DEFAULT_VERIFY_MODEL, help="multimodal ZenMux model id (must accept audio)")
    p.add_argument("--concurrency", type=int, default=5)
    p.add_argument("--limit", type=int, default=0, help="0 = all sentences")
    p.add_argument("--language", default="English", help="language the audio should be in")


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


def _cmd_article_enhance(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    if not paths.sentences.exists():
        raise SystemExit(f"missing sentences file: {paths.sentences} (run `article split-text` first)")
    sentences = read_sentences(paths.sentences)
    cache = enhance_sentences(
        sentences=sentences,
        cache_path=paths.enhancement_cache,
        concurrency=args.concurrency,
        model=args.model,
    )
    write_enhanced_file(sentences, cache, paths.sentences_enhanced)


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


def _pick_sentences_path(args: argparse.Namespace, paths) -> Path:
    """Decide whether to feed the enhanced or the plain sentences file to TTS.

    Only the fish backend understands the tags, so chatterbox always reads
    the plain file. For fish, `--use-enhanced auto` (default) reads the
    enhanced file when it's present and falls back to plain otherwise.
    """
    backend = args.backend or "chatterbox"
    use = args.use_enhanced
    if backend != "fish" or use == "no":
        return paths.sentences
    if use == "yes":
        if not paths.sentences_enhanced.exists():
            raise SystemExit(
                f"--use-enhanced=yes but {paths.sentences_enhanced} is missing "
                "(run `article enhance` first)"
            )
        return paths.sentences_enhanced
    # auto: prefer enhanced when present
    return paths.sentences_enhanced if paths.sentences_enhanced.exists() else paths.sentences


def _cmd_article_tts(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    meta = ArticleMeta.load(paths.meta)
    backend = _build_backend(args, meta)

    # _pick_sentences_path needs the resolved backend name, not the empty
    # default; mirror it onto args so the helper can read it uniformly.
    args.backend = backend.name
    sentences_path = _pick_sentences_path(args, paths)
    if not sentences_path.exists():
        raise SystemExit(f"missing sentences file: {sentences_path}")
    if sentences_path == paths.sentences_enhanced:
        print(f"using enhanced sentences: {sentences_path.name}")

    sentences = read_sentences(sentences_path)
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
            model=args.translation_model,
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


def _cmd_article_verify(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    if not paths.sentences.exists():
        raise SystemExit(f"missing sentences file: {paths.sentences}")
    sentences = read_sentences(paths.sentences)
    audio_files = _audio_files(paths)
    if not audio_files:
        raise SystemExit(f"no .wav files under {paths.audio_dir}")
    sentences = sentences[: len(audio_files)]
    verify_article(
        sentences=sentences,
        audio_files=audio_files,
        report_path=paths.verify_report,
        model=args.model,
        concurrency=args.concurrency,
        target_language=args.language,
        limit=args.limit,
    )


def _cmd_article_pipeline(args: argparse.Namespace) -> None:
    paths = article_paths(args.slug)
    meta = ArticleMeta.load(paths.meta)
    if not paths.source.exists():
        raise SystemExit(f"missing source: {paths.source}")
    split_file(paths.source, paths.sentences)

    backend = _build_backend(args, meta)
    args.backend = backend.name

    if args.enhance:
        if backend.name != "fish":
            print(f"note: --enhance has no effect on backend={backend.name}; skipping")
        else:
            base_sentences = read_sentences(paths.sentences)
            cache = enhance_sentences(
                sentences=base_sentences,
                cache_path=paths.enhancement_cache,
                concurrency=args.enhance_concurrency,
                model=args.enhance_model,
            )
            write_enhanced_file(base_sentences, cache, paths.sentences_enhanced)

    sentences_path = _pick_sentences_path(args, paths)
    if sentences_path == paths.sentences_enhanced:
        print(f"using enhanced sentences: {sentences_path.name}")
    sentences = read_sentences(sentences_path)
    # Original (untagged) sentences for LRC and verification.
    plain_sentences = read_sentences(paths.sentences)

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
            sentences=plain_sentences[: len(files)],
            cache_path=paths.translation_cache,
            concurrency=args.translation_concurrency,
            model=args.translation_model,
        )

    write_lrc(
        sentences=plain_sentences[: len(files)],
        timestamps=timestamps,
        audio_files=None,
        out_path=paths.lrc,
        title=meta.title or args.slug,
        artist=meta.artist,
        album=meta.album,
        include_metadata=args.include_metadata,
        translations=translations,
    )

    if args.verify:
        verify_article(
            sentences=plain_sentences[: len(files)],
            audio_files=files,
            report_path=paths.verify_report,
            model=args.verify_model,
            concurrency=args.verify_concurrency,
            target_language=args.verify_language,
            limit=0,
        )


def main() -> None:
    parser = argparse.ArgumentParser(prog="blog-voice")
    top = parser.add_subparsers(dest="domain", required=True)

    voice = top.add_parser("voice", help="character voice library: scrape / classify / split")
    voice_sub = voice.add_subparsers(dest="action", required=True)
    _add_voice_subcommands(voice_sub)

    article = top.add_parser(
        "article",
        help="article pipeline: add / split-text / enhance / tts / merge / lrc / verify / pipeline",
    )
    article_sub = article.add_subparsers(dest="action", required=True)
    _add_article_subcommands(article_sub)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
