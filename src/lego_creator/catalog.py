"""The model catalog: series and numbers, revisions, and how models relate (model.yaml).

A model's slug is `<series>-<number>` ("tank-1", shown to children as "탱크 1호"). The number
counts models within a series and never changes. Improving the same model adds a revision;
a new model in the series gets the next number and may record what it was `based_on`.
"""

from __future__ import annotations

import re

from .report import Issue

PORT_RE = re.compile(r"\bPort\.([A-F])\b")


def model_slug(series: str, number: int) -> str:
    return f"{series}-{number}"


def next_number(metas: dict[str, dict], series: str) -> int:
    return max((int(m.get("number", 0)) for m in metas.values() if m.get("series") == series), default=0) + 1


def new_meta(name: str, series: str, number: int, kits: dict[str, int], today: str, based_on: str | None = None) -> dict:
    meta = {"name": name, "series": series, "number": number}
    if based_on:
        meta["based_on"] = based_on
    meta |= {"kits": kits, "status": "draft", "version": 1, "created": today,
             "revisions": [{"version": 1, "date": today, "note": "First draft"}]}
    return meta


def revise(meta: dict, note: str, today: str) -> dict:
    """A copy of meta with the next revision appended."""
    version = int(meta.get("version", 0)) + 1
    return {**meta, "version": version,
            "revisions": [*meta.get("revisions", []), {"version": version, "date": today, "note": note}]}


def updated(meta: dict) -> str:
    """Date of the latest revision, or the creation date."""
    revisions = meta.get("revisions") or []
    return str(revisions[-1]["date"]) if revisions else str(meta.get("created", ""))


def check_catalog(slug: str, metas: dict[str, dict]) -> list[Issue]:
    meta = metas[slug]
    issues: list[Issue] = []
    if "series" in meta or "number" in meta:
        expected = model_slug(str(meta.get("series")), meta.get("number"))
        if slug != expected:
            issues.append(Issue("error", "slug-mismatch", f"folder is {slug} but series and number give {expected}"))
    revisions = meta.get("revisions")
    if revisions and revisions[-1].get("version") != meta.get("version"):
        issues.append(Issue("error", "revision-mismatch",
                            f"version is {meta.get('version')} but the last revision is {revisions[-1].get('version')}"))
    seen = {slug}
    base = meta.get("based_on")
    while base:
        if base not in metas:
            issues.append(Issue("error", "based-on-missing", f"based_on {base} is not a model"))
            break
        if base in seen:
            issues.append(Issue("error", "based-on-cycle", f"based_on chain returns to {base}"))
            break
        seen.add(base)
        base = metas[base].get("based_on")
    return issues


def program_ports(text: str) -> set[str]:
    """Hub ports a Pybricks program uses, ignoring comments."""
    return {m for line in text.splitlines() for m in PORT_RE.findall(line.split("#", 1)[0])}


def check_programs(programs: dict[str, str], declared: set[str]) -> list[Issue]:
    issues = []
    for name, text in sorted(programs.items()):
        extra = sorted(program_ports(text) - declared)
        if extra:
            issues.append(Issue("error", "program-port-undeclared",
                                f"{name} uses port {', '.join(extra)} without a `0 !LC PORT` line in the model"))
    return issues
