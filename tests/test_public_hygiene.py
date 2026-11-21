"""The repository is public: files that would be committed must not carry personal data or secrets."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = {
    "email address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "home directory path": re.compile(r"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "claude.ai artifact link": re.compile(r"claude\.ai/(?:code/)?artifact/[A-Za-z0-9-]+"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "token-like secret": re.compile(r"(?i)\b(?:api[_-]?key|secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"),
}
SKIP = {"uv.lock"}  # third-party package metadata


def _committable_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                         cwd=ROOT, capture_output=True, check=True).stdout
    return [ROOT / p for p in out.decode().split("\0") if p and p not in SKIP]


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="needs a git checkout")
def test_no_personal_data_or_secrets_in_committable_files():
    hits = []
    for path in _committable_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for label, pattern in FORBIDDEN.items():
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append(f"{path.relative_to(ROOT)}:{line}: {label}: {m.group(0)[:40]}")
    assert hits == []
