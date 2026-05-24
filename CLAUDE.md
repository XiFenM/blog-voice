# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Pipeline overview

Two pipelines, each driven by the unified `blog-voice` CLI:

```
voice pipeline:
  wiki.kurobbs.com  ─► voice scrape   ─► voices/<character>/*.wav + manifest.json
  voices/<…>.wav    ─► voice split    ─► voices_split/<character>/{normal,mecha}/

article pipeline (per <slug>):
  <raw txt>         ─► article add        ─► articles/<slug>/source.txt + meta.json
  source.txt        ─► article split-text ─► articles/<slug>/sentences.txt
  sentences.txt + ref-voice ─► article tts ─► articles/<slug>/audio/####.wav
  audio/*.wav       ─► article merge      ─► articles/<slug>/merged.wav
  sentences.txt + audio/*.wav ─► article lrc ─► articles/<slug>/subtitle.lrc
```

`article pipeline <slug>` chains split-text + tts + merge + lrc end-to-end. Each stage writes plain files; stages are independently rerunnable.

## Project layout

```
src/blog_voice/
├── cli.py              # argparse subcommand entry: blog-voice [voice|article] <action>
├── paths.py            # ArticlePaths(slug) + ArticleMeta JSON read/write
├── voices/             # scrape.py, classify.py (unsupervised), split.py (supervised)
├── text/sentences.py
├── tts/                # base.py protocol, chatterbox.py, fish_audio.py, runner.py
├── audio/merge.py
└── subtitle/lrc.py
```

The CLI is the only entry point — there are no top-level scripts. `pyproject.toml` registers `blog-voice = "blog_voice.cli:main"` as a console script and uses hatchling with `packages = ["src/blog_voice"]`.

## Commands

```bash
uv sync                                  # install + register `blog-voice` CLI

# voice library
uv run blog-voice voice scrape <wiki-url-or-id> [--out voices]
uv run blog-voice voice classify [--voice-dir voices/X] [--split]
uv run blog-voice voice split [--labels voice_labels.json]

# article pipeline
uv run blog-voice article add <slug> --source <file> --title T --artist A \
    --ref-voice voices_split/X/normal/foo.wav [--backend chatterbox|fish]
uv run blog-voice article split-text <slug>
uv run blog-voice article tts <slug> [--limit 5] [--device cuda|cpu] \
    [--backend chatterbox|fish] [--ref <wav>] [--fish-reference-id <id>]
uv run blog-voice article merge <slug> [--gap 0.3]
uv run blog-voice article lrc <slug> [--translate-zh] [--include-metadata]
uv run blog-voice article pipeline <slug> [...all of the above args...]
```

No tests, no linter, no build step beyond `uv sync`.

## Architecture notes (the non-obvious parts)

**`voices/scrape.py`** — reverse-engineered from wiki.kurobbs.com network traffic. The wiki page only injects audio URLs into the DOM on click, but the underlying API `POST /wiki/core/catalogue/item/getEntryDetail` returns the full payload (116 entries for 爱弥斯) with `playUrl` fields nested in arbitrary positions. The script walks the JSON recursively rather than relying on a fixed schema — kurobbs sometimes restructures `mediaList` / `content.modules`. **No auth needed**; only headers required are `wiki_type: 9` and `source: h5`. The transcript of each line lives alongside its playUrl in the `content` field — we capture it into `manifest.json` and also write a sibling `<wav>.transcript.txt` so the fish-audio backend can use it as the reference text without an ASR roundtrip. The scrape is idempotent: re-running over an existing directory skips wav downloads but re-writes transcripts/manifest, so you can backfill transcripts on a previously-scraped character by just running `voice scrape` again.

**`voices/classify.py` vs `voices/split.py`** — two ways to separate a character's voice modes (e.g. 爱弥斯's 常态 vs 机甲).
- `classify` is unsupervised: KMeans=2 over MFCC + spectral + HPSS features, then uses early-numbered files as the "normal anchor" majority vote to assign cluster→mode. Fine for first-pass exploration.
- `split` is supervised: reads `voice_labels.json` with hand-labeled `pure_normal` / `pure_mecha` lists, trains the reference KMeans on those, then scans mixed-mode files with a 0.5s sliding window and picks the split point that minimizes misclassifications (via prefix-sum on a median-smoothed label sequence). `manual_split_ratios` overrides the algorithm for specific files.

**`text/sentences.py`** — input is whatever's in `articles/<slug>/source.txt`. First-line detection: if it parses as a JSON-encoded string (the `playwright-cli --raw eval` output format), decode with `json.loads` before splitting; otherwise treat as plain text. Sentence splitter is regex + abbreviation whitelist (`Mr./e.g./No./Inc./…`); good for prose, doesn't handle code blocks.

**`tts/base.py` + backends** — Protocol with `synthesize(text, dest)`. Two implementations:
- `tts/chatterbox.py` — local model, weights downloaded once to `.model-cache/chatterbox/` (5 files via `httpx.stream`, atomic via `.part` swap, respects `HF_ENDPOINT`). The critical design choice: **always pass the same `--ref` clip to every sentence** to prevent voice drift on autoregressive models (per voice.md §2). Writes IEEE_FLOAT 32-bit via `torchaudio.save`.
- `tts/fish_audio.py` — Fish Audio API via `fish-audio-sdk` (`from fishaudio import FishAudio`). Two reference modes:
  1. `reference_id` — a voice clone model already saved in your fish.audio account. Fastest and most stable, recommended for long runs.
  2. Local wav file — uploaded inline as `ReferenceAudio(audio=bytes, text=transcript)`. The API requires a transcript for the reference clip; **`voice scrape` writes the kurobbs `content` field next to each wav as `<name>.transcript.txt`**, so for whole pure clips the transcript is free. If the transcript file is missing (e.g. a split fragment, or a non-kurobbs wav), the backend falls back to a one-time Fish ASR call and caches the result in the same `<name>.transcript.txt` path. Manual edits to that file are honored next run. Outputs PCM by default.

API keys go in `.env`: `FISH_API_KEY` (or legacy `FISH_AUDIO_API_KEY`), `DEEPSEEK_API_KEY`.

**`tts/runner.py`** — resumability via `dest.exists() and dest.stat().st_size > 0` — interrupted partial writes can corrupt; the chatterbox path is atomic through torchaudio's tmp, the fish path writes bytes directly so a half-written file can be deleted manually.

**`audio/merge.py`** — concatenates wavs using `soundfile` (not stdlib `wave`) because chatterbox produces float32 and stdlib `wave` only handles PCM. Output is forced to 16-bit PCM. Returns per-sentence end-timestamps so the LRC generator uses the same timing as the merged audio (which may include `--gap` silence between sentences).

**`subtitle/lrc.py`** — generates per-sentence LRC timestamps either from a passed-in `timestamps` list (used by `pipeline` so silence gaps are respected) or by summing wav durations (used by standalone `article lrc`). `--translate-zh` calls DeepSeek per sentence (20-way ThreadPoolExecutor, `json_object` response_format) and caches into `articles/<slug>/translations_zh.json`, written incrementally so a crash doesn't lose progress.

**`paths.py`** — `ArticlePaths(slug)` is the canonical accessor for an article's files; `ArticleMeta` is a dataclass stored as `articles/<slug>/meta.json` so default ref-voice / backend / artist / title can live alongside the data instead of being passed every time.

## Working with playwright-cli (for future debugging of wiki APIs)

- Connect to user's local Chrome via CDP: requires `--remote-debugging-port=9222` on Chrome + SSH `RemoteForward 9222 localhost:9222`. Verify with `curl http://localhost:9222/json/version`.
- `playwright-cli --raw eval "…"` returns a **JSON-encoded string** to stdout (with literal `\n`), not raw text. `text/sentences.py:_decode` handles both forms.
- To find hidden API endpoints: click the UI element that loads content, then `playwright-cli requests` to grep for the XHR, `request <n>` for headers, `response-body <n>` for the payload. Response bodies > a few KB are auto-persisted to a tool-results file path — `grep` that file rather than dumping into context.

## Reference voice picking

After running `voice scrape` and `voice split`, prefer clips from `voices_split/<character>/normal/` in the 10–16s range with no battle SFX:

```bash
python3 -c "import wave, glob, os
for f in sorted(glob.glob('voices_split/<character>/normal/*.wav')):
    with wave.open(f,'rb') as w: d = w.getnframes()/w.getframerate()
    if 10 <= d <= 16: print(os.path.basename(f), f'{d:.1f}s')
"
```

Then prefer `自我介绍 / 心声 / 闲趣 / 抱负` over `重击 / 突破 / 受击` (the latter contain shouts/SFX). The picked clip name is also in `voices/<character>/manifest.json`. For 爱弥斯 the current default ref is `voices_split/爱弥斯/normal/104_滑翔.wav`.

## See also

- [voice.md](voice.md) — TTS model selection rationale, reference-audio prep, technical-term preprocessing advice. Read this before changing TTS engines or trying to improve output quality.
- [README.md](README.md) — user-facing setup + run instructions for the unified CLI.
