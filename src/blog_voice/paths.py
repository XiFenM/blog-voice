"""Per-article path layout.

Each article lives under articles/<slug>/ and owns its source text, the
sentence-split version, per-sentence wavs, the merged wav, and the LRC
subtitle. Defaults like title/artist/ref-voice/backend are stored in
meta.json so subsequent pipeline steps don't need them re-specified.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ArticlePaths:
    slug: str
    root: Path

    @property
    def meta(self) -> Path:
        return self.root / "meta.json"

    @property
    def source(self) -> Path:
        return self.root / "source.txt"

    @property
    def sentences(self) -> Path:
        return self.root / "sentences.txt"

    @property
    def sentences_enhanced(self) -> Path:
        return self.root / "sentences_enhanced.txt"

    @property
    def enhancement_cache(self) -> Path:
        return self.root / "enhancements.json"

    @property
    def audio_dir(self) -> Path:
        return self.root / "audio"

    @property
    def merged(self) -> Path:
        return self.root / "merged.wav"

    @property
    def lrc(self) -> Path:
        return self.root / "subtitle.lrc"

    @property
    def translation_cache(self) -> Path:
        return self.root / "translations_zh.json"

    @property
    def verify_report(self) -> Path:
        return self.root / "verify_report.json"

    def ensure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)


def article_paths(slug: str, articles_root: Path = Path("articles")) -> ArticlePaths:
    return ArticlePaths(slug=slug, root=articles_root / slug)


@dataclass
class ArticleMeta:
    title: str = ""
    artist: str = ""
    album: str = "blog-voice"
    ref_voice: str = ""
    backend: str = "chatterbox"
    fish_reference_id: str = ""
    extra: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "ArticleMeta":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known}
        return cls(
            title=data.get("title", ""),
            artist=data.get("artist", ""),
            album=data.get("album", "blog-voice"),
            ref_voice=data.get("ref_voice", ""),
            backend=data.get("backend", "chatterbox"),
            fish_reference_id=data.get("fish_reference_id", ""),
            extra=extra,
        )

    def dump(self, path: Path) -> None:
        data = {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "ref_voice": self.ref_voice,
            "backend": self.backend,
            "fish_reference_id": self.fish_reference_id,
            **self.extra,
        }
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
