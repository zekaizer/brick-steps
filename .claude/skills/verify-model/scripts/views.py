"""Render a model from fixed angles, or close up on a point, for review. Needs LeoCAD and Xvfb (ADR 0001).

    uv run python .claude/skills/verify-model/scripts/views.py SLUG --out DIR
        writes front-left.png, front.png, side.png, top.png, rear.png and below.png
    uv run python .claude/skills/verify-model/scripts/views.py SLUG --out DIR --at X Y Z [--from DX DY DZ] [--name NAME]
        writes NAME.png (default close-X_Y_Z.png): a camera at the point plus the offset, looking at the point
    uv run python .claude/skills/verify-model/scripts/views.py PART --part --out DIR
        writes PART.png: one part from the front-left, to see its shape

SLUG may also be a path to an .mpd file. Coordinates are LDraw (-Y is up, -Z is the model's front).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

from lego_creator.instructions import build_mpd
from lego_creator.ldraw import Library, parse
from lego_creator.render import XVFB, leocad_config

ROOT = Path(__file__).resolve().parents[4]
# LeoCAD camera latitude and longitude for each named view; the model's front is -Z.
VIEWS = {"front-left": (30, -35), "front": (10, 0), "side": (0, -90), "top": (89, 0), "rear": (25, 150),
         "below": (-45, -30)}


def render(mpd: Path, out: Path, camera: list[str], size: tuple[int, int] = (1200, 900)) -> None:
    with tempfile.TemporaryDirectory() as conf:
        settings = Path(conf) / "LeoCAD Software" / "LeoCAD.conf"
        settings.parent.mkdir(parents=True)
        settings.write_text(leocad_config("#ffffff"), encoding="utf-8")
        cmd = [*XVFB, "leocad", "-l", str(ROOT / "ldraw"), "-i", str(out), "-w", str(size[0]), "-h", str(size[1]),
               *camera, "--aa-samples", "4", "--no-fade-steps", "--no-highlight", str(mpd)]
        subprocess.run(cmd, env={**os.environ, "XDG_CONFIG_HOME": conf}, check=True, capture_output=True)
    if not out.exists():
        raise SystemExit(f"LeoCAD wrote no image for {mpd}")
    print(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--part", action="store_true", help="target is an LDraw part id")
    ap.add_argument("--at", nargs=3, type=float, metavar=("X", "Y", "Z"))
    ap.add_argument("--from", dest="offset", nargs=3, type=float, metavar=("DX", "DY", "DZ"), default=(-350, -250, -450))
    ap.add_argument("--name")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    library = Library(ROOT / "ldraw", ROOT / "custom")
    if args.part:
        text = f"0 FILE part.ldr\n1 16 0 0 0 1 0 0 0 1 0 0 0 1 {args.target}.dat\n"
    else:
        path = Path(args.target)
        path = path if path.suffix == ".mpd" else ROOT / "models" / args.target / "model.mpd"
        text = path.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        mpd = Path(tmp) / "view.mpd"
        mpd.write_text(build_mpd(text, parse(text, default_name="main.ldr"), library, ROOT / "custom"), encoding="utf-8")
        if args.part:
            render(mpd, args.out / f"{args.target}.png", ["--camera-angles", "30", "-35"], (700, 500))
        elif args.at:
            x, y, z = args.at
            dx, dy, dz = args.offset
            name = args.name or f"close-{x:g}_{y:g}_{z:g}"
            camera = ["--camera-position-ldraw", *(f"{v:g}" for v in (x + dx, y + dy, z + dz, x, y, z, 0, -1, 0))]
            render(mpd, args.out / f"{name}.png", camera, (900, 700))
        else:
            for name, (lat, lon) in VIEWS.items():
                render(mpd, args.out / f"{name}.png", ["--camera-angles", str(lat), str(lon)])


if __name__ == "__main__":
    main()
