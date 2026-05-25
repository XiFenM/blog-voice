"""Convert the merged wav into an m4a (AAC) for music-player workflows.

Players that sync `.lrc` subtitles (Apple Music / netease / …) want a compact
tagged audio file, not a 200 MB wav. This shells out to ffmpeg — a *soft*
dependency: if it isn't installed the wav is left untouched and we just warn,
so the rest of the pipeline never fails over a missing encoder.

ffmpeg is located on PATH, falling back to the static binary shipped by the
`imageio-ffmpeg` package if that happens to be installed.
"""

import shutil
import subprocess
from pathlib import Path


def _ffmpeg_exe() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:  # optional: a pip-installable static ffmpeg
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def to_m4a(
    wav_path: Path,
    out_path: Path,
    *,
    title: str = "",
    artist: str = "",
    album: str = "",
    bitrate: str = "128k",
) -> bool:
    """Encode `wav_path` to AAC `.m4a` at `out_path`, tagging title/artist/album.

    Returns True on success, False if ffmpeg is unavailable or the encode
    fails (the caller keeps the wav either way).
    """
    exe = _ffmpeg_exe()
    if exe is None:
        print(
            "m4a: ffmpeg not found — skipping (install ffmpeg, or "
            "`uv pip install imageio-ffmpeg`). merged.wav is unaffected."
        )
        return False
    if not wav_path.exists():
        print(f"m4a: source wav missing: {wav_path}")
        return False

    cmd = [exe, "-y", "-i", str(wav_path), "-c:a", "aac", "-b:a", bitrate]
    for key, value in (("title", title), ("artist", artist), ("album", album)):
        if value:
            cmd += ["-metadata", f"{key}={value}"]
    cmd.append(str(out_path))

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace")[-400:] if exc.stderr else ""
        print(f"m4a: ffmpeg failed (rc={exc.returncode}); merged.wav is unaffected.\n{detail}")
        return False

    print(f"wrote {out_path} (aac {bitrate})")
    return True
