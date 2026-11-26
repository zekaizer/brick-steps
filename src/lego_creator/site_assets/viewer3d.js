// Brick Steps 3D step view (ADR 0002): replaces the step picture with a model the child can turn.
// The page stays usable without it: on any failure the rendered pictures remain.
// The page's thread never parses LDraw: viewer3d-worker.js does, and the page assembles what it sends in slices
// of a few milliseconds, so taps and scrolling are never held up. Until a section is ready its picture stays,
// with a pill saying the 3D view is on its way.
// A step figure's data-moves (site.py, from insertion.moves) says how each new part comes in: entry k is
// section.parts[shown - fresh + k], which starts at base + from * travel (LDraw axes of its submodel) and moves to
// base in its wave; an entry with `at` gets an arrow whose tip is there.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { LDrawLoader } from "three/addons/loaders/LDrawLoader.js";
import { LDrawConditionalLineMaterial } from "three/addons/materials/LDrawConditionalLineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";

const DROP_MS = 600;
const WAVE_MS = 450; // a wave of new parts starts this long after the wave before it
const ARROW_LENGTH = [0.12, 0.25]; // clamp(travel, 0.12 R, 0.25 R), R the section's radius
const SLICE_MS = 8; // longest stretch the page's thread works before letting the browser draw
const PLUG_TRAVEL = 50; // LDU a cable slides into its port when the cable card opens
const VIEW_DIR = new THREE.Vector3(-1, 0.85, 1).normalize(); // front-left, from above
const deck = document.getElementById("deck");
const source = document.body.dataset.model3d;

function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function buildStage() {
  const stage = document.createElement("div");
  stage.className = "stage3d";
  stage.innerHTML =
    '<canvas aria-label="돌려 볼 수 있는 3D 조립 그림"></canvas>' +
    '<p class="hint t-body">손가락으로 돌려 보세요</p>' +
    '<div class="tools"><button type="button" class="replay t-button">다시 보기</button>' +
    '<button type="button" class="home t-button">처음 방향</button></div>';
  return stage;
}

function start(worker) {
  const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const yellow = token("--yellow");
  const stage = buildStage();
  const canvas = stage.querySelector("canvas");
  const replay = stage.querySelector(".replay");

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); // throws without WebGL
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(token("--paper"));
  const scene = new THREE.Scene();
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  sun.position.set(-1, 2, 1.5);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa8ae, 2.4), sun);
  const camera = new THREE.PerspectiveCamera(30, 4 / 3, 1, 10000);
  const controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.rotateSpeed = 0.8;
  controls.autoRotateSpeed = 3;

  // Materials only: made from the colour lines the worker sends, then looked up by each drawable's colour code.
  const loader = new LDrawLoader();
  loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
  let materialsReady = null;
  const geometries = new Map();
  const directs = new Map();
  const outline = new LineMaterial({ color: yellow, linewidth: 2 });
  // Arrows are drawn over the model, like the port letters, so one on the far side still shows.
  const arrowFill = new THREE.MeshBasicMaterial({ color: yellow, depthTest: false });
  const arrowEdge = new LineMaterial({ color: token("--ink"), linewidth: 2, depthTest: false });
  const glow = new Map();
  let section = null, arrive = null, plugIn = null, queued = false, shownCard = null, cableGroup = null, arrows = null;

  function draw() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(tick);
  }
  function tick(now) {
    queued = false;
    if (plugIn) {
      if (plugIn.t0 === null) plugIn.t0 = now;
      const k = Math.min(1, (now - plugIn.t0) / DROP_MS), left = Math.pow(1 - k, 3);
      for (const c of plugIn.cables) c.group.position.copy(c.out).multiplyScalar(left * PLUG_TRAVEL);
      if (k === 1) plugIn = null; else draw();
    }
    if (arrive) {
      if (arrive.t0 === null) arrive.t0 = now;
      let moving = false;
      for (const p of arrive.parts) {
        // Parts of a later wave wait at their start, glowing, until their wave goes.
        const k = Math.min(1, Math.max(0, (now - arrive.t0 - p.delay) / DROP_MS));
        if (k < 1) moving = true;
        p.part.group.position.copy(p.part.base).addScaledVector(p.from, Math.pow(1 - k, 3) * p.travel);
      }
      if (moving) {
        draw();
      } else {
        showArrows(arrive.marks);
        arrive = null;
      }
    }
    if (controls.autoRotate) { controls.update(); draw(); }
    renderer.render(scene, camera);
  }
  function resize() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    draw();
  }
  new ResizeObserver(resize).observe(canvas);
  controls.addEventListener("change", draw);
  controls.addEventListener("start", () => {
    controls.autoRotate = false;
    stage.querySelector(".hint").classList.add("gone");
  });

  function glowing(material) {
    if (!glow.has(material)) {
      const m = material.clone();
      m.emissive = new THREE.Color(yellow);
      m.emissiveIntensity = 0.35;
      glow.set(material, m);
    }
    return glow.get(material);
  }
  const faded = new Map();
  function fading(material) {
    if (!faded.has(material)) {
      const m = material.clone();
      m.transparent = true;
      m.opacity = 0.18;
      m.depthWrite = false;
      faded.set(material, m);
    }
    return faded.get(material);
  }
  // Parts that are not part of the cable step fade, so the cables stay in sight.
  function setFaded(part, fade) {
    for (const list of [part.meshes, part.edges]) {
      for (const m of list) {
        m.object.material = !fade ? m.material : Array.isArray(m.material) ? m.material.map(fading) : fading(m.material);
      }
    }
  }

  function setFresh(part, fresh) {
    if (fresh && !part.outline) part.outline = buildOutline(part.group);
    if (part.outline) part.outline.visible = fresh;
    for (const m of part.meshes) {
      m.object.material = !fresh ? m.material : Array.isArray(m.material) ? m.material.map(glowing) : glowing(m.material);
    }
  }
  // A thick outline for one placed part or sub-assembly, built from its own edge lines.
  function buildOutline(group) {
    const inverse = group.matrixWorld.clone().invert(), v = new THREE.Vector3(), points = [];
    group.traverse((o) => {
      if (!o.isLineSegments || o.isConditionalLine) return;
      const pos = o.geometry.getAttribute("position"), index = o.geometry.getIndex();
      const m = new THREE.Matrix4().multiplyMatrices(inverse, o.matrixWorld);
      for (let i = 0, n = index ? index.count : pos.count; i < n; i++) {
        v.fromBufferAttribute(pos, index ? index.getX(i) : i).applyMatrix4(m);
        points.push(v.x, v.y, v.z);
      }
    });
    const line = new LineSegments2(new LineSegmentsGeometry().setPositions(points), outline);
    line.visible = false;
    group.add(line);
    return line;
  }

  let sliceStart = performance.now();
  async function breathe() {
    if (performance.now() - sliceStart > SLICE_MS) {
      await new Promise((resolve) => setTimeout(resolve, 0));
      sliceStart = performance.now();
    }
  }

  function faceMaterial(code) {
    if (code === null) return loader.missingColorMaterial;
    if (code.startsWith("0x2")) {
      if (!directs.has(code)) directs.set(code, loader.getMaterial(code));
      return directs.get(code);
    }
    return loader.getMaterial(code) || loader.missingColorMaterial;
  }
  function material(kind, code) {
    const face = faceMaterial(code);
    if (kind === "mesh") return face;
    const edge = loader.edgeMaterialCache.get(face);
    return kind === "line" ? edge : loader.conditionalEdgeMaterialCache.get(edge);
  }
  function make(node) {
    let o;
    if (node.kind === "group") {
      o = new THREE.Group();
    } else {
      const geometry = geometries.get(node.geometry);
      const mat = Array.isArray(node.colour) ? node.colour.map((c) => material(node.kind, c)) : material(node.kind, node.colour);
      o = node.kind === "mesh" ? new THREE.Mesh(geometry, mat) : new THREE.LineSegments(geometry, mat);
      if (node.kind === "conditional") o.isConditionalLine = true;
    }
    o.matrix.fromArray(node.matrix);
    o.matrix.decompose(o.position, o.quaternion, o.scale);
    return o;
  }

  // One submodel as the worker sent it: its placed references in file order, which is the order the page counts in.
  async function assemble(msg) {
    await materialsReady;
    for (const g of msg.geometries) {
      const geometry = new THREE.BufferGeometry();
      for (const [name, a] of Object.entries(g.attributes)) {
        geometry.setAttribute(name, new THREE.BufferAttribute(a.array, a.itemSize, a.normalized));
      }
      if (g.index) geometry.setIndex(new THREE.BufferAttribute(g.index, 1));
      for (const group of g.groups) geometry.addGroup(group.start, group.count, group.materialIndex);
      geometries.set(g.id, geometry);
    }
    sliceStart = performance.now();
    const root = make(msg.root);
    const stack = [[msg.root, root]];
    while (stack.length) {
      const [node, object] = stack.pop();
      for (const child of node.children) {
        const o = make(child);
        object.add(o);
        stack.push([child, o]);
      }
      await breathe();
    }
    root.updateMatrixWorld(true);
    const model = root.children.find((c) => c.isGroup); // its frame is the submodel's LDraw axes
    const parts = [];
    for (const group of model.children.filter((c) => c.isGroup)) {
      const meshes = [];
      const edges = [];
      group.traverse((o) => {
        if (o.isMesh) meshes.push({ object: o, material: o.material });
        else if (o.isLineSegments) edges.push({ object: o, material: o.material });
      });
      parts.push({ group, base: group.position.clone(), meshes, edges, outline: null });
      await breathe();
    }
    const ball = new THREE.Sphere(new THREE.Vector3().fromArray(msg.ball.center), msg.ball.radius);
    const distance = ball.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.05;
    await renderer.compileAsync(root, camera, scene); // shaders compile without holding the page where the GPU allows
    return { root, model, parts, ball, distance };
  }

  // Sections the worker is asked for, in the order the child is likely to need them.
  const sections = new Map();
  function load(sub) {
    if (!sections.has(sub)) {
      let settle;
      const promise = new Promise((resolve, reject) => { settle = { resolve, reject }; });
      promise.catch(() => {}); // a failure is handled where the section is shown
      sections.set(sub, { promise, settle, ready: false });
      worker.postMessage({ type: "want", subs: [sub] });
    }
    return sections.get(sub);
  }
  function fail(sub, message) {
    for (const [name, entry] of sections) {
      if (sub === null || name === sub) entry.settle.reject(new Error(message));
    }
  }
  worker.addEventListener("message", (event) => {
    const msg = event.data;
    if (msg.type === "colours") {
      materialsReady = loader.preloadMaterials(URL.createObjectURL(new Blob([msg.text], { type: "text/plain" })));
    } else if (msg.type === "section") {
      const entry = load(msg.sub);
      assemble(msg).then((built) => { entry.ready = true; entry.settle.resolve(built); }, entry.settle.reject);
    } else if (msg.type === "failed") {
      fail(msg.sub, msg.message);
    }
  });
  worker.addEventListener("error", (event) => fail(null, event.message || "worker failed"));

  // The picture stays while the 3D view is made; the pill tells the child it is on its way.
  function waiting(figure, on) {
    let pill = figure.querySelector(".loading3d");
    if (on && !pill) {
      pill = document.createElement("p");
      pill.className = "loading3d t-body";
      pill.setAttribute("role", "status");
      pill.textContent = "곧 돌려 볼 수 있어요";
      figure.append(pill);
    } else if (!on && pill) {
      pill.remove();
    }
  }

  function goHome() {
    controls.target.copy(section.ball.center);
    camera.position.copy(section.ball.center).addScaledVector(VIEW_DIR, section.distance);
    controls.minDistance = section.distance * 0.5;
    controls.maxDistance = section.distance * 1.6;
    controls.update();
    draw();
  }

  // A round port letter that always faces the camera, like the letters printed on the hub.
  function portLabel(text, color) {
    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const g = c.getContext("2d");
    g.fillStyle = color;
    g.beginPath();
    g.arc(64, 64, 60, 0, Math.PI * 2);
    g.fill();
    g.fillStyle = token("--surface");
    g.font = "600 80px Lexend, sans-serif";
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillText(text, 64, 70);
    const map = new THREE.CanvasTexture(c);
    map.colorSpace = THREE.SRGBColorSpace;
    const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map, depthTest: false }));
    sprite.scale.set(30, 30, 1);
    sprite.renderOrder = 10;
    return sprite;
  }

  function clearCables() {
    if (!cableGroup) return;
    cableGroup.removeFromParent();
    cableGroup.traverse((o) => {
      o.geometry?.dispose();
      o.material?.map?.dispose();
      o.material?.dispose();
    });
    cableGroup = null;
  }

  // A flat ribbon along a curve: SPIKE cables are 6-wire ribbons, 18 LDU wide and about 4 thick.
  // The wide side starts flat at the port end (`wide`) and is carried along the curve without
  // twisting, so it enters the socket the way the real plug does.
  const RIBBON_WIDTH = 18, RIBBON_THICK = 4;
  function ribbon(curve, wide, samples = 80) {
    const points = curve.getSpacedPoints(samples).reverse();  // walk from the port end
    const positions = [], index = [];
    let w = wide.clone();
    for (let i = 0; i <= samples; i++) {
      const t = points[Math.min(i + 1, samples)].clone().sub(points[Math.max(i - 1, 0)]).normalize();
      w.addScaledVector(t, -w.dot(t)).normalize();
      const n = t.clone().cross(w).normalize();
      for (const [a, b] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
        const v = points[i].clone().addScaledVector(w, a * RIBBON_WIDTH / 2).addScaledVector(n, b * RIBBON_THICK / 2);
        positions.push(v.x, v.y, v.z);
      }
      if (i > 0) {
        const p0 = (i - 1) * 4, p1 = i * 4;
        for (let k = 0; k < 4; k++) {
          const k2 = (k + 1) % 4;
          index.push(p0 + k, p1 + k, p1 + k2, p0 + k, p1 + k2, p0 + k2);
        }
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(index);
    geometry.computeVertexNormals();
    return geometry;
  }

  // Cables in LDraw units, from each device to its hub port, each in its port's color. The ribbon
  // leaves the device sideways, runs up outside the hub's side and ends in a plug of the real size
  // (23816a: 34 x 18 x 34), so the hub never hides it. Not the real cable route; the motor end has
  // no plug because SPIKE motor cables do not come off.
  function drawCables(list) {
    cableGroup = new THREE.Group();
    const moving = [];
    const up = new THREE.Vector3(0, 1, 0);
    for (const c of list) {
      if (!c.to) continue;
      const color = token(`--port-${c.port.toLowerCase()}`) || token("--ink");
      const material = new THREE.MeshStandardMaterial({ color, roughness: 0.6, side: THREE.DoubleSide });
      const from = new THREE.Vector3(...c.from), to = new THREE.Vector3(...c.to);
      const out = new THREE.Vector3(...c.out);
      const wide = up.clone().cross(out).normalize();  // the socket is wide along the hub's length
      const side = to.clone().addScaledVector(out, 60);
      const reach = side.clone().sub(from).dot(out);  // how far to go out to clear the hub's side
      const besideDevice = from.clone().addScaledVector(out, reach);
      const curve = new THREE.CatmullRomCurve3(
        [from, besideDevice, besideDevice.clone().lerp(side, 0.5), side, to.clone().addScaledVector(out, 17)],
        false, "centripetal");
      const group = new THREE.Group();
      group.add(new THREE.Mesh(ribbon(curve, wide), material));
      const plug = new THREE.Mesh(new THREE.BoxGeometry(34, 18, 34), material);
      plug.position.copy(to);  // half of the plug sits inside the socket
      plug.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(out, up, out.clone().cross(up)));
      group.add(plug);
      cableGroup.add(group);
      moving.push({ group, out });
      const label = portLabel(c.port, color);
      label.position.copy(to).addScaledVector(out, 80);
      cableGroup.add(label);
    }
    section.root.add(cableGroup);
    return moving;
  }

  // A solid arrow with its tip at `at`, pointing along -from: the way the part went in.
  function arrowMesh(m) {
    const length = THREE.MathUtils.clamp(m.travel, ARROW_LENGTH[0] * section.ball.radius,
      ARROW_LENGTH[1] * section.ball.radius);
    const head = length * 0.35;
    const shaft = new THREE.CylinderGeometry(length * 0.06, length * 0.06, length - head, 16).translate(0, (length - head) / 2, 0);
    const cone = new THREE.ConeGeometry(length * 0.16, head, 24).translate(0, length - head / 2, 0);
    const group = new THREE.Group();
    for (const geometry of [shaft, cone]) {
      const fill = new THREE.Mesh(geometry, arrowFill);
      fill.renderOrder = 10;
      const edge = new LineSegments2(new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(geometry, 30)), arrowEdge);
      edge.renderOrder = 11;
      group.add(fill, edge);
    }
    const from = new THREE.Vector3(...m.from);
    group.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), from.clone().negate());
    group.position.fromArray(m.at).addScaledVector(from, length);
    return group;
  }
  function showArrows(marks) {
    if (!marks.length) return;
    arrows = new THREE.Group();
    for (const m of marks) arrows.add(arrowMesh(m));
    section.model.add(arrows);
  }
  function clearArrows() {
    if (!arrows) return;
    arrows.removeFromParent();
    arrows.traverse((o) => o.geometry?.dispose());
    arrows = null;
  }

  function apply(figure, animate) {
    const shown = Number(figure.dataset.shown), fresh = Number(figure.dataset.fresh);
    const moves = figure.dataset.moves ? JSON.parse(figure.dataset.moves) : [];
    arrive = null;
    plugIn = null;
    clearCables();
    clearArrows();
    const cables = figure.dataset.cables ? JSON.parse(figure.dataset.cables) : null;
    const keep = cables ? new Set(JSON.parse(figure.dataset.keep || "[]")) : null;
    if (cables) {
      const moving = drawCables(cables);
      // The cables slide in from outside, so the child sees which way the plug goes into the port.
      if (animate && !calm) plugIn = { cables: moving, t0: null };
    }
    section.parts.forEach((p, i) => {
      p.group.position.copy(p.base);
      p.group.visible = i < shown;
      setFaded(p, false);
      setFresh(p, i < shown && i >= shown - fresh);
      if (keep && !keep.has(i)) setFaded(p, true);
    });
    const marks = moves.filter((m) => m.at);
    if (moves.length && animate && !calm) {
      const parts = moves.map((m, k) => ({
        part: section.parts[shown - fresh + k], from: new THREE.Vector3(...m.from), travel: m.travel, delay: m.wave * WAVE_MS,
      }));
      arrive = { parts, marks, t0: null };
    } else {
      showArrows(marks); // going back or reduced motion: the arrows alone say how the parts went in
    }
    controls.autoRotate = !fresh && !cables && !calm; // the finished model turns until touched
    replay.hidden = (!fresh && !cables) || calm;
    draw();
  }

  function show(card, animate) {
    shownCard = card;
    const figure = card.querySelector("figure[data-sub]");
    if (!figure) {
      controls.autoRotate = false;
      return;
    }
    const entry = load(figure.dataset.sub);
    if (!entry.ready) {
      waiting(figure, true);
      worker.postMessage({ type: "want", subs: [figure.dataset.sub] });
    }
    entry.promise.then((next) => {
      waiting(figure, false);
      if (shownCard !== card) return;
      if (section !== next) {
        if (section) scene.remove(section.root);
        section = next;
        scene.add(section.root);
        goHome();
      }
      figure.classList.add("has-3d");
      figure.append(stage);
      resize();
      apply(figure, animate);
    }).catch((err) => {
      waiting(figure, false);
      console.error(err);
    });
  }

  replay.addEventListener("click", () => apply(stage.parentElement, true));
  stage.querySelector(".home").addEventListener("click", goHome);
  document.addEventListener("brick-steps:show", (e) => show(e.detail.card, e.detail.dir > 0));
  // Ask for the shown card first, then the finished model, then every section in page order.
  const current = deck.querySelector(".card.on");
  const subs = [...deck.querySelectorAll("figure[data-sub]")].map((f) => f.dataset.sub);
  const first = [current?.querySelector("figure[data-sub]")?.dataset.sub, document.querySelector("#done figure[data-sub]")?.dataset.sub];
  worker.postMessage({ type: "open", url: new URL(source, location.href).href });
  for (const sub of new Set([...first.filter(Boolean), ...subs])) load(sub);
  if (current) show(current, true);
}

if (deck && source) {
  let worker = null;
  try {
    worker = new Worker(new URL("viewer3d-worker.js", import.meta.url), { type: "module" });
    start(worker);
  } catch (err) {
    worker?.terminate(); // no worker or no WebGL: the pictures stay
    console.error(err);
  }
}
