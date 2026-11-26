"""Headless LeoCAD rendering (ADR 0001).

LeoCAD reads its background color only from its settings file, so every render runs with
XDG_CONFIG_HOME pointing at a private config dir; the user's own LeoCAD settings are never touched.
"""

from __future__ import annotations

import functools
import hashlib
import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .pack3d import pack_model

XVFB = ["xvfb-run", "-a", "-s", "-screen 0 1600x1200x24"]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def leocad_config(background: str) -> str:
    """LeoCAD.conf with a solid background; LeoCAD packs colors as 0xAABBGGRR."""
    r, g, b = _rgb(background)
    value = r | g << 8 | b << 16 | 0xFF << 24
    return f"[Settings]\nBackgroundGradient=false\nBackgroundColor={value}\n"


def leocad_cmd(mpd: Path, out_png: Path, libpath: Path, *, width: int, height: int, submodel: str | None = None,
               first: int | None = None, last: int | None = None, highlight: str | None = None) -> list[str]:
    cmd = [*XVFB, "leocad", "-l", str(libpath), "-i", str(out_png), "-w", str(width), "-h", str(height),
           "--viewpoint", "home", "--aa-samples", "4", "--no-fade-steps"]
    if submodel is not None:
        cmd += ["-s", submodel]
    if first is not None and last is not None:
        cmd += ["-f", str(first), "-t", str(last)]
    if highlight is not None:
        r, g, b = _rgb(highlight)
        cmd += ["--highlight", "--highlight-color", f"#FF{r:02X}{g:02X}{b:02X}"]
    else:
        cmd += ["--no-highlight"]
    return [*cmd, str(mpd)]


def step_outputs(out_png: Path) -> dict[int, Path]:
    """Files LeoCAD wrote for a step range: <stem>NN.png next to out_png, or out_png itself for a single step."""
    pattern = re.compile(rf"^{re.escape(out_png.stem)}(\d+){re.escape(out_png.suffix)}$")
    found = {}
    for p in out_png.parent.iterdir():
        if m := pattern.match(p.name):
            found[int(m.group(1))] = p
    if not found and out_png.exists():
        return {1: out_png}
    return dict(sorted(found.items()))


@functools.cache
def leocad_version() -> str:
    """LeoCAD's version line. It is part of every cache key, so a new LeoCAD renders everything again."""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    return subprocess.run(["leocad", "--version"], env=env, capture_output=True, text=True,
                          check=True).stdout.splitlines()[0].strip()


@dataclass
class RenderCache:
    """Pictures from earlier renders, kept in `root/<key>/`.

    The key covers everything LeoCAD reads for a picture: the model, every library file and colour it
    uses, the command line, the settings file and LeoCAD's version. Safe to share between threads.
    """

    root: Path
    reused: int = 0
    rendered: int = 0
    used: set[str] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def prune(self) -> int:
        """Delete the entries this run did not use; returns how many went."""
        stale = [e for e in self.root.iterdir() if e.name not in self.used] if self.root.is_dir() else []
        for entry in stale:
            shutil.rmtree(entry)
        return len(stale)


def _cache_key(mpd: Path, libpath: Path, cmd: list[str], background: str) -> str:
    text = mpd.read_text(encoding="utf-8")
    main = next((line.split(None, 2)[2].strip() for line in text.splitlines()
                 if line.split(None, 2)[:2] == ["0", "FILE"] and len(line.split(None, 2)) == 3), mpd.name)
    digest = hashlib.sha256()
    for piece in (leocad_version(), "\0".join(cmd), leocad_config(background), pack_model(text, main, [libpath])):
        digest.update(piece.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()[:32]


def _through_cache(cache: RenderCache | None, mpd: Path, out_png: Path, libpath: Path, config_dir: Path,
                   background: str, key_cmd: list[str], cmd: list[str], outputs) -> None:
    """Run `cmd`, or copy its pictures from the cache. `outputs()` lists what the run wrote.

    A cached file is stored under its name minus `out_png`'s stem, so it comes back under any stem.
    """
    if cache is None:
        _run(cmd, config_dir, background)
        return
    key = _cache_key(mpd, libpath, key_cmd, background)
    entry = cache.root / key
    with cache._lock:
        cache.used.add(key)
    if entry.is_dir():
        for f in entry.iterdir():
            shutil.copyfile(f, out_png.parent / (out_png.stem + f.name))
        with cache._lock:
            cache.reused += 1
        return
    _run(cmd, config_dir, background)
    # Filled under a private name and renamed, so a half-written entry is never read.
    tmp = cache.root / f".{key}-{os.getpid()}-{threading.get_ident()}"
    tmp.mkdir(parents=True)
    for p in outputs():
        shutil.copyfile(p, tmp / p.name[len(out_png.stem):])
    try:
        tmp.rename(entry)
    except OSError:  # another thread stored the same picture first
        shutil.rmtree(tmp)
    with cache._lock:
        cache.rendered += 1


def _run(cmd: list[str], config_dir: Path, background: str) -> None:
    conf = config_dir / "LeoCAD Software" / "LeoCAD.conf"
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(leocad_config(background), encoding="utf-8")
    env = {**os.environ, "XDG_CONFIG_HOME": str(config_dir)}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"leocad failed ({result.returncode}): {result.stderr.strip()[-500:]}")


def render_steps(mpd: Path, out_png: Path, libpath: Path, config_dir: Path, *, submodel: str, count: int,
                 width: int, height: int, background: str, highlight: str | None,
                 cache: RenderCache | None = None) -> dict[int, Path]:
    """Render steps 1..count of a submodel, or take them from `cache`; returns {step number: png}."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    args = {"width": width, "height": height, "submodel": submodel, "first": 1, "last": count, "highlight": highlight}
    _through_cache(cache, mpd, out_png, libpath, config_dir, background,
                   leocad_cmd(Path("MODEL"), Path("OUT.png"), Path("LIB"), **args),
                   leocad_cmd(mpd, out_png, libpath, **args), lambda: step_outputs(out_png).values())
    return step_outputs(out_png)


def render_image(mpd: Path, out_png: Path, libpath: Path, config_dir: Path, *, width: int, height: int,
                 background: str, cache: RenderCache | None = None) -> Path:
    """Render a whole model (its last step) as one picture, or take it from `cache`."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _through_cache(cache, mpd, out_png, libpath, config_dir, background,
                   leocad_cmd(Path("MODEL"), Path("OUT.png"), Path("LIB"), width=width, height=height),
                   leocad_cmd(mpd, out_png, libpath, width=width, height=height), lambda: [out_png])
    if not out_png.exists():
        raise RuntimeError(f"leocad wrote no image for {mpd}")
    return out_png
