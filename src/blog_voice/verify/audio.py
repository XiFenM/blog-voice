"""Verify generated TTS audio matches the source sentence via a multimodal LLM.

Per sentence: encode the wav as base64 and send it to a model that accepts
audio input (e.g. `google/gemini-3.5-flash` via ZenMux) together with the
original sentence. The model returns JSON describing whether the audio
correctly reads the text, plus a naturalness score and any issues.

The full per-sentence report is written to `articles/<slug>/verify_report.json`
so the result is queryable later. Failed sentences are surfaced as a
top-level `failed` list for quick triage.
"""

import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from blog_voice.llm.zenmux import get_client


def _system_prompt(target_language: str) -> str:
    return (
        "You are a strict QA reviewer for text-to-speech audio. "
        f"The audio is supposed to read the given sentence in {target_language}. "
        "Listen to the audio, then return strict JSON with this shape:\n"
        "{\n"
        '  "ok": boolean,                        // overall pass/fail\n'
        '  "transcription": string,              // what you actually hear\n'
        '  "matches_text": boolean,              // does transcription match the target sentence (allow minor punctuation/casing differences)\n'
        '  "naturalness": integer 1-5,           // 5 = indistinguishable from natural human reading\n'
        '  "issues": [string]                    // brief notes: mispronunciations, robotic prosody, cut-off audio, wrong emphasis, etc. Empty if none.\n'
        "}\n"
        "Set ok=false if matches_text is false OR naturalness < 3. "
        "Return JSON only, no markdown."
    )


def _user_content(sentence: str, audio_bytes: bytes, audio_format: str) -> list[dict]:
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    return [
        {
            "type": "text",
            "text": (
                f"Target sentence:\n{json.dumps({'sentence': sentence}, ensure_ascii=False)}\n\n"
                "Listen to the attached audio and return your QA verdict as JSON."
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
    audio_path: Path,
    target_language: str,
) -> dict:
    audio_format = audio_path.suffix.lstrip(".").lower() or "wav"
    response = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": _system_prompt(target_language)},
            {"role": "user", "content": _user_content(sentence, audio_path.read_bytes(), audio_format)},
        ],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    return json.loads(content)


def _load_report(path: Path) -> dict:
    if not path.exists():
        return {"results": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_report(path: Path, report: dict) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def verify_article(
    sentences: list[str],
    audio_files: list[Path],
    report_path: Path,
    model: str,
    concurrency: int,
    target_language: str,
    limit: int = 0,
) -> dict:
    if len(sentences) != len(audio_files):
        raise SystemExit(
            f"sentence/audio mismatch: {len(sentences)} vs {len(audio_files)}"
        )
    if limit:
        sentences = sentences[:limit]
        audio_files = audio_files[:limit]

    report = _load_report(report_path)
    report.setdefault("results", {})
    results: dict = report["results"]

    pending = [
        (i, s, f)
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
            executor.submit(_verify_one, client, model, s, f, target_language): (i, s, f)
            for i, s, f in pending
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
