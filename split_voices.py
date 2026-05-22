"""Split character voice clips by manually labelled timbre mode.

Uses labeled pure-normal and pure-mecha clips to build a reference model,
then finds the optimal split point for mixed files by scanning with a
sliding-window classifier.
"""

import argparse
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.ndimage import median_filter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def numeric_prefix(path: Path) -> int:
    return int(path.name.split("_", 1)[0])


def _features(y: np.ndarray, sr: int) -> np.ndarray | None:
    if len(y) < 0.35 * sr:
        return None
    rms = librosa.feature.rms(y=y)[0]
    if np.max(rms) < 1e-4:
        return None
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    delta = librosa.feature.delta(mfcc)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    roll = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    flat = librosa.feature.spectral_flatness(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    harm, perc = librosa.effects.hpss(y)
    hrms = librosa.feature.rms(y=harm)[0]
    prms = librosa.feature.rms(y=perc)[0]
    out: list[float] = []
    for a in (mfcc, delta):
        out.extend(np.mean(a, axis=1))
        out.extend(np.std(a, axis=1))
    for v in (centroid, bw, roll, flat, zcr, rms, hrms, prms):
        out.append(float(np.mean(v)))
        out.append(float(np.std(v)))
        out.append(float(np.percentile(v, 90) - np.percentile(v, 10)))
    out.append(float(np.mean(prms) / (np.mean(hrms) + 1e-8)))
    return np.array(out, dtype=np.float32)


def _utterances(
    y: np.ndarray, sr: int, min_len: float = 0.35, max_gap: float = 0.18
) -> list[tuple[int, int]]:
    intervals = librosa.effects.split(y, top_db=28, frame_length=1024, hop_length=256)
    min_s = int(min_len * sr)
    gap_s = int(max_gap * sr)
    merged: list[list[int]] = []
    for s, e in intervals:
        if not merged or s - merged[-1][1] > gap_s:
            merged.append([int(s), int(e)])
        else:
            merged[-1][1] = int(e)
    return [(s, e) for s, e in merged if e - s >= min_s]


def build_model(
    voice_dir: Path,
    pure_normal: list[int],
    pure_mecha: list[int],
    sr: int,
) -> tuple[StandardScaler, KMeans, int, int]:
    normal_feats: list[np.ndarray] = []
    mecha_feats: list[np.ndarray] = []
    for prefix in pure_normal:
        for path in voice_dir.glob(f"{prefix:03d}_*.wav"):
            y, _ = librosa.load(path, sr=sr, mono=True)
            for s, e in _utterances(y, sr):
                f = _features(y[s:e], sr)
                if f is not None:
                    normal_feats.append(f)
    for prefix in pure_mecha:
        for path in voice_dir.glob(f"{prefix:03d}_*.wav"):
            y, _ = librosa.load(path, sr=sr, mono=True)
            for s, e in _utterances(y, sr):
                f = _features(y[s:e], sr)
                if f is not None:
                    mecha_feats.append(f)
    if not normal_feats or not mecha_feats:
        raise SystemExit("not enough labeled data to build reference model")
    X = np.vstack(normal_feats + mecha_feats)
    y_labels = np.array([0] * len(normal_feats) + [1] * len(mecha_feats))
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    km = KMeans(n_clusters=2, random_state=11, n_init=80)
    km_labels = km.fit_predict(Xs)
    c0 = np.bincount(y_labels[km_labels == 0], minlength=2)
    c1 = np.bincount(y_labels[km_labels == 1], minlength=2)
    if c0[0] + c1[1] >= c0[1] + c1[0]:
        normal_cluster, mecha_cluster = 0, 1
    else:
        normal_cluster, mecha_cluster = 1, 0
    accuracy = (np.sum((km_labels == normal_cluster) & (y_labels == 0)) +
                np.sum((km_labels == mecha_cluster) & (y_labels == 1))) / len(y_labels)
    print(f"reference model accuracy on labeled data: {accuracy:.2%}")
    return scaler, km, normal_cluster, mecha_cluster


def _scan_labels(
    y: np.ndarray,
    sr: int,
    scaler: StandardScaler,
    km: KMeans,
    normal_cluster: int,
    mecha_cluster: int,
    window_s: float = 0.5,
    hop_s: float = 0.05,
) -> np.ndarray:
    """Return an array of binary labels (0=normal, 1=mecha) on a fine grid."""
    win = int(window_s * sr)
    hop = int(hop_s * sr)
    labels: list[int] = []
    for start in range(0, len(y) - win + 1, hop):
        seg = y[start : start + win]
        f = _features(seg, sr)
        if f is None:
            if labels:
                labels.append(labels[-1])
            else:
                labels.append(0)
            continue
        fs = scaler.transform(f.reshape(1, -1))
        pred = km.predict(fs)[0]
        labels.append(0 if pred == normal_cluster else 1)
    return np.array(labels)


def find_transition(
    y: np.ndarray,
    sr: int,
    scaler: StandardScaler,
    km: KMeans,
    normal_cluster: int,
    mecha_cluster: int,
    normal_first: bool = True,
) -> int | None:
    """Find the split point that best separates the two modes.

    Scans the audio with overlapping windows, then finds the single split
    point (sample index) that minimizes misclassifications assuming the
    left side is one mode and the right side the other.
    """
    labels = _scan_labels(y, sr, scaler, km, normal_cluster, mecha_cluster)
    if len(labels) < 4:
        return None
    smoothed = median_filter(labels.astype(float), size=max(5, len(labels) // 15 + 1))
    labels = (smoothed >= 0.5).astype(int)
    n = len(labels)
    cumsum = np.cumsum(labels)
    total = cumsum[-1]
    left_sum = np.insert(cumsum, 0, 0)
    right_sum = total - left_sum
    indices = np.arange(n + 1)
    if normal_first:
        left_wrong = left_sum
        right_wrong = (n - indices) - right_sum
    else:
        left_wrong = indices - left_sum
        right_wrong = right_sum
    errors = left_wrong + right_wrong
    best_idx = int(np.argmin(errors[1:-1])) + 1
    hop_s = 0.05
    center_time = (best_idx + 0.5) * hop_s
    return int(center_time * sr)


def write_segment(
    dest_dir: Path, source: Path, tag: str, index: int, y: np.ndarray, sr: int
) -> None:
    target = dest_dir / f"{source.stem}_{tag}{index:02d}.wav"
    sf.write(target, y, sr, subtype="PCM_16")


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

    scaler, km, normal_cluster, mecha_cluster = build_model(
        voice_dir, labels["pure_normal"], labels["pure_mecha"], args.sr
    )

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
            manual = labels.get("manual_split_ratios", {}).get(str(num))
            if manual is not None:
                split = int(len(y) * manual)
            else:
                split = find_transition(y, sr, scaler, km, normal_cluster, mecha_cluster, normal_first=True)
            if split is None or split <= 0 or split >= len(y):
                split = int(len(y) * 0.5)
            write_segment(normal_dir, path, "a", 1, y[:split], sr)
            write_segment(mecha_dir, path, "b", 1, y[split:], sr)
            stats["split"] += 1
        elif num in labels["split_mecha_then_normal"]:
            y, sr = librosa.load(path, sr=args.sr, mono=True)
            manual = labels.get("manual_split_ratios", {}).get(str(num))
            if manual is not None:
                split = int(len(y) * manual)
            else:
                split = find_transition(y, sr, scaler, km, normal_cluster, mecha_cluster, normal_first=False)
            if split is None or split <= 0 or split >= len(y):
                split = int(len(y) * 0.5)
            write_segment(mecha_dir, path, "a", 1, y[:split], sr)
            write_segment(normal_dir, path, "b", 1, y[split:], sr)
            stats["split"] += 1

    copied = stats["normal"] + stats["mecha"]
    print(f"copied {copied} pure files ({stats['normal']} normal, {stats['mecha']} mecha)")
    print(f"split {stats['split']} mixed files -> {out_dir}/normal/ and {out_dir}/mecha/")


if __name__ == "__main__":
    main()
