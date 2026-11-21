// Brick Steps 3D step view (ADR 0002): replaces the step picture with a model the child can turn.
// The page stays usable without it: on any failure the rendered pictures remain.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { LDrawLoader } from "three/addons/loaders/LDrawLoader.js";
import { LDrawConditionalLineMaterial } from "three/addons/materials/LDrawConditionalLineMaterial.js";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";

const DROP_MS = 600;
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
    '<p class="hint t-caption">손가락으로 돌려 보세요</p>' +
    '<div class="tools"><button type="button" class="replay t-button">다시 보기</button>' +
    '<button type="button" class="home t-button">처음 방향</button></div>';
  return stage;
}

function start(packed) {
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

  const loader = new LDrawLoader();
  loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
  const outline = new LineMaterial({ color: yellow, linewidth: 2 });
  const glow = new Map();
  const sections = new Map();
  let section = null, drop = null, queued = false, shownCard = null, cableGroup = null;

  function draw() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(tick);
  }
  function tick(now) {
    queued = false;
    if (drop) {
      if (drop.t0 === null) drop.t0 = now;
      const k = Math.min(1, (now - drop.t0) / DROP_MS), left = Math.pow(1 - k, 3);
      for (const p of drop.parts) p.group.position.copy(p.base).y -= left * drop.height; // LDraw -Y is up
      if (k === 1) drop = null; else draw();
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
    part.outline.visible = fresh;
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

  // One submodel, parsed once: its placed references in file order, which is the order the page counts in.
  function load(sub) {
    if (!sections.has(sub)) {
      sections.set(sub, new Promise((resolve, reject) => {
        loader.parse("1 16 0 0 0 1 0 0 0 1 0 0 0 1 " + sub + "\n" + packed, resolve, reject);
      }).then((root) => {
        root.rotation.x = Math.PI; // LDraw -Y is up
        root.updateMatrixWorld(true);
        const model = root.children.find((c) => c.isGroup);
        const parts = model.children.filter((c) => c.isGroup).map((group) => {
          const meshes = [];
          const edges = [];
          group.traverse((o) => {
            if (o.isMesh) meshes.push({ object: o, material: o.material });
            else if (o.isLineSegments) edges.push({ object: o, material: o.material });
          });
          return { group, base: group.position.clone(), meshes, edges, outline: buildOutline(group) };
        });
        const ball = new THREE.Box3().setFromObject(root).getBoundingSphere(new THREE.Sphere());
        const distance = ball.radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.05;
        return { root, parts, ball, distance };
      }));
    }
    return sections.get(sub);
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

  // Cables in LDraw units, from each device to its hub port, each in its port's color. The line
  // leaves the device sideways, runs up outside the hub's side and ends straight in the port with a
  // plug, so the hub never hides it. Not the real cable route; the motor end has no plug because
  // SPIKE motor cables do not come off.
  function drawCables(list) {
    cableGroup = new THREE.Group();
    for (const c of list) {
      if (!c.to) continue;
      const color = token(`--port-${c.port.toLowerCase()}`) || token("--ink");
      const material = new THREE.MeshStandardMaterial({ color, roughness: 0.6 });
      const from = new THREE.Vector3(...c.from), to = new THREE.Vector3(...c.to);
      const out = new THREE.Vector3(...c.out);
      const side = to.clone().addScaledVector(out, 50);
      const reach = side.clone().sub(from).dot(out);  // how far to go out to clear the hub's side
      const besideDevice = from.clone().addScaledVector(out, reach);
      const curve = new THREE.CatmullRomCurve3(
        [from, besideDevice, besideDevice.clone().lerp(side, 0.5), side, to.clone().addScaledVector(out, 22)],
        false, "centripetal");
      cableGroup.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 64, 4, 8), material));
      const plug = new THREE.Mesh(new THREE.BoxGeometry(22, 14, 18), material);
      plug.position.copy(to).addScaledVector(out, 11);
      plug.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), out);
      cableGroup.add(plug);
      const label = portLabel(c.port, color);
      label.position.copy(to).addScaledVector(out, 70);
      cableGroup.add(label);
    }
    section.root.add(cableGroup);
  }

  function apply(figure, animate) {
    const shown = Number(figure.dataset.shown), fresh = Number(figure.dataset.fresh);
    drop = null;
    clearCables();
    const cables = figure.dataset.cables ? JSON.parse(figure.dataset.cables) : null;
    const keep = cables ? new Set(JSON.parse(figure.dataset.keep || "[]")) : null;
    if (cables) drawCables(cables);
    section.parts.forEach((p, i) => {
      p.group.position.copy(p.base);
      p.group.visible = i < shown;
      setFaded(p, false);
      setFresh(p, i < shown && i >= shown - fresh);
      if (keep && !keep.has(i)) setFaded(p, true);
    });
    if (fresh && animate && !calm) {
      drop = { parts: section.parts.slice(shown - fresh, shown), t0: null, height: section.ball.radius * 0.9 };
    }
    controls.autoRotate = !fresh && !cables && !calm; // the finished model turns until touched
    replay.hidden = !fresh || calm;
    draw();
  }

  function show(card, animate) {
    shownCard = card;
    const figure = card.querySelector("figure[data-sub]");
    if (!figure) {
      controls.autoRotate = false;
      return;
    }
    load(figure.dataset.sub).then((next) => {
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
      console.error(err);
      sections.delete(figure.dataset.sub);
    });
  }

  replay.addEventListener("click", () => apply(stage.parentElement, true));
  stage.querySelector(".home").addEventListener("click", goHome);
  document.addEventListener("brick-steps:show", (e) => show(e.detail.card, e.detail.dir > 0));
  const current = deck.querySelector(".card.on");
  if (current) show(current, true);
}

if (deck && source) {
  fetch(source)
    .then((res) => { if (!res.ok) throw new Error(res.status + " " + source); return res.text(); })
    .then(start)
    .catch((err) => console.error(err));
}
