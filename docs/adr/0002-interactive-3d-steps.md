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

- **Library.** The manual's 3D view uses three.js 0.170.0 and these add-ons: `LDrawLoader`, `LDrawConditionalLineMaterial`, `OrbitControls`, `LineSegments2`, `LineSegmentsGeometry` and `LineMaterial`. 0.170.0 is the last release whose `three.module.min.js` is a single file.
- **Vendored, not from a CDN.** Those files are committed unmodified under `src/lego_creator/site_assets/vendor/three/` with the three.js license, and `lc site` copies them into `assets/vendor/three/`. The page loads them through an import map. Nothing is fetched from another origin, so the service worker can cache them and the manual keeps working offline. Upgrading three.js means replacing these files and this ADR's version.
- **Model data.** For each manual, `lc` writes `model3d.txt`: the LDConfig colours, every submodel of the model, and every library and custom file they reference, each as a `0 FILE` block under the name `LDrawLoader` looks it up by. The site therefore redistributes the subset of the LDraw library that its models use (CC BY 4.0); the manual credits it.
- **Enhancement, not replacement.** LeoCAD step images (ADR 0001) stay. They are the PDF, the gallery and tray pictures, and what the page shows without JavaScript, WebGL or import maps. When the 3D view starts, it replaces the step image on screen with a stage the child can turn. The page tells the script which parts each step shows and which are new, so the Python step plan stays the single source of step contents.

## Consequences

- The repository carries about 800 KB of third-party JavaScript, reviewed only on upgrade.
- A manual's first load grows by the three.js files (shared by all manuals, cached) and its `model3d.txt`, whose size follows the number of distinct parts, not the number of placed parts. Electronic parts such as the hub and motors are the largest.
- The 3D view always drops new parts in from above; it does not know the real insertion direction. The view is not checked in CI, because CI has no browser; changes to it need a manual check in a browser.
- Browsers without import maps (Safari before 16.4) silently keep the images.
