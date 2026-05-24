"""Split decoded blog text into sentences, separated by blank lines.

The raw text is whatever `article.source` contains. If the first line parses
as a JSON-encoded string (the format `playwright-cli --raw eval` emits) we
decode it; otherwise treat it as plain text.
"""

import json
import re
from pathlib import Path

ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st",
    "inc", "ltd", "co", "corp",
    "e.g", "i.e", "etc", "vs", "no",
    "u.s", "u.k", "u.s.a",
    "a.m", "p.m",
    "fig", "vol", "eq", "ref", "approx", "cf",
}

SENT_END = re.compile(r'([.!?])(["\')\]]?)(\s+)(?=[A-Z(\["\'])')


def split_paragraph(paragraph: str) -> list[str]:
    text = re.sub(r"\s+", " ", paragraph).strip()
    if not text:
        return []
    sentences: list[str] = []
    i = 0
    for m in SENT_END.finditer(text):
        end = m.end(2)
        candidate = text[i:end]
        prev_word = re.split(r"[\s(\[]", candidate)[-1].rstrip(".!?\"')]").lower()
        if prev_word in ABBREV:
            continue
        sentences.append(candidate.strip())
        i = m.end()
    tail = text[i:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def _decode(raw: str) -> str:
    first_line = raw.split("\n", 1)[0]
    try:
        candidate = json.loads(first_line)
    except json.JSONDecodeError:
        return raw
    return candidate if isinstance(candidate, str) else raw


def split_file(raw_path: Path, out_path: Path) -> int:
    text = _decode(raw_path.read_text(encoding="utf-8"))
    paragraphs = re.split(r"\n\s*\n", text)
    all_sents: list[str] = []
    for p in paragraphs:
        all_sents.extend(split_paragraph(p))
    out_path.write_text("\n\n".join(all_sents) + "\n", encoding="utf-8")
    print(f"wrote {len(all_sents)} sentences to {out_path}")
    return len(all_sents)
