"""Downloads into the local cache."""


def test_download_sends_a_tool_user_agent(tmp_path, monkeypatch):
    # library.ldraw.org answers 403 to urllib's default "Python-urllib/x.y" agent.
    import io
    import urllib.request

    from lego_creator import fetch

    seen = {}

    def fake_urlopen(req, *a, **k):
        seen["ua"] = req.get_header("User-agent")
        return io.BytesIO(b"payload")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    out = fetch.download("https://example.invalid/x.zip", tmp_path / "x.zip")
    assert out.read_bytes() == b"payload"
    assert seen["ua"] and seen["ua"].startswith("brick-steps/") and "Python-urllib" not in seen["ua"]
