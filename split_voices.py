"""Split character voice clips by manually labelled timbre mode."""

import argparse
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf


def numeric_prefix(path: Path) -> int:
    return int(path.name.split("_", 1)[0])


def find_split_point(y: np.ndarray, sr: int, mid_ratio: float = 0.5) -> int:
    """Find the best split point near mid_ratio (0-1) by looking for a silence gap."""
    mid = int(len(y) * mid_ratio)
    frame_len = int(0.05 * sr)
    search_radius = int(0.4 * sr)
    start = max(mid - search_radius, 0)
    end = min(mid + search_radius, len(y))
    rms = np.array([
        np.sqrt(np.mean(y[i:i + frame_len] ** 2))
        for i in range(start, end - frame_len)
    ])
    threshold = np.max(rms) * 0.03
    below = np.where(rms < threshold)[0]
    if len(below) == 0:
        return mid
    clusters = []
    cluster_start = below[0]
    for i in range(1, len(below)):
        if below[i] - below[i - 1] > 2:
            clusters.append((cluster_start, below[i - 1]))
            cluster_start = below[i]
    clusters.append((cluster_start, below[-1]))
    best_gap = max(clusters, key=lambda c: c[1] - c[0])
    best_mid = (best_gap[0] + best_gap[1]) // 2 + start
    return best_mid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", default="voice_labels.json")
    parser.add_argument("--sr", type=int, default=22050)
    args = parser.parse_args()

    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    voice_dir = Path(labels["voice_dir"])
    out_dir = Path(labels["out_dir"])

    normal_dir = out_dir / "normal"
    mecha_dir = out_dir / "mecha"

    for d in [normal_dir, mecha_dir]:
        d.mkdir(parents=True, exist_ok=True)

    files = {numeric_prefix(p): p for p in sorted(voice_dir.glob("*.wav"))}
    stats = {"normal": 0, "mecha": 0, "split": 0}

    def copy_to(dest_dir: Path, source: Path) -> None:
        y, sr = librosa.load(source, sr=args.sr, mono=True)
        target = dest_dir / source.name
        sf.write(target, y, sr, subtype="PCM_16")
        stats[dest_dir.parent.name if dest_dir.parent.name != "normal" and dest_dir.parent.name != "mecha" else dest_dir.name if dest_dir.name in ("normal", "mecha") else "normal"] += 1

    def write_segment(dest_dir: Path, source: Path, tag: str, index: int, y: np.ndarray, sr: int) -> None:
        target = dest_dir / f"{source.stem}_{tag}{index:02d}.wav"
        sf.write(target, y, sr, subtype="PCM_16")

    for num, path in files.items():
        if num in labels["pure_normal"]:
            y, sr = librosa.load(path, sr=args.sr, mono=True)
            sf.write(normal_dir / path.name, y, sr, subtype="PCM_16")
            stats["normal"] += 1

        elif num in labels["pure_mecha"]:
            y, sr = librosa.load(path, sr=args.sr, mono=True)
            sf.write(mecha_dir / path.name, y, sr, subtype="PCM_16")
            stats["mecha"] += 1

        elif num in labels["split_normal_then_mecha"]:
            y, sr = librosa.load(path, sr=args.sr, mono=True)
            split = find_split_point(y, sr, 0.5)
            write_segment(normal_dir, path, "a", 1, y[:split], sr)
            write_segment(mecha_dir, path, "b", 1, y[split:], sr)
            stats["split"] += 1

        elif num in labels["split_mecha_then_normal"]:
            y, sr = librosa.load(path, sr=args.sr, mono=True)
            split = find_split_point(y, sr, 0.5)
            write_segment(mecha_dir, path, "a", 1, y[:split], sr)
            write_segment(normal_dir, path, "b", 1, y[split:], sr)
            stats["split"] += 1

    copied = stats["normal"] + stats["mecha"]
    print(f"copied {copied} pure files ({stats['normal']} normal, {stats['mecha']} mecha)")
    print(f"split {stats['split']} mixed files -> {out_dir}/normal/ and {out_dir}/mecha/")


if __name__ == "__main__":
    main()
