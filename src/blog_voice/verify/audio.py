"""Verify generated TTS audio matches the source sentence via a multimodal LLM.

Per sentence: encode the wav as base64 and send it to a model that accepts
audio input (e.g. `google/gemini-3.5-flash` via ZenMux) together with the
original sentence AND its intended spoken form (the normalized text). The
model submits its verdict by calling the `submit_review` tool — and, because
it actually *heard* what went wrong, can propose a `corrected_spoken_text`
rewrite that would fix a mispronunciation (e.g. respelling `Impl` so it isn't
read as "impulse"). The caller applies that fix and re-synthesizes.

The full per-sentence report is written to `articles/<slug>/verify_report.json`
so the result is queryable later, with `failed_indexes` surfaced for triage.
"""

import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from blog_voice.llm.zenmux import get_client

_REVIEW_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_review",
        "description": "Submit the QA verdict for one TTS audio clip.",
        "parameters": {
            "type": "object",
            "properties": {
                "ok": {"type": "boolean", "description": "overall pass; false if matches_text is false OR naturalness < 3"},
                "transcription": {"type": "string", "description": "what you actually hear in the audio"},
                "matches_text": {
                    "type": "boolean",
                    "description": "does the audio match the INTENDED SPOKEN FORM (allow minor punctuation/casing; the symbol rewrites are correct, not errors)",
                },
                "naturalness": {"type": "integer", "description": "1-5, where 5 is indistinguishable from natural human reading"},
                "issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "brief notes: mispronunciations, robotic prosody, gasps/breath artifacts, cut-off audio, wrong emphasis. Empty if none.",
                },
                "corrected_spoken_text": {
                    "type": ["string", "null"],
                    "description": (
                        "If the audio is wrong because of HOW the spoken-form text was written "
                        "(a mispronounced token, a tag that caused an artifact), provide a corrected "
                        "spoken-form rewrite of the full intended spoken form that would fix it — e.g. "
                        "respell 'Impl' as 'Imp-ell' so it isn't read as 'impulse', or drop a bad tag. "
                        "Set null when text can't help (e.g. a robotic/distorted voice — that needs a "
                        "different voice reference, not different text)."
                    ),
                },
            },
            "required": ["ok", "transcription", "matches_text", "naturalness", "issues", "corrected_spoken_text"],
        },
    },
}


def _system_prompt(target_language: str) -> str:
    return (
        "You are a strict QA reviewer for text-to-speech audio. "
        f"The audio reads a {target_language} sentence. The TTS engine was fed a "
        "SPOKEN-FORM rewrite of the original, where code symbols and tricky "
        "tokens are written the way they should be pronounced (e.g. 'torch.mm' "
        "-> 'torch dot M M', 'tensor[1, 0]' -> 'tensor at index one comma "
        "zero'). You are given the original sentence AND that intended spoken "
        "form. Judge the audio against the INTENDED SPOKEN FORM — the symbol "
        "rewrites are correct and expected, not errors. Submit your verdict by "
        "calling the submit_review tool. When the audio mispronounced something "
        "because of how the text was written, propose a corrected_spoken_text "
        "fix; when only the voice quality is bad, leave corrected_spoken_text null."
    )


def _user_content(
    sentence: str,
    spoken_form: str | None,
    audio_bytes: bytes,
    audio_format: str,
) -> list[dict]:
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    payload = {"original_sentence": sentence}
    if spoken_form is not None and spoken_form != sentence:
        payload["intended_spoken_form"] = spoken_form
    return [
        {
            "type": "text",
            "text": (
                f"{json.dumps(payload, ensure_ascii=False)}\n\n"
                "Listen to the attached audio and call submit_review with your verdict, "
                "judging against the intended spoken form."
            ),
        },
        {
            "type": "input_audio",
            "input_audio": {"data": encoded, "format": audio_format},
        },
    ]


def _verify_one(
    client,
    model: str,
    sentence: str,
    spoken_form: str | None,
    audio_path: Path,
    target_language: str,
) -> dict:
    audio_format = audio_path.suffix.lstrip(".").lower() or "wav"
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        tools=[_REVIEW_TOOL],
        tool_choice={"type": "function", "function": {"name": "submit_review"}},
        messages=[
            {"role": "system", "content": _system_prompt(target_language)},
            {
                "role": "user",
                "content": _user_content(
                    sentence, spoken_form, audio_path.read_bytes(), audio_format
                ),
            },
        ],
    )
    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None)
    if tool_calls:
        return json.loads(tool_calls[0].function.arguments)
    # Fallback: some providers may answer with plain JSON content instead.
    return json.loads(message.content or "{}")


def _load_report(path: Path) -> dict:
    if not path.exists():
        return {"results": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_report(path: Path, report: dict) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def invalidate_indexes(report_path: Path, indexes: list[int]) -> None:
    """Drop the given sentence indexes from an existing report.

    Used when a clip's audio is regenerated: removing its stored verdict
    makes the next `verify_article()` treat it as pending and re-check it
    (verify is otherwise resumable and skips indexes already present).
    """
    if not report_path.exists() or not indexes:
        return
    report = _load_report(report_path)
    results = report.get("results", {})
    for idx in indexes:
        results.pop(str(idx), None)
    _save_report(report_path, report)


def verify_article(
    sentences: list[str],
    audio_files: list[Path],
    report_path: Path,
    model: str,
    concurrency: int,
    target_language: str,
    limit: int = 0,
    spoken_sentences: list[str] | None = None,
) -> dict:
    if len(sentences) != len(audio_files):
        raise SystemExit(
            f"sentence/audio mismatch: {len(sentences)} vs {len(audio_files)}"
        )
    if spoken_sentences is not None and len(spoken_sentences) != len(sentences):
        raise SystemExit(
            f"spoken/sentence mismatch: {len(spoken_sentences)} vs {len(sentences)}"
        )
    if limit:
        sentences = sentences[:limit]
        audio_files = audio_files[:limit]
        if spoken_sentences is not None:
            spoken_sentences = spoken_sentences[:limit]

    report = _load_report(report_path)
    report.setdefault("results", {})
    results: dict = report["results"]

    def _spoken_at(idx0: int) -> str | None:
        return spoken_sentences[idx0] if spoken_sentences is not None else None

    pending = [
        (i, s, f, _spoken_at(i - 1))
        for i, (s, f) in enumerate(zip(sentences, audio_files), 1)
        if str(i) not in results
    ]
    if not pending:
        print("nothing to verify (report already complete)")
        return report

    client = get_client()
    print(f"verifying {len(pending)} clips via {model} (concurrency={concurrency})")
    completed = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_verify_one, client, model, s, spoken, f, target_language): (i, s, f)
            for i, s, f, spoken in pending
        }
        for future in as_completed(futures):
            i, sentence, audio = futures[future]
            try:
                verdict = future.result()
            except Exception as exc:
                verdict = {"ok": False, "issues": [f"verification error: {exc}"]}
            results[str(i)] = {
                "index": i,
                "audio": audio.name,
                "sentence": sentence,
                **verdict,
            }
            completed += 1
            tag = "OK" if verdict.get("ok") else "FAIL"
            issues = verdict.get("issues") or []
            issue_str = f" — {issues[0]}" if issues else ""
            print(f"[{tag}] {completed}/{len(pending)} #{i:04d}{issue_str}")
            _save_report(report_path, report)

    # Sort + compute summary.
    sorted_results = sorted(results.values(), key=lambda r: r["index"])
    failed = [r for r in sorted_results if not r.get("ok")]
    report["model"] = model
    report["total"] = len(sorted_results)
    report["passed"] = len(sorted_results) - len(failed)
    report["failed_count"] = len(failed)
    report["failed_indexes"] = [r["index"] for r in failed]
    _save_report(report_path, report)

    print(f"\nverify summary: {report['passed']} / {report['total']} passed; {report['failed_count']} failed")
    if failed:
        print("failed indexes:", report["failed_indexes"][:20], "…" if len(failed) > 20 else "")
    return report
