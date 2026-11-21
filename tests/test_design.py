import json
from pathlib import Path

from lego_creator.design import tokens_css

ROOT = Path(__file__).resolve().parents[1]

TOKENS = {
    "color": {"themes": [{"id": "light"}], "tokens": [{"name": "ink", "value": "#1f2a30"}, {"name": "duo", "value": {"light": "#fff", "dark": "#000"}}]},
    "type": {
        "families": {"display": "\"Jua\", sans-serif"},
        "groups": [{"name": "D", "family": "display", "styles": [{"name": "title", "fontSize": "32px", "lineHeight": "40px", "fontWeight": 400}, {"name": "num", "fontSize": "64px", "lineHeight": 1, "fontWeight": 400}]}],
    },
    "spacing": {"tokens": [{"name": "space-4", "value": "16px"}]},
    "size": {"tokens": [{"name": "tap-min", "value": "56px"}]},
}


def test_tokens_css_declares_custom_properties():
    css = tokens_css(TOKENS)
    for decl in ("--ink: #1f2a30;", "--duo: #fff;", "--space-4: 16px;", "--tap-min: 56px;", '--font-display: "Jua", sans-serif;'):
        assert decl in css


def test_tokens_css_emits_a_class_per_type_style():
    css = tokens_css(TOKENS)
    assert ".t-title {" in css and "font-size: 32px;" in css and "line-height: 40px;" in css
    assert "font-family: var(--font-display);" in css
    assert "line-height: 1;" in css


def test_synced_design_tokens_compile():
    tokens = json.loads((ROOT / "design" / "brick-steps.tokens.json").read_text(encoding="utf-8"))
    css = tokens_css(tokens)
    assert "--yellow: #f2cd37;" in css and ".t-step-number {" in css
