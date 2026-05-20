# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Pipeline overview

Three independent scripts chained by files on disk:

```
wiki.kurobbs.com  ─► scrape_voices.py  ─► voices/<角色>/*.wav + manifest.json
<blog URL>        ─► (playwright eval) ─► pytorch_internals_raw.txt
                  ─► split_sentences.py ► pytorch_internals_sentences.txt
voices/<…>.wav (ref) + sentences.txt ─► generate_tts.py ─► tts_out/####.wav
```

Each stage writes plain files; nothing is in-memory between stages, so any step can be re-run in isolation.

## Commands

```bash
uv sync                                            # install deps

# stage 1: scrape character voices (one character at a time)
uv run python scrape_voices.py <wiki-url-or-id> [--out voices]

# stage 2: blog text fetch + sentence split
playwright-cli --raw eval "() => document.querySelector('article.post').innerText" > pytorch_internals_raw.txt
uv run python split_sentences.py                   # reads RAW, writes sentences.txt

# stage 3: TTS (resumable — already-existing tts_out/####.wav are skipped)
uv run python generate_tts.py --limit 5            # smoke test
uv run python generate_tts.py --device cuda        # full run on GPU
```

No tests, no linter, no build step — uv handles everything.

## Architecture notes (the non-obvious parts)

**`scrape_voices.py`** — found via reverse-engineering wiki.kurobbs.com network traffic. The wiki page itself only injects audio URLs into the DOM on click, but the underlying API `POST /wiki/core/catalogue/item/getEntryDetail` returns the full payload (116 entries for 爱弥斯) with `playUrl` fields nested in arbitrary positions. The script walks the JSON recursively rather than relying on a fixed schema — kurobbs sometimes restructures `mediaList` / `content.modules`. **No auth needed**; only headers required are `wiki_type: 9` and `source: h5`.

**`split_sentences.py`** — input file's first line is a JSON-encoded string (output of `playwright-cli --raw eval`), so it does `json.loads(first_line)` before splitting. Sentence splitter is regex + abbreviation whitelist (`Mr./e.g./No./Inc./…`); good enough for prose but does not handle code blocks specially.

**`generate_tts.py`** — wraps Chatterbox-TTS. The critical design choice: **always pass the same `--ref` clip to every sentence** to prevent voice drift on autoregressive models (per voice.md §2). Resumability is `dest.exists() and dest.stat().st_size > 0` — interrupted partial writes won't corrupt the run because `torchaudio.save` writes atomically through a tmp file. CPU mode is ~10–20× slower than realtime on this 4-core VM; GPU brings it to ~0.3–0.5× realtime.

## Working with playwright-cli (for future debugging of wiki APIs)

- Connect to user's local Chrome via CDP: requires `--remote-debugging-port=9222` on Chrome + SSH `RemoteForward 9222 localhost:9222`. Verify with `curl http://localhost:9222/json/version`.
- `playwright-cli --raw eval "…"` returns a **JSON-encoded string** to stdout (with literal `\n`), not raw text. Decode before processing.
- To find hidden API endpoints: click the UI element that loads content, then `playwright-cli requests` to grep for the XHR, `request <n>` for headers, `response-body <n>` for the payload. Response bodies > a few KB are auto-persisted to a tool-results file path — `grep` that file rather than dumping into context.

## Reference voice picking

For a new character, after running stage 1, pick reference clips in the 10–16s range with no battle SFX:

```bash
python3 -c "import wave, glob, os
for f in sorted(glob.glob('voices/<角色>/*.wav')):
    with wave.open(f,'rb') as w: d = w.getnframes()/w.getframerate()
    if 10 <= d <= 16: print(os.path.basename(f), f'{d:.1f}s')
"
```

Then prefer `自我介绍 / 心声 / 闲趣 / 抱负` over `重击 / 突破 / 受击` (the latter contain shouts/SFX). The picked clip name is in [voices/爱弥斯/manifest.json](voices/爱弥斯/manifest.json).

## See also

- [voice.md](voice.md) — TTS model selection rationale, reference-audio prep, technical-term preprocessing advice. Read this before changing TTS engines or trying to improve output quality.
- [README.md](README.md) — user-facing setup + run instructions, including the SSH/Chrome debug-port handshake.
