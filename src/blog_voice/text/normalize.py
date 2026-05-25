"""Rewrite code symbols and technical terms into TTS-readable spoken form.

Technical blogs are full of tokens a TTS engine mangles: dotted calls
(`torch.mm` → "torch mum"), underscore macros (`AT_DISPATCH_ALL_TYPES` read
as "...underscore..."), subscripts/template args (`tensor[1, 0]`, `<float, 3>`
silently dropped), file extensions (`.so` → "so"), operators (`::`, `<<`),
and odd casings (`PyTorch` → "PayTorch", `NumPy` → "num-pees", `dtype` →
"dipe"). These were the bulk of the verify failures.

This pass asks an LLM to rewrite ONLY those tokens into a plain spoken form,
leaving ordinary prose untouched — no prosody tags, no translation. Unlike
`enhance` (Fish tags, fish-only), normalization helps BOTH backends, so it
runs first in the chain and `enhance` builds on top of it.

We never touch the original `sentences.txt` (the LRC subtitle and the QA
model must still see the real symbols). Output goes to
`sentences_normalized.txt`; the per-article `normalizations.json` cache maps
original → normalized so partial runs resume for free.
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from blog_voice.llm.zenmux import DEEPSEEK_FALLBACK_PRO, chat_completion


# Worked examples steer the model toward "spoken form a narrator would say",
# not literal symbol names. Kept short; the model generalizes from these.
NORMALIZATION_GUIDE = """
Rewrite a single English sentence from a technical blog so a text-to-speech
engine reads it correctly out loud. Change ONLY code symbols and technical
tokens into the words a human narrator would actually speak; leave every
ordinary English word, the meaning, and the sentence order exactly as-is.

Rules:
- Do NOT add, remove, or reorder normal words. Do NOT rephrase prose.
- Do NOT translate. Do NOT add any bracket/prosody tags.
- Rewrite only symbols that are part of code identifiers/expressions; never
  read an underscore literally as the word "underscore".
- NEVER read ordinary punctuation aloud — parentheses, quotation marks,
  commas, periods are natural pauses, not words. (Do NOT produce things like
  "open parenthesis".)
- Leave acronyms and abbreviations as written (CUDA, GPU, CPU, API, XLA, …):
  the TTS pronounces them correctly, so do NOT spell them out or expand them.
- If the sentence has nothing to fix, return it verbatim.

Transformations (apply only when the token appears):
- Dotted calls / attributes: keep the dot spoken as "dot".
    torch.mm            -> torch dot M M
    torch.add           -> torch dot add
    x.accessor          -> x dot accessor
- Underscores in identifiers/macros are spoken as a space (a tiny pause),
  never the word "underscore":
    AT_DISPATCH_ALL_TYPES   -> AT DISPATCH ALL TYPES
    tanh_backward           -> tanh backward
- Subscripts / indices must be SPOKEN, not dropped:
    tensor[1, 0]        -> tensor at index one comma zero
    tensor[1, :]        -> tensor at index one comma all
- Template / angle-bracket args are spoken:
    accessor<float, 3>()    -> accessor of float comma three
    operator<<              -> the left-shift operator
- Scope / operators within identifiers:
    CPUFloatType::add   -> CPU float type's add
- File extensions and dotted names read the dot:
    libcaffe2.so        -> libcaffe2 dot S O
- Tricky casings get a phonetic spelling (so the engine says them right):
    PyTorch -> Pie-Torch    ;    PyObject -> Pie-Object    ;    NumPy -> Num-Pie
- Latin abbreviations: e.g. -> for example ; i.e. -> that is

Output strict JSON only, no markdown, one key 'normalized' whose value is the
rewritten sentence as a string.
"""


def _system_prompt() -> str:
    return (
        "You are a text-to-speech normalizer for technical English narration. "
        "You receive one sentence and return a spoken-form rewrite that a TTS "
        "engine will pronounce correctly, changing only code symbols and "
        "technical tokens.\n" + NORMALIZATION_GUIDE
    )


def _user_prompt(sentence: str) -> str:
    return f"Normalize this sentence:\n{json.dumps({'sentence': sentence}, ensure_ascii=False)}"


def _normalize_one(model: str, sentence: str) -> str:
    response = chat_completion(
        model=model,
        fallback_model=DEEPSEEK_FALLBACK_PRO,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(sentence)},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    data = json.loads(content)
    normalized = data.get("normalized")
    if not isinstance(normalized, str) or not normalized.strip():
        raise ValueError(f"unexpected normalization response: {content}")
    return normalized.strip()


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_cache(path: Path, cache: dict[str, str]) -> None:
    path.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_sentences(
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

    print(f"normalizing {len(pending)} sentences via {model} (concurrency={concurrency})")
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {executor.submit(_normalize_one, model, s): s for s in pending}
        for future in as_completed(futures):
            source = futures[future]
            try:
                cache[source] = future.result()
            except Exception as exc:
                _save_cache(cache_path, cache)
                raise SystemExit(f"failed to normalize: {source}\n{exc}") from exc
            completed += 1
            print(f"normalized {completed} / {len(pending)}")
            _save_cache(cache_path, cache)
    return cache


def write_normalized_file(
    sentences: list[str],
    cache: dict[str, str],
    out_path: Path,
) -> None:
    out_path.write_text(
        "\n\n".join(cache[s] for s in sentences) + "\n",
        encoding="utf-8",
    )
    print(f"wrote normalized sentences -> {out_path}")
