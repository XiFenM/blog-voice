"""Split decoded blog text into sentences, separated by blank lines."""

import json
import pathlib
import re

RAW = pathlib.Path("pytorch_internals_raw.txt")
OUT = pathlib.Path("pytorch_internals_sentences.txt")

ABBREV = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st",
    "inc", "ltd", "co", "corp",
    "e.g", "i.e", "etc", "vs", "no",
    "u.s", "u.k", "u.s.a",
    "a.m", "p.m",
    "fig", "vol", "eq", "ref", "approx", "cf",
}

SENT_END = re.compile(r'([.!?])(["\')\]]?)(\s+)(?=[A-Z(\["\'])')


def split_sentences(paragraph: str) -> list[str]:
    text = re.sub(r"\s+", " ", paragraph).strip()
    if not text:
        return []
    sentences = []
    buf = []
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


def main():
    first_line = RAW.read_text().split("\n", 1)[0]
    text = json.loads(first_line)

    paragraphs = re.split(r"\n\s*\n", text)
    all_sents: list[str] = []
    for p in paragraphs:
        all_sents.extend(split_sentences(p))

    OUT.write_text("\n\n".join(all_sents) + "\n")
    print(f"wrote {len(all_sents)} sentences to {OUT}")


if __name__ == "__main__":
    main()
