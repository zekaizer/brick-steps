"""`lc` command line entry point."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import re
import shutil
import sys
import tomllib
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import yaml

from .bom import Bom, load_id_map, load_inventory, load_unknown_parts
from .export import ExportEnv, build_manual, build_site, write_assets
from .ldraw import Library, flatten, parse
from .rebrickable import extract_set_inventory
from .release import check_release, release_notes
from .validate import validate

# Editable install: src/lego_creator/cli.py -> repo root.
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
LDRAW_URL = "https://library.ldraw.org/library/updates/complete.zip"
REBRICKABLE_URL = "https://cdn.rebrickable.com/media/downloads/{}.csv.gz"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# library.ldraw.org rejects urllib's default agent with 403; identify the tool instead (no personal data).
USER_AGENT = "brick-steps/0 (+https://github.com/zekaizer/brick-steps)"

MPD_TEMPLATE = """\
0 FILE main.ldr
0 {name}
0 Name: main.ldr
0 Author: {author}
0 // Port map: 0 !LC PORT <A-F> <ldraw part id> <role>
"""

SPEC_TEMPLATE = """\
# {name}

## Purpose

## Mechanism

## Ports

Declared in `model.mpd` as `0 !LC PORT` lines; `lc validate` checks them.

## Open questions
"""

PROGRAM_TEMPLATE = """\
from pybricks.hubs import PrimeHub

hub = PrimeHub()
"""


def _fail(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


def _load_model(root: Path, slug: str) -> tuple[dict, Path]:
    d = root / "models" / slug
    meta = yaml.safe_load((d / "model.yaml").read_text(encoding="utf-8")) or {}
    return meta, d / "model.mpd"


def _kit_counts(kits: dict[str, int] | list[str] | None) -> dict[str, int]:
    """Normalize model.yaml `kits` ({set: qty} or a list with repeats) to {set: qty}."""
    if isinstance(kits, dict):
        return {str(k): int(v) for k, v in kits.items()}
    return dict(Counter(kits or []))


def _owned_kits(root: Path) -> dict[str, int]:
    owned = root / ".local" / "owned.yaml"
    if owned.exists():
        return _kit_counts((yaml.safe_load(owned.read_text(encoding="utf-8")) or {}).get("kits"))
    return {"45678-1": 1}


def _load_kits(root: Path, kits: dict[str, int]) -> Bom:
    available: Bom = Counter()
    for k, qty in kits.items():
        for key, n in load_inventory(root / "inventory" / f"{k}.csv").items():
            available[key] += n * qty
    return available


def cmd_new(root: Path, _lib: Library, args: argparse.Namespace) -> int:
    if not SLUG_RE.match(args.slug):
        return _fail(f"slug must match {SLUG_RE.pattern}")
    d = root / "models" / args.slug
    if d.exists():
        return _fail(f"{d} already exists")
    (d / "program").mkdir(parents=True)
    name = args.name or args.slug.replace("-", " ").title()
    kits = _kit_counts(args.kit) if args.kit else _owned_kits(root)
    meta = {"name": name, "kits": kits, "status": "draft", "version": 1}
    (d / "model.yaml").write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
    (d / "model.mpd").write_text(MPD_TEMPLATE.format(name=name, author=args.author), encoding="utf-8")
    (d / "spec.md").write_text(SPEC_TEMPLATE.format(name=name), encoding="utf-8")
    (d / "program" / "main.py").write_text(PROGRAM_TEMPLATE, encoding="utf-8")
    print(f"created {d}")
    return 0


def cmd_validate(root: Path, lib: Library, args: argparse.Namespace) -> int:
    meta, mpd = _load_model(root, args.slug)
    doc = parse(mpd.read_text(encoding="utf-8"), default_name=mpd.name)
    kits = _kit_counts(meta.get("kits"))
    available = _load_kits(root, kits)
    unknown = set().union(*(load_unknown_parts(root / "inventory" / f"{k}.csv") for k in kits))
    issues = validate(doc, lib, available, load_id_map(root / "inventory" / "id-map.csv"), unknown)
    for i in issues:
        print(f"{i.level:7} {i.code:20} {i.message}")
    errors = sum(i.level == "error" for i in issues)
    print(f"{args.slug}: {errors} error(s), {len(issues) - errors} warning(s)")
    return 1 if errors else 0


def cmd_bom(root: Path, lib: Library, args: argparse.Namespace) -> int:
    _, mpd = _load_model(root, args.slug)
    bom = flatten(parse(mpd.read_text(encoding="utf-8"), default_name=mpd.name))
    print("part,color,qty,title")
    for (pid, color), n in sorted(bom.items()):
        print(f"{pid},{color},{n},{lib.title(pid) or '?'}")
    return 0


def _download(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {url}")
        tmp = dest.with_suffix(dest.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp, tmp.open("wb") as f:
            shutil.copyfileobj(resp, f)
        tmp.rename(dest)
    return dest


def cmd_fetch_ldraw(root: Path, _lib: Library, _args: argparse.Namespace) -> int:
    z = _download(LDRAW_URL, root / ".cache" / "dl" / "complete.zip")
    with zipfile.ZipFile(z) as zf:
        zf.extractall(root)  # archive entries are rooted at ldraw/
    print(f"extracted to {root / 'ldraw'}")
    return 0


def _read_gz_csv(path: Path) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def cmd_import_inventory(root: Path, _lib: Library, args: argparse.Namespace) -> int:
    dl = root / ".cache" / "dl"
    tables = {t: _read_gz_csv(_download(REBRICKABLE_URL.format(t), dl / f"{t}.csv.gz"))
              for t in ("inventories", "inventory_parts", "parts")}
    names = {r["part_num"]: r["name"] for r in tables["parts"]}
    for set_num in args.sets:
        rows = extract_set_inventory(tables["inventories"], tables["inventory_parts"], names, set_num)
        if not rows:
            return _fail(f"set {set_num} not found in Rebrickable data")
        out = root / "inventory" / f"{set_num}.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=["part_num", "color_id", "quantity", "name"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        out.write_text(buf.getvalue(), encoding="utf-8")
        print(f"{out}: {len(rows)} rows, {sum(int(r['quantity']) for r in rows)} parts")
    return 0


def _export_env(root: Path, args: argparse.Namespace) -> ExportEnv:
    tokens = json.loads((root / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    return ExportEnv(args.ldraw_dir, root / "custom", tokens, root / ".cache" / "leocad")


def cmd_site(root: Path, _lib: Library, args: argparse.Namespace) -> int:
    out = args.out or root / "site"
    cards = build_site(root, out, _export_env(root, args), include_drafts=args.include_drafts, pdf=not args.no_pdf)
    print(f"{out}: {len(cards)} manual(s): {', '.join(c.slug for c in cards) or 'none'}")
    return 0


def cmd_instructions(root: Path, _lib: Library, args: argparse.Namespace) -> int:
    meta, mpd = _load_model(root, args.slug)
    out = args.out or root / "models" / args.slug / "out" / "manual"
    env = _export_env(root, args)
    write_assets(out / "assets", env.tokens)
    card = build_manual(
        meta.get("name", args.slug), args.slug, mpd.read_text(encoding="utf-8"), env, out,
        thumbs_dir=out / "parts", thumbs_href="parts/", assets_href="assets/", sw_href=None, manifest_href=None,
        pdf=not args.no_pdf,
    )
    print(f"{out / 'index.html'}: {card.step_count} steps, {card.part_count} parts")
    return 0


def cmd_release_check(root: Path, _lib: Library, args: argparse.Namespace) -> int:
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    problems = check_release(args.tag, version, changelog)
    for p in problems:
        print(f"error: {p}", file=sys.stderr)
    if problems:
        return 1
    print(release_notes(changelog, args.tag.removeprefix("v")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lc", description="LEGO SPIKE Prime model tooling")
    p.add_argument("--root", type=Path, default=Path(os.environ.get("LC_ROOT", DEFAULT_ROOT)))
    p.add_argument("--ldraw", type=Path, default=None, help="LDraw library dir (default: $LDRAWDIR or <root>/ldraw)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("new", help="scaffold models/<slug>")
    s.add_argument("slug")
    s.add_argument("--name")
    s.add_argument("--kit", action="append", help="kit set id, repeat for multiple copies (default: .local/owned.yaml, else 45678-1)")
    s.add_argument("--author", default="")
    s.set_defaults(func=cmd_new)

    s = sub.add_parser("validate", help="check parts, kit inventory and ports")
    s.add_argument("slug")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("bom", help="print flattened BOM in LDraw ids")
    s.add_argument("slug")
    s.set_defaults(func=cmd_bom)

    s = sub.add_parser("instructions", help="export one model's manual (HTML + PDF) via LeoCAD")
    s.add_argument("slug")
    s.add_argument("--out", type=Path, help="default: models/<slug>/out/manual")
    s.add_argument("--no-pdf", action="store_true")
    s.set_defaults(func=cmd_instructions)

    s = sub.add_parser("site", help="build the gallery + manuals site (GitHub Pages) via LeoCAD")
    s.add_argument("--out", type=Path, help="default: <root>/site")
    s.add_argument("--include-drafts", action="store_true", help="also publish models whose status is not ready")
    s.add_argument("--no-pdf", action="store_true")
    s.set_defaults(func=cmd_site)

    s = sub.add_parser("release-check", help="check tag, pyproject and CHANGELOG agree; print the release notes")
    s.add_argument("tag", help="e.g. v0.0.1")
    s.set_defaults(func=cmd_release_check)

    s = sub.add_parser("fetch-ldraw", help="download and extract the official LDraw library")
    s.set_defaults(func=cmd_fetch_ldraw)

    s = sub.add_parser("import-inventory", help="write inventory/<set>.csv from Rebrickable bulk data")
    s.add_argument("sets", nargs="+", metavar="SET", help="e.g. 45678-1")
    s.set_defaults(func=cmd_import_inventory)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root: Path = args.root
    ldraw = args.ldraw or Path(os.environ.get("LDRAWDIR", root / "ldraw"))
    args.ldraw_dir = ldraw
    return args.func(root, Library(ldraw, root / "custom"), args)


if __name__ == "__main__":
    sys.exit(main())
