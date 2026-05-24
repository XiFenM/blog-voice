# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Why this project exists (read first)

The user is a software engineer (AI Infra direction) running a **22-week (5-month) English listening + speaking improvement plan**. This repo exists to produce custom AI Infra audio teaching material for that plan: every 2–3 weeks the user adds one new AI Infra article and runs the full pipeline → `merged.wav` + `subtitle.lrc` becomes their listening / shadowing material. Expected cadence: **8–10 new articles over the 22 weeks**.

The full plan, including baseline test SOPs, the 5-phase week-by-week schedule, four practice SOPs (美剧 / 口语课 / AI Infra listening / recording review), and the Anki chunk-card template, lives at **[English-learn/English-learn.md](English-learn/English-learn.md)**. Reference materials (`reference-advice*.md`, `AI-infra-podcast.md`) sit alongside it.

What this means for working in this repo:

- When the user asks for a new article, **prefer AI Infra topics** matching the plan (vLLM blog, KV cache, GPU scheduling, inference serving, etc.) over arbitrary tech writing.
- When suggesting cadence or batch size for new articles, anchor on the plan: **one new article per 2–3 weeks**, not "let's add ten at once."
- `English-learn/baseline/` (Week 0 + Week 22 test recordings) and `English-learn/weekly/` (weekly logs) are **personal data** — same gitignore treatment as `voices/` and `articles/*/audio/`. The plan markdown itself and reference advice files are fine to commit (general study material, no copyright issue).
- Voice-related decisions (which ref clip, which 美剧 to use, etc.) have already been made and recorded in the plan — defer to the plan rather than re-recommending from scratch.

## Pipeline overview

Two pipelines, each driven by the unified `blog-voice` CLI:

```
voice pipeline:
  wiki.kurobbs.com  ─► voice scrape   ─► voices/<character>/*.wav + manifest.json
  voices/<…>.wav    ─► voice split    ─► voices_split/<character>/{normal,mecha}/

article pipeline (per <slug>):
  <raw txt>         ─► article add        ─► articles/<slug>/source.txt + meta.json
  source.txt        ─► article split-text ─► articles/<slug>/sentences.txt
  sentences.txt    ─► article enhance    ─► articles/<slug>/sentences_enhanced.txt  (optional, fish only)
  sentences[_enhanced].txt + ref-voice ─► article tts ─► articles/<slug>/audio/####.wav
  audio/*.wav       ─► article merge      ─► articles/<slug>/merged.wav
  sentences.txt + audio/*.wav ─► article lrc ─► articles/<slug>/subtitle.lrc
  sentences.txt + audio/*.wav ─► article verify ─► articles/<slug>/verify_report.json  (optional)
```

`article pipeline <slug>` chains split-text + tts + merge + lrc end-to-end. `--enhance` and `--verify` opt in to the optional stages. Each stage writes plain files; stages are independently rerunnable.

## Project layout

```
src/blog_voice/
├── cli.py              # argparse subcommand entry: blog-voice [voice|article] <action>
├── paths.py            # ArticlePaths(slug) + ArticleMeta JSON read/write
├── llm/zenmux.py       # shared OpenAI-compatible client (base_url=https://zenmux.ai/api/v1)
├── voices/             # scrape.py, classify.py (unsupervised), split.py (supervised)
├── text/               # sentences.py (split), enhance.py (LLM-injected Fish tags)
├── tts/                # base.py protocol, chatterbox.py, fish_audio.py, runner.py
├── audio/merge.py
├── subtitle/lrc.py     # LRC + optional bilingual translation via ZenMux
└── verify/audio.py     # multimodal-LLM audio QA via ZenMux
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
uv run blog-voice article enhance <slug> [--model deepseek/deepseek-v4-pro]    # fish only
uv run blog-voice article tts <slug> [--limit 5] [--device cuda|cpu] \
    [--backend chatterbox|fish] [--ref <wav>] [--fish-reference-id <id>] \
    [--use-enhanced auto|yes|no]
uv run blog-voice article merge <slug> [--gap 0.3]
uv run blog-voice article lrc <slug> [--translate-zh] [--translation-model deepseek/deepseek-v4-flash]
uv run blog-voice article verify <slug> [--model google/gemini-3.5-flash] [--language English]
uv run blog-voice article pipeline <slug> [...all of the above args + --enhance --verify]
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

API keys go in `.env`: `FISH_API_KEY` (or legacy `FISH_AUDIO_API_KEY`) for TTS; `ZENMUX_API_KEY` covers all LLM call sites (translation, sentence enhancement, audio verification).

Per-character Fish Audio voice model IDs (uploaded via fish.audio's voice cloning UI/API) live in `voice_labels.json` under `reference_ids` — each entry has `id`, `source` wav path, `role` (`preferred` vs `backup`), and a `note`. Per-article default goes in `articles/<slug>/meta.json:fish_reference_id`.

**`tts/runner.py`** — resumability via `dest.exists() and dest.stat().st_size > 0` — interrupted partial writes can corrupt; the chatterbox path is atomic through torchaudio's tmp, the fish path writes bytes directly so a half-written file can be deleted manually.

**`audio/merge.py`** — concatenates wavs using `soundfile` (not stdlib `wave`) because chatterbox produces float32 and stdlib `wave` only handles PCM. Output is forced to 16-bit PCM. Returns per-sentence end-timestamps so the LRC generator uses the same timing as the merged audio (which may include `--gap` silence between sentences).

**`llm/zenmux.py`** — single OpenAI-compatible client factory pointing at `https://zenmux.ai/api/v1`, reads `ZENMUX_API_KEY` from env. Shared by translation, enhancement, and verification so one provider key fronts all three (model id format is `provider/model-name`). Default model constants live here: `DEFAULT_TRANSLATION_MODEL=deepseek/deepseek-v4-flash`, `DEFAULT_ENHANCEMENT_MODEL=deepseek/deepseek-v4-pro`, `DEFAULT_VERIFY_MODEL=google/gemini-3.5-flash`. They're imported by `cli.py` for argparse defaults so a single edit in zenmux.py propagates to every command.

`chat_completion(model, **kwargs)` is the single function call sites should use instead of `client.chat.completions.create()` directly: it tries ZenMux first, and on **any** exception falls back to the DeepSeek native API (`https://api.deepseek.com`, key from `DEEPSEEK_API_KEY`) — but only for `deepseek/*` models, mapped to native names (`deepseek-reasoner` if the slug contains "reasoner"/"r1", else `deepseek-chat`). Non-DeepSeek models re-raise. The fallback client is lazily created and module-cached. Set `DEEPSEEK_API_KEY` in `.env` to enable; without it the fallback is a no-op and the ZenMux error propagates.

**`subtitle/lrc.py`** — generates per-sentence LRC timestamps either from a passed-in `timestamps` list (used by `pipeline` so silence gaps are respected) or by summing wav durations (used by standalone `article lrc`). `--translate-zh` calls the chosen ZenMux model per sentence (configurable concurrency, `json_object` response_format) and caches into `articles/<slug>/translations_zh.json`, written incrementally so a crash doesn't lose progress. The cache key is the source English sentence, so switching translation model produces a new cache file only if you delete the old one; existing cached translations are reused.

**`text/enhance.py`** — LLM injects Fish Audio S2-Pro bracket tags into each sentence. The system prompt embeds a curated tag inventory (pause/breath/emphasis + a small emotion subset suited to tech narration) and placement rules (emotion at sentence start only, ≤2 tags per span, sparing use). Writes `articles/<slug>/sentences_enhanced.txt` plus a `enhancements.json` cache. **Only useful for the fish backend** — chatterbox doesn't recognize the tags and would read them as literal text. `cli._pick_sentences_path` auto-routes: chatterbox → `sentences.txt`, fish → `sentences_enhanced.txt` if it exists, falling back to plain. `article lrc` and `article verify` always use the plain `sentences.txt` because the tags are TTS-internal artifacts that shouldn't appear in the subtitle or be sent to the QA model.

**`verify/audio.py`** — base64-encodes each wav and sends it with the original sentence to a multimodal ZenMux model (default `google/gemini-3.5-flash`) using the OpenAI-style `input_audio` content part. Response is a strict JSON verdict (`ok`, `matches_text`, `naturalness 1-5`, `transcription`, `issues[]`). The per-clip result is written incrementally into `articles/<slug>/verify_report.json` keyed by index, so the run is resumable; the report's top-level `passed/total/failed_indexes` summary is recomputed at the end of each run. Concurrency is intentionally lower than translation (default 5 vs 20) because audio payloads can be much larger.

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

Then prefer `自我介绍 / 心声 / 闲趣 / 抱负` over `重击 / 突破 / 受击` (the latter contain shouts/SFX). The picked clip name is also in `voices/<character>/manifest.json`. For 爱弥斯 the current default ref is **`voices_split/爱弥斯/refs/lively_20s.wav`** — a 20.7s 48kHz/24-bit merge of `022_自我介绍` (10.6s) + 250ms silence + `009_讨厌的食物` (9.8s), chosen for the user's "活泼开朗" preference (declarative intro + literal chuckle, wide prosody range).

For Fish Audio TTS, the user has pre-uploaded three voice models and stored the `reference_id`s in `voice_labels.json:reference_ids`: `lively_20s` (preferred, default in `articles/pytorch-internals/meta.json:fish_reference_id`), plus `016_关于椿` and `022_自我介绍` as backups for A/B testing.

## See also

- [English-learn/English-learn.md](English-learn/English-learn.md) — **the 22-week English learning plan this project serves**. Read first when the user mentions article cadence, topic selection, or anything about listening / shadowing.
- [English-learn/AI-infra-podcast.md](English-learn/AI-infra-podcast.md) — curated AI Infra podcast list mapped to listening phases 3–5 of the plan.
- [voice.md](voice.md) — TTS model selection rationale, reference-audio prep, technical-term preprocessing advice. Read this before changing TTS engines or trying to improve output quality.
- [README.md](README.md) — user-facing setup + run instructions for the unified CLI, including the 5-minute quickstart.
- [voice_labels.json](voice_labels.json) — per-character voice mode labels + Fish Audio `reference_id` registry.

## What to do when ZenMux hits 402

ZenMux's free-tier rolling-window quota is tight enough that a full 250-sentence run (enhance 250 + translate 250 = ~500 chat completions) routinely exhausts it. Symptoms: `APIStatusError: Error code: 402 - {'error': {'code': '402', 'type': 'quote_exceeded', ...}}` mid-run, and `translate_sentences` / `enhance_sentences` raises `SystemExit` after the first failure.

Recovery, in order of preference:
1. **Configure DeepSeek fallback once**: set `DEEPSEEK_API_KEY` in `.env`. After that, any `deepseek/*` model that fails on ZenMux is silently retried against `https://api.deepseek.com` with the mapped native model id (`deepseek-chat` / `deepseek-reasoner`). Costs are usually lower than ZenMux. Run the same `article lrc` / `article enhance` command and it picks up where the cache left off — already-translated sentences are not re-billed.
2. **Switch model for the failing call**: e.g. `article lrc --translation-model openai/gpt-4o-mini` to dodge `deepseek/*` quota specifically (only useful if your OpenAI bucket on ZenMux is independent).
3. **Wait for the rolling window** to refresh. Translation/enhancement caches survive across runs, so resuming costs nothing for completed sentences.
4. **Audio verify (Gemini) has no fallback** — DeepSeek doesn't host multimodal audio models. If verify dies on 402, the only options are wait or upgrade ZenMux. Run `article verify --limit N` to do it in chunks; the report is keyed by sentence index so partial runs are safe.
