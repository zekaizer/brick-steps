"""Downloads into the local cache (.cache/), shared by the commands that fetch outside data."""

from __future__ import annotations

import shutil
import urllib.request
from pathlib import Path

# library.ldraw.org rejects urllib's default agent with 403; identify the tool instead (no personal data).
USER_AGENT = "brick-steps/0 (+https://github.com/zekaizer/brick-steps)"


def download(url: str, dest: Path) -> Path:
    """dest, downloaded from url unless it is already there."""
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {url}")
        tmp = dest.with_suffix(dest.suffix + ".part")
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as resp, tmp.open("wb") as f:
            shutil.copyfileobj(resp, f)
        tmp.rename(dest)
    return dest
