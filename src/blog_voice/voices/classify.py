"""Classify and optionally split character voice clips by rough timbre mode."""

import csv
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def numeric_prefix(path: Path) -> int:
    return int(path.name.split("_", 1)[0])


def speech_intervals(y: np.ndarray, sr: int) -> list[tuple[int, int]]:
    intervals = librosa.effects.split(y, top_db=28, frame_length=1024, hop_length=256)
    merged: list[list[int]] = []
    max_gap = int(0.18 * sr)
    min_len = int(0.35 * sr)
    for start, end in intervals:
        if not merged or start - merged[-1][1] > max_gap:
            merged.append([int(start), int(end)])
        else:
            merged[-1][1] = int(end)
    return [(start, end) for start, end in merged if end - start >= min_len]


def segment_features(y: np.ndarray, sr: int) -> np.ndarray | None:
    rms = librosa.feature.rms(y=y)[0]
    if np.max(rms) < 1e-4:
        return None

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    delta = librosa.feature.delta(mfcc)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    harmonic, percussive = librosa.effects.hpss(y)
    harmonic_rms = librosa.feature.rms(y=harmonic)[0]
    percussive_rms = librosa.feature.rms(y=percussive)[0]

    features: list[float] = []
    for matrix in (mfcc, delta):
        features.extend(np.mean(matrix, axis=1))
        features.extend(np.std(matrix, axis=1))
    for values in (centroid, bandwidth, rolloff, flatness, zcr, rms, harmonic_rms, percussive_rms):
        features.append(float(np.mean(values)))
        features.append(float(np.std(values)))
        features.append(float(np.percentile(values, 90) - np.percentile(values, 10)))
    features.append(float(np.mean(percussive_rms) / (np.mean(harmonic_rms) + 1e-8)))
    return np.array(features, dtype=np.float32)


def mode_from_ratio(normal_ratio: float, normal_threshold: float, mecha_threshold: float) -> str:
    if normal_ratio >= normal_threshold:
        return "normal"
    if normal_ratio <= mecha_threshold:
        return "mecha"
    return "mixed"


def write_segment(out_dir: Path, mode: str, source: Path, index: int, y: np.ndarray, sr: int) -> None:
    target_dir = out_dir / mode
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source.stem}_seg{index:02d}.wav"
    sf.write(target, y, sr, subtype="PCM_16")


def classify(
    voice_dir: Path,
    report_path: Path,
    split_dir: Path | None,
    sr: int,
    normal_anchor_max_index: int,
    normal_threshold: float,
    mecha_threshold: float,
) -> None:
    files = sorted(voice_dir.glob("*.wav"))
    if not files:
        raise SystemExit(f"no wav files found in {voice_dir}")

    audio: dict[Path, tuple[np.ndarray, int]] = {}
    segments: list[tuple[Path, int, int, np.ndarray]] = []
    file_segment_indexes: dict[Path, list[int]] = {}

    for path in files:
        y, sample_rate = librosa.load(path, sr=sr, mono=True)
        audio[path] = (y, sample_rate)
        indexes = []
        for start, end in speech_intervals(y, sample_rate):
            features = segment_features(y[start:end], sample_rate)
            if features is None:
                continue
            indexes.append(len(segments))
            segments.append((path, start, end, features))
        file_segment_indexes[path] = indexes

    if not segments:
        raise SystemExit("no speech segments detected")

    features = np.vstack([segment[3] for segment in segments])
    labels = KMeans(n_clusters=2, random_state=11, n_init=80).fit_predict(
        StandardScaler().fit_transform(features)
    )

    anchor_labels = [
        labels[index]
        for path in files
        if numeric_prefix(path) <= normal_anchor_max_index
        for index in file_segment_indexes[path]
    ]
    if not anchor_labels:
        raise SystemExit("normal anchor produced no speech segments")
    normal_label = max(set(anchor_labels), key=anchor_labels.count)

    with report_path.open("w", encoding="utf-8", newline="") as report_file:
        writer = csv.writer(report_file, delimiter="\t")
        writer.writerow([
            "file",
            "duration",
            "segments",
            "normal_ratio",
            "file_mode",
            "segment_modes",
        ])
        for path in files:
            y, sample_rate = audio[path]
            indexes = file_segment_indexes[path]
            segment_labels = ["normal" if labels[index] == normal_label else "mecha" for index in indexes]
            normal_ratio = segment_labels.count("normal") / len(segment_labels) if segment_labels else 0.0
            file_mode = mode_from_ratio(normal_ratio, normal_threshold, mecha_threshold)
            timed_modes = []
            for segment_number, index in enumerate(indexes, start=1):
                _, start, end, _ = segments[index]
                mode = segment_labels[segment_number - 1]
                timed_modes.append(f"{start / sample_rate:.2f}-{end / sample_rate:.2f}:{mode}")
                if split_dir is not None:
                    write_segment(split_dir, mode, path, segment_number, y[start:end], sample_rate)
            writer.writerow([
                path.name,
                f"{len(y) / sample_rate:.2f}",
                len(indexes),
                f"{normal_ratio:.2f}",
                file_mode,
                " ".join(timed_modes),
            ])

    print(f"wrote {report_path}; segments={len(segments)}")
    if split_dir is not None:
        print(f"wrote split segments to {split_dir}")
