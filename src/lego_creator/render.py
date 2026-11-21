"""Headless LeoCAD rendering (ADR 0001).

LeoCAD reads its background color only from its settings file, so every render runs with
XDG_CONFIG_HOME pointing at a private config dir; the user's own LeoCAD settings are never touched.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

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


def _run(cmd: list[str], config_dir: Path, background: str) -> None:
    conf = config_dir / "LeoCAD Software" / "LeoCAD.conf"
    conf.parent.mkdir(parents=True, exist_ok=True)
    conf.write_text(leocad_config(background), encoding="utf-8")
    env = {**os.environ, "XDG_CONFIG_HOME": str(config_dir)}
    result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"leocad failed ({result.returncode}): {result.stderr.strip()[-500:]}")


def render_steps(mpd: Path, out_png: Path, libpath: Path, config_dir: Path, *, submodel: str, count: int,
                 width: int, height: int, background: str, highlight: str | None) -> dict[int, Path]:
    """Render steps 1..count of a submodel; returns {step number: png}."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _run(leocad_cmd(mpd, out_png, libpath, width=width, height=height, submodel=submodel, first=1, last=count,
                    highlight=highlight), config_dir, background)
    return step_outputs(out_png)


def render_image(mpd: Path, out_png: Path, libpath: Path, config_dir: Path, *, width: int, height: int,
                 background: str) -> Path:
    """Render a whole model (its last step) as one picture."""
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _run(leocad_cmd(mpd, out_png, libpath, width=width, height=height), config_dir, background)
    if not out_png.exists():
        raise RuntimeError(f"leocad wrote no image for {mpd}")
    return out_png
