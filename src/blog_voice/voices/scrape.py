"""Scrape character voice audio from the Wuthering Waves wiki (wiki.kurobbs.com)."""

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

API_URL = "https://api.kurobbs.com/wiki/core/catalogue/item/getEntryDetail"
HEADERS = {
    "wiki_type": "9",
    "source": "h5",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "user-agent": "Mozilla/5.0",
}


def resolve_id(arg: str) -> str:
    if arg.isdigit():
        return arg
    m = re.search(r"/item/(\d+)", urlparse(arg).path)
    if not m:
        sys.exit(f"cannot extract character id from: {arg}")
    return m.group(1)


def fetch_entry(entry_id: str) -> dict:
    r = httpx.post(API_URL, headers=HEADERS, data={"id": entry_id}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if payload.get("code") != 200:
        sys.exit(f"api error: {payload}")
    return payload["data"]


def collect_audio(node, out):
    if isinstance(node, dict):
        url = node.get("playUrl")
        if url and url.endswith((".wav", ".mp3", ".ogg", ".m4a")):
            out.append({
                "title": node.get("audioTitle") or "untitled",
                "url": url,
                "text": (node.get("content") or "").strip(),
            })
        for v in node.values():
            collect_audio(v, out)
    elif isinstance(node, list):
        for v in node:
            collect_audio(v, out)


def safe_name(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", s).strip()


def _write_transcript(wav_path: Path, text: str) -> None:
    """Write the spoken-content transcript next to the wav.

    Filename matches what fish_audio.py looks for (<wav>.transcript.txt) so
    the fish backend can skip its ASR call entirely.
    """
    if not text:
        return
    transcript_path = wav_path.with_suffix(wav_path.suffix + ".transcript.txt")
    transcript_path.write_text(text + "\n", encoding="utf-8")


def download(entries, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for i, e in enumerate(entries, 1):
            ext = Path(urlparse(e["url"]).path).suffix or ".wav"
            fname = f"{i:03d}_{safe_name(e['title'])}{ext}"
            dest = out_dir / fname
            text = e.get("text", "")
            if dest.exists() and dest.stat().st_size > 0:
                _write_transcript(dest, text)
                print(f"  [skip] {fname}")
                continue
            for attempt in range(3):
                try:
                    with client.stream("GET", e["url"]) as resp:
                        resp.raise_for_status()
                        dest.write_bytes(resp.read())
                    _write_transcript(dest, text)
                    print(f"  [ok]   {fname}  ({dest.stat().st_size} bytes)")
                    break
                except Exception as ex:
                    print(f"  [retry {attempt + 1}] {fname}: {ex}")
                    time.sleep(1)
            else:
                print(f"  [fail] {fname}")


def scrape(target: str, out_root: Path) -> Path:
    entry_id = resolve_id(target)
    print(f"fetching entry {entry_id}…")
    data = fetch_entry(entry_id)
    name = data.get("name") or entry_id
    print(f"character: {name}")

    entries: list[dict] = []
    collect_audio(data, entries)
    print(f"found {len(entries)} audio clips")
    if not entries:
        return out_root

    out_dir = out_root / safe_name(name)
    print(f"downloading to {out_dir}…")
    download(entries, out_dir)

    manifest = out_dir / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"id": entry_id, "name": name, "entries": entries},
            ensure_ascii=False,
            indent=2,
        )
    )
    print(f"manifest: {manifest}")
    return out_dir
