"""Release helpers: CHANGELOG.md sections and version consistency (docs/releasing.md)."""

from __future__ import annotations

import re

HEADING = re.compile(r"^## \[(\d+\.\d+\.\d+)\][^\n]*$", re.MULTILINE)
TAG = re.compile(r"^v(\d+\.\d+\.\d+)$")


def released_versions(changelog: str) -> list[str]:
    """Released versions in file order (newest first by Keep a Changelog convention)."""
    return HEADING.findall(changelog)


def release_notes(changelog: str, version: str) -> str:
    """Body of the `## [version]` section, without its heading or the link references at the end."""
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n", changelog, re.MULTILINE)
    if m is None:
        return ""
    rest = changelog[m.end():]
    end = re.search(r"^(## |\[[^\]]+\]: )", rest, re.MULTILINE)
    return (rest[: end.start()] if end else rest).strip()


def check_release(tag: str, project_version: str, changelog: str) -> list[str]:
    """Problems that block releasing `tag`; empty when the tag, pyproject and CHANGELOG agree."""
    m = TAG.match(tag)
    if m is None:
        return [f"tag {tag!r} is not of the form vMAJOR.MINOR.PATCH"]
    version = m.group(1)
    problems = []
    if project_version != version:
        problems.append(f"pyproject version {project_version} does not match tag {tag}")
    released = released_versions(changelog)
    if version not in released:
        problems.append(f"CHANGELOG has no [{version}] section")
    elif released[0] != version:
        problems.append(f"CHANGELOG's newest release is {released[0]}, not {version}")
    return problems
