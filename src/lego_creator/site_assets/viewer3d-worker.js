// Brick Steps 3D step view, model worker (ADR 0002): parses LDraw off the page's thread, so the page never stalls.
// The page sends {type: "open", url} once, then {type: "want", subs} with the submodels it needs most first.
// The worker answers {type: "colours", text} once, then {type: "section", sub, root, geometries, ball} per submodel,
// or {type: "failed", sub, message}. A geometry travels once; later sections refer to it by id.
// Materials stay behind: each drawable carries the LDraw colour code its material was made from, and the page
// makes the same materials from the colour lines.
import { Box3, LineBasicMaterial, Sphere } from "./vendor/three-0.187.0/three.module.js";
import { LDrawLoader } from "./vendor/three-0.187.0/worker/LDrawLoader.js";

let packed = null;
let loader = null;
let queue = [];
const done = new Set();
const geometryIds = new WeakMap();
let nextGeometry = 0;
let running = false;

// Direct colours (0x2RRGGBB) are made on the fly and named after their value; the rest carry their code.
function colourCode(material) {
  const direct = /^Direct_Color_([0-9A-Fa-f]{6})/.exec(material.name);
  return direct ? "0x2" + direct[1] : material.userData.code ?? null;
}

function pack(root) {
  const geometries = [];
  const transfer = [];
  function geometry(g) {
    if (!geometryIds.has(g)) {
      const id = nextGeometry++;
      geometryIds.set(g, id);
      const attributes = {};
      for (const [name, a] of Object.entries(g.attributes)) {
        const array = a.array.slice(); // the worker keeps its copy: cached parts reuse it in later sections
        attributes[name] = { array, itemSize: a.itemSize, normalized: a.normalized };
        transfer.push(array.buffer);
      }
      const index = g.index ? g.index.array.slice() : null;
      if (index) transfer.push(index.buffer);
      geometries.push({ id, attributes, index, groups: g.groups });
    }
    return geometryIds.get(g);
  }
  function node(o) {
    const kind = o.isMesh ? "mesh" : o.isConditionalLine ? "conditional" : o.isLineSegments ? "line" : "group";
    const out = { kind, matrix: o.matrix.toArray(), children: o.children.map(node) };
    if (kind !== "group") {
      out.geometry = geometry(o.geometry);
      out.colour = Array.isArray(o.material) ? o.material.map(colourCode) : colourCode(o.material);
    }
    return out;
  }
  return { root: node(root), geometries, transfer };
}

function parse(sub) {
  return new Promise((resolve, reject) => {
    loader.parse("1 16 0 0 0 1 0 0 0 1 0 0 0 1 " + sub + "\n" + packed, resolve, reject);
  });
}

async function run() {
  if (running || !loader) return;
  running = true;
  while (queue.length) {
    const sub = queue.shift();
    if (done.has(sub)) continue;
    done.add(sub);
    try {
      const root = await parse(sub);
      root.rotation.x = Math.PI; // LDraw -Y is up
      root.updateMatrixWorld(true);
      const ball = new Box3().setFromObject(root).getBoundingSphere(new Sphere());
      const { root: tree, geometries, transfer } = pack(root);
      self.postMessage({ type: "section", sub, root: tree, geometries, ball: { center: ball.center.toArray(), radius: ball.radius } },
        transfer);
    } catch (err) {
      self.postMessage({ type: "failed", sub, message: String(err) });
    }
    // Let a "want" that arrived meanwhile reorder the queue before the next section.
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  running = false;
}

self.addEventListener("message", async (event) => {
  const msg = event.data;
  if (msg.type === "open") {
    try {
      const res = await fetch(msg.url);
      if (!res.ok) throw new Error(res.status + " " + msg.url);
      packed = await res.text();
    } catch (err) {
      self.postMessage({ type: "failed", sub: null, message: String(err) });
      return;
    }
    self.postMessage({ type: "colours", text: packed.split("\n").filter((l) => l.startsWith("0 !COLOUR")).join("\n") });
    loader = new LDrawLoader();
    // Conditional edges need a material class; the page makes the real ones, so a plain line material will do here.
    loader.setConditionalLineMaterial(LineBasicMaterial);
    run();
  } else if (msg.type === "want") {
    queue = [...msg.subs.filter((s) => !done.has(s)), ...queue.filter((s) => !msg.subs.includes(s))];
    run();
  }
});
