"""Inject Fish Audio prosody/emotion tags into plain sentences via LLM.

Fish Audio's S2-Pro model accepts free-form bracket tags like `[short pause]`,
`[emphasis]`, `[curious]` etc. inline with the text. Adding a few well-placed
tags makes long technical narration sound noticeably more expressive without
sounding theatrical.

We never modify the original `sentences.txt` — instead we write
`sentences_enhanced.txt` in the same one-paragraph-per-sentence format. The
fish backend auto-picks the enhanced file when present; chatterbox always
uses the plain `sentences.txt` because it doesn't understand the tags.

Cache: per-article `enhancements.json` maps original → enhanced so partial
runs are free to resume.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from blog_voice.llm.zenmux import DEEPSEEK_FALLBACK_PRO, chat_completion


# Curated subset of Fish Audio tags that suit calm-to-lively English tech
# narration. Full canonical lists live at:
#   https://docs.fish.audio/api-reference/emotion-reference
#   https://docs.fish.audio/developer-guide/best-practices/emotion-control
# S2-Pro additionally accepts arbitrary natural-language bracket descriptors.
TAG_REFERENCE = """
Fish Audio S2-Pro supports inline tags in [square brackets]. The model
interprets natural-language descriptors, so you may use the listed tags
verbatim OR coin descriptive variants like [thoughtful pause] or
[mildly emphatic].

Placement rules:
- Emotion tags MUST appear at the start of a sentence.
- Pause / breath / effect / emphasis tags can appear inline anywhere.
- Don't stack more than two tags on the same span.
- Don't tag every sentence — use sparingly to avoid theatrical reading.

PAUSE / BREATH (inline, anywhere):
  [break]            short pause (~250ms), like a comma
  [long-break]       longer pause (~700ms), like a thought break
  [breath]           audible inhale
  [sigh]             slow exhale

EMPHASIS (inline, immediately BEFORE the word/phrase to stress):
  [emphasis]         stresses the next word or short phrase
  [short pause]      a beat of silence for dramatic effect

EMOTION (start of sentence only; pick AT MOST one per sentence):
  [calm]             default for plain expository sentences — usually omit
  [confident]        assertive technical claim
  [curious]          rhetorical question or "what if…"
  [excited]          enthusiastic discovery / surprising result
  [satisfied]        wrapping-up / conclusion sentences
  [empathetic]       acknowledging the reader's difficulty
  [determined]       "let's tackle this"
  [surprised]        unexpected result, contradiction
  [chuckling]        light humor, parenthetical aside

TONE (start of sentence only; usually leave off):
  [soft tone]        intimate side note
  [in a hurry tone]  rapid recap
"""


def _system_prompt(voice_style: str) -> str:
    return (
        "You are a TTS prompt engineer. You receive one English sentence "
        f"from a technical blog being narrated in the voice of '{voice_style}'. "
        "Your job is to inject minimal Fish Audio bracket tags so the line "
        "is read with appropriate prosody — pauses at natural breath points, "
        "emphasis on the key technical term or contrast, and an emotion tag "
        "only when the sentence content clearly calls for one. "
        "Keep ALL of the original words and punctuation; insert tags between "
        "words. Do not rephrase. Do not translate. Prefer subtlety: most "
        "sentences should receive zero or one tag; reserve emotion tags for "
        "sentences whose meaning genuinely shifts the register. "
        "Return strict JSON only, with no markdown, using one top-level key "
        "'enhanced' whose value is the tagged sentence as a string.\n"
        + TAG_REFERENCE
    )


def _user_prompt(sentence: str) -> str:
    return f"Enhance this sentence:\n{json.dumps({'sentence': sentence}, ensure_ascii=False)}"


def _enhance_one(model: str, sentence: str) -> str:
    response = chat_completion(
        model=model,
        fallback_model=DEEPSEEK_FALLBACK_PRO,
        temperature=0.4,
        messages=[
            {"role": "system", "content": _system_prompt("a lively young female voice")},
            {"role": "user", "content": _user_prompt(sentence)},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    data = json.loads(content)
    enhanced = data.get("enhanced")
    if not isinstance(enhanced, str) or not enhanced.strip():
        raise ValueError(f"unexpected enhancement response: {content}")
    return enhanced.strip()


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def enhance_sentences(
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

    print(f"enhancing {len(pending)} sentences via {model} (concurrency={concurrency})")
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_enhance_one, model, s): s for s in pending
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                cache[source] = future.result()
            except Exception as exc:
                _save_cache(cache_path, cache)
                raise SystemExit(f"failed to enhance: {source}\n{exc}") from exc
            completed += 1
            print(f"enhanced {completed} / {len(pending)}")
            _save_cache(cache_path, cache)
    return cache


def write_enhanced_file(
    sentences: list[str],
    cache: dict[str, str],
    out_path: Path,
) -> None:
    out_path.write_text(
        "\n\n".join(cache[s] for s in sentences) + "\n",
        encoding="utf-8",
    )
    print(f"wrote enhanced sentences -> {out_path}")
