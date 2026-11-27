# 4. Fonts: self-hosted, cut down to the characters the site shows

Date: 2026-11-27

## Status

Accepted

## Context

The site names Noto Sans KR (body) and Lexend (display) in the Brick Steps design system and loaded them from Google Fonts with `display=optional`. `optional` keeps a font that arrives late from swapping in after the first paint, but the page then stays in the device's own font. Google Fonts splits Noto Sans KR into about a hundred slices, so a first visit often misses the short wait. The result differs by device: Apple SD Gothic Neo on the iPad, the vendor's font on an Android tablet.

The site's Korean text is small and known at build time: a few hundred distinct characters across every page.

## Decision

- **Source.** The build takes Noto Sans KR and Lexend as variable fonts from the google/fonts repository at a pinned commit, checks each file's SHA-256 and keeps them in `.cache/fonts/`. They are downloaded on first use and are not committed.
- **Subset at build time.** After the pages are written, `lc site` and `lc instructions` cut each font down with fontTools to printable ASCII plus every character in the pages, the PDF pages, the site's scripts and its stylesheet. The fonts are also cut down to the weights the design system uses (Noto Sans KR 400 to 700, Lexend 600 to 700). Each font becomes one WOFF2 file under `assets/fonts/`, named after a hash of its bytes, with its `@font-face` rule appended to `site.css`.
- **Symbols.** The arrows and the menu triangle of the mission blocks (↺ ↻ ▾) are in neither font. Noto Sans Math, from the same commit, is cut down to the characters Noto Sans KR lacks and declared under the name "Noto Sans KR" with `unicode-range`, so the type families need no new name.
- **Always the embedded font.** The rules use `font-display: block`: text waits for the font (at most about 3 s) instead of showing in a fallback, so every device shows the same letters. The family names in the design system tokens stay as they are.
- **Caching.** The service worker keeps the font files in its static cache, which survives deploys, and lists the current files in the stamped `sw.js`. A file whose hash is not in the list is removed, and so are other static files this build does not pin.
- **PDF.** The PDF is rendered after the fonts exist and embeds the same subset fonts.

## Consequences

- No request leaves the site for fonts, and the fonts work offline once cached.
- A character added in a later build gets into the font on that build. Text a script makes at run time from data outside the pages (none today) would fall back to the next font in the stack. The build warns about any character that none of the fonts has.
- A first visit shows no text until the fonts arrive (about 85 KB together today) instead of showing a fallback font.
- Builds need network access once to fill `.cache/fonts/`; CI caches the folder.
- Changing a family or weight in the design system also needs `SOURCES` in `src/lego_creator/fonts.py` changed.
