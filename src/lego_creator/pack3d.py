"""Pack a model and every LDraw file it needs into one text file for the browser 3D view (ADR 0002)."""

from __future__ import annotations

from pathlib import Path

from .ldraw import normalize_name

# Library folders, in the order three.js LDrawLoader would try them over the network.
SEARCH = ("parts", "p", "models", "")
# Meta lines that only matter to people reading the part file.
DROPPED = ("0 !HISTORY", "0 !KEYWORDS", "0 !HELP", "0 !CATEGORY", "0 !CMDLINE", "0 //")


def _key(ref: str) -> str:
    """The cache name LDrawLoader gives a referenced file."""
    ref = normalize_name(ref)
    if ref.startswith("s/"):
        return "parts/" + ref
    if ref.startswith("48/"):
        return "p/" + ref
    return ref


def _refs(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        tokens = line.split(None, 14)
        if len(tokens) == 15 and tokens[0] == "1":
            out.append(tokens[14])
    return out


def _find(ref: str, roots: list[Path]) -> Path:
    name = normalize_name(ref)
    for root in roots:
        for folder in SEARCH:
            path = root / folder / name
            if path.is_file():
                return path
    raise ValueError(f"file not found in the LDraw libraries: {name}")


def _submodels(text: str, main_name: str) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current = blocks.setdefault(normalize_name(main_name), [])
    for line in text.splitlines():
        tokens = line.split(None, 2)
        if tokens[:2] == ["0", "FILE"] and len(tokens) == 3:
            current = blocks.setdefault(normalize_name(tokens[2]), [])
        elif tokens[:2] != ["0", "NOFILE"] and line.strip():
            current.append(line.strip())
    return {name: lines for name, lines in blocks.items() if lines}


def pack_model(text: str, main_name: str, roots: list[Path]) -> str:
    """Colours, then each submodel and each referenced library file as a `0 FILE` block.

    Nothing but colours precedes the first block, so the viewer chooses what to draw by
    prepending one reference line. `roots` are searched in order (official library first).
    """
    colours = [line.strip() for line in (roots[0] / "LDConfig.ldr").read_text(encoding="utf-8").splitlines()
               if line.startswith("0 !COLOUR")]
    blocks = {name: "\n".join(lines) for name, lines in _submodels(text, main_name).items()}
    queue = [ref for body in blocks.values() for ref in _refs(body)]
    while queue:
        ref = queue.pop()
        key = _key(ref)
        if key in blocks:
            continue
        body = _find(ref, roots).read_text(encoding="utf-8", errors="replace")
        blocks[key] = "\n".join(s for s in (line.strip() for line in body.splitlines())
                                if s and not s.startswith(DROPPED))
        queue.extend(_refs(body))
    return "\n".join(colours + [f"0 FILE {name}\n{body}" for name, body in blocks.items()]) + "\n"
