import tomllib
from pathlib import Path

from lego_creator.release import check_release, release_notes, released_versions

ROOT = Path(__file__).resolve().parents[1]

CHANGELOG = """# Changelog

## [Unreleased]

### Added
- Something new

## [0.0.2] - 2026-12-01

### Fixed
- A bug

## [0.0.1] - 2026-11-22

### Added
- First release

[Unreleased]: https://example.invalid/compare/v0.0.2...HEAD
"""


def test_released_versions_newest_first_without_unreleased():
    assert released_versions(CHANGELOG) == ["0.0.2", "0.0.1"]


def test_release_notes_is_the_section_body():
    assert release_notes(CHANGELOG, "0.0.2") == "### Fixed\n- A bug"
    assert release_notes(CHANGELOG, "0.0.1") == "### Added\n- First release"


def test_check_release_accepts_matching_tag_version_and_changelog():
    assert check_release("v0.0.2", "0.0.2", CHANGELOG) == []


def test_check_release_reports_each_mismatch():
    problems = check_release("v0.0.3", "0.0.2", CHANGELOG)
    assert any("pyproject" in p for p in problems) and any("CHANGELOG" in p for p in problems)
    assert check_release("0.0.2", "0.0.2", CHANGELOG) != []  # tag must start with v


def test_repository_version_matches_latest_changelog_release():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    released = released_versions((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    if released:
        assert project == released[0]
