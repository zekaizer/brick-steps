"""Web fonts of the site, cut down to the characters its pages show (ADR 0004)."""

from __future__ import annotations

import hashlib
import io
import shutil
import urllib.parse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from .fetch import download

GOOGLE_FONTS = "https://raw.githubusercontent.com/google/fonts/5026800714d07231937d92eb4cceabf06e05d74e/"


@dataclass(frozen=True)
class FontSource:
    family: str  # as the design system's type families name it
    slug: str  # start of the written file's name
    path: str  # in the google/fonts repository
    sha256: str
    weights: tuple[int, int]  # a variable font is cut to this range; the @font-face rule declares it
    # Only for the characters the family's earlier sources lack, declared with unicode-range.
    fills_gaps: bool = False

    @property
    def file_name(self) -> str:
        return Path(self.path).name


SOURCES = (
    FontSource("Noto Sans KR", "noto-sans-kr", "ofl/notosanskr/NotoSansKR[wght].ttf",
               "194018e6b2b293a7964f037b25c0249ce1418bc9ab3c971060a03aa57861e252", (400, 700)),
    FontSource("Lexend", "lexend", "ofl/lexend/Lexend[wght].ttf",
               "3add53e641fbc81da64da4bb254285e2831b52b029527bc0714e2b9610832ee6", (600, 700)),
    # The arrows and the menu triangle of the mission blocks (↺ ↻ ▾) are in neither font above.
    FontSource("Noto Sans KR", "noto-sans-math", "ofl/notosansmath/NotoSansMath-Regular.ttf",
               "3f495fe933c06786e4d5f6d86b8ee70b6753a68ee3b9d87528726de0f6e2c47d", (400, 700), fills_gaps=True),
)


ASCII = "".join(chr(c) for c in range(0x20, 0x7F))


def fetch_fonts(cache: Path) -> list[tuple[FontSource, Path]]:
    """Every source font in cache/, downloaded on first use.

    Raises ValueError for a file that is not the pinned one.
    """
    found = []
    for source in SOURCES:
        path = download(GOOGLE_FONTS + urllib.parse.quote(source.path), cache / source.file_name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != source.sha256:
            raise ValueError(f"{path.name} is not the pinned {GOOGLE_FONTS}{source.path}; delete {path} and build again")
        found.append((source, path))
    return found


def used_chars(texts: Iterable[str]) -> str:
    """Printable ASCII and every other character in texts, each once, sorted."""
    chars = set(ASCII)
    for text in texts:
        chars.update(c for c in text if ord(c) > 0x7E)
    return "".join(sorted(chars))


def uncovered(sources: list[tuple[FontSource, Path]], chars: str) -> str:
    """The characters of chars outside printable ASCII that no source font has.

    The browser draws them in a device font.
    """
    have = set().union(*(_codepoints(TTFont(path, lazy=True)) for _, path in sources))
    return "".join(c for c in chars if ord(c) > 0x7E and ord(c) not in have)


def _codepoints(font: TTFont) -> set[int]:
    cmap = font.getBestCmap()
    assert cmap is not None, "every pinned source font has a Unicode cmap"
    return set(cmap)


def write_fonts(dest: Path, sources: list[tuple[FontSource, Path]], chars: str) -> str:
    """One WOFF2 file per source font in dest/, holding only chars and its weights; returns the @font-face rules.

    A gap-filling source gets only what its family still lacks, and no file when that is nothing.
    dest/ is emptied first. The rules' URLs are relative to dest's parent, where site.css is. File names carry a
    hash of their bytes because the service worker keeps fonts by URL across deploys.
    """
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    rules = []
    covered: dict[str, set[int]] = {}
    for source, path in sources:
        font = TTFont(path, recalcTimestamp=False)  # keeps head.modified: the same characters give the same file name
        have = _codepoints(font)
        wanted = [ord(c) for c in chars]
        if source.fills_gaps:
            wanted = [c for c in wanted if c > 0x7E and c in have and c not in covered.get(source.family, set())]
            if not wanted:
                continue
        covered.setdefault(source.family, set()).update(have)
        # name_IDs: updateFontNames below reads the STAT names.
        subsetter = subset.Subsetter(subset.Options(layout_features=["*"], name_IDs=["*"]))
        subsetter.populate(unicodes=wanted)
        subsetter.subset(font)
        if "fvar" in font:
            instancer.instantiateVariableFont(font, {"wght": source.weights}, inplace=True, updateFontNames=True)
        font.flavor = "woff2"
        buf = io.BytesIO()
        font.save(buf)
        data = buf.getvalue()
        name = f"{source.slug}-{hashlib.sha256(data).hexdigest()[:12]}.woff2"
        (dest / name).write_bytes(data)
        low, high = source.weights
        span = f" unicode-range: {', '.join(f'U+{c:04X}' for c in wanted)};" if source.fills_gaps else ""
        rules.append(f'@font-face {{ font-family: "{source.family}"; src: url("{dest.name}/{name}") format("woff2"); '
                     f"font-weight: {low} {high};{span} font-display: block; }}")
    return "\n".join(rules) + "\n"
