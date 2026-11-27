# 2. Interactive 3D steps: three.js LDrawLoader, vendored, on top of the rendered manual

Date: 2026-11-22

## Status

Accepted

## Context

A step image shows the model from one fixed angle. Children building on their own often cannot tell where a part goes when it is hidden behind others, and they cannot turn a picture around. A prototype showed that the same LDraw model can be drawn in the browser, step by step, and turned with a finger on an iPad mini.

The manual is still a static site on GitHub Pages that has to work offline once opened (ADR 0001), and the repository has no JavaScript toolchain. These options were considered:

- **Keep images only and render more angles.** It needs no new dependency, but the number of images multiplies and the child still cannot choose the angle.
- **A hand-written WebGL LDraw renderer.** It adds no dependency, but parsing LDraw correctly (BFC winding, conditional lines, colour inheritance) is a project of its own.
- **three.js with its `LDrawLoader` add-on.** It reads LDraw text directly, including files embedded as `0 FILE` blocks, and keeps each placed part as a separate object, which is what a step-by-step view needs. three.js is MIT licensed and has no dependencies. Its ES modules run in the browser unbundled when an import map resolves the `three` specifier.

## Decision

- **Library.** The manual's 3D view uses three.js 0.187.0 and these add-ons: `LDrawLoader`, `LDrawConditionalLineMaterial`, `OrbitControls`, `LineSegments2`, `LineSegmentsGeometry` and `LineMaterial`. 0.187.0 is the first release whose `LDrawLoader` smooths a large part in linear time: 0.170.0 took 8.6 s on the 19 x 11 frame, which held the page still. It ships no minified build, so `three.module.js` and the `three.core.js` it imports are vendored as published.
- **Vendored, not from a CDN.** Those files are committed unmodified under `src/lego_creator/site_assets/vendor/three-<version>/` with the three.js license, and `lc site` copies them into `assets/vendor/three-<version>/`. The version is in the path because the service worker keeps vendored files under their URL for good. The page loads them through an import map. Nothing is fetched from another origin, so the service worker can cache them and the manual keeps working offline. Upgrading three.js means replacing these files, the folder's version (`THREE_DIR` in `site.py` and the list in `sw.js`) and this ADR's version.
- **Off the page's thread.** The page never parses LDraw. A module worker (`viewer3d-worker.js`) does, section by section: the one shown first, then the finished model, then the rest in page order. It sends back transforms, geometry buffers (each once) and colour codes, and the page makes the materials from the same colour lines and builds the meshes a few milliseconds at a time. Until a section is ready its step picture stays, with a "곧 돌려 볼 수 있어요" pill. Workers have no import map, so `lc site` writes a copy of `LDrawLoader` whose one import from `three` names the vendored file; the vendored file stays as published.
- **Model data.** For each manual, `lc` writes `model3d.txt`: the LDConfig colours, every submodel of the model, and every library and custom file they reference, each as a `0 FILE` block under the name `LDrawLoader` looks it up by. The site therefore redistributes the subset of the LDraw library that its models use (CC BY 4.0); the manual credits it.
- **Enhancement, not replacement.** LeoCAD step images (ADR 0001) stay. They are the PDF, the gallery and tray pictures, and what the page shows without JavaScript, WebGL or import maps. When the 3D view starts, it replaces the step image on screen with a stage the child can turn. The page tells the script which parts each step shows and which are new, so the Python step plan stays the single source of step contents.

## Consequences

- The repository carries about 800 KB of third-party JavaScript, reviewed only on upgrade.
- A manual's first load grows by the three.js files (shared by all manuals, cached) and its `model3d.txt`, whose size follows the number of distinct parts, not the number of placed parts. Electronic parts such as the hub and motors are the largest.
- The 3D view brings each new part in from the side `src/lego_creator/insertion.py` works out from the part geometry at build time (pins along their own axis, parts onto pins or axles along them, anything else from the first clear side, from above first), wave by wave within a step, and shows a yellow arrow beside each part that does not come from above, from just before the part moves. The page receives this as `data-moves` on each step figure. The sides come from rays and hole walls, not from fingers, so they are guesses: `lc insertions` lists them for review and `0 !LC INSERT FROM <side>` in the model overrides a wrong one. The view is not checked in CI, because CI has no browser; changes to it need a manual check in a browser.
- Browsers without import maps (Safari before 16.4) silently keep the images.
