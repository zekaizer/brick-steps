"""Compile the synced Brick Steps design tokens (design/brick-steps.tokens.json) into CSS."""

from __future__ import annotations

TYPE_PROPS = (("fontSize", "font-size"), ("lineHeight", "line-height"), ("fontWeight", "font-weight"), ("letterSpacing", "letter-spacing"))


def _first_theme_value(value: object, theme: str | None) -> str:
    if isinstance(value, dict):
        return str(value.get(theme) if theme in value else next(iter(value.values())))
    return str(value)


def tokens_css(tokens: dict) -> str:
    """CSS custom properties for every token, plus a `.t-<style>` class per type style.

    Only the first color theme is emitted: the site is single-theme by design.
    """
    lines = [":root {"]
    color = tokens.get("color", {})
    themes = color.get("themes") or [{}]
    first = themes[0].get("id")
    for tok in color.get("tokens", []):
        lines.append(f"  --{tok['name']}: {_first_theme_value(tok['value'], first)};")
    for family, body in tokens.items():
        if family in ("color", "type") or not isinstance(body, dict) or "tokens" not in body:
            continue
        for tok in body["tokens"]:
            lines.append(f"  --{tok['name']}: {tok['value']};")
    type_ = tokens.get("type", {})
    for key, stack in type_.get("families", {}).items():
        lines.append(f"  --font-{key}: {stack};")
    lines.append("}")

    for group in type_.get("groups", []):
        for style in group.get("styles", []):
            family = style.get("family", group.get("family"))
            lines.append(f".t-{style['name']} {{")
            if family:
                lines.append(f"  font-family: var(--font-{family});")
            for key, prop in TYPE_PROPS:
                if key in style:
                    lines.append(f"  {prop}: {style[key]};")
            lines.append("}")
    return "\n".join(lines) + "\n"
