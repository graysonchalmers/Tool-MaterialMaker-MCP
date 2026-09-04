/* Play surface frontend. Talks to the local server, shows a cookbook gallery,
   renders author-named sliders, and shades a three.js sphere with the returned
   PBR maps. Rotate: drag the viewport. Slider release triggers a small render. */
"use strict";

let current = null;      // {name, sliders}
let values = {};         // slider id (e.g. "dune_ripples/param0") -> value
let debounceTimer = null;
let sphere = null, renderer = null, scene = null, camera = null;
let yaw = 0.6, pitch = 0.3, dragging = false, lastX = 0, lastY = 0;

async function j(url, opts) { const r = await fetch(url, opts); return r.json(); }

function initThree() {
  const el = document.getElementById("viewport");
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(el.clientWidth, el.clientHeight);
  el.appendChild(renderer.domElement);
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x15151a);
  camera = new THREE.PerspectiveCamera(45, el.clientWidth / el.clientHeight, 0.1, 100);
  camera.position.set(0, 0, 3.2);
  scene.add(new THREE.AmbientLight(0x404050, 1.2));
  const key = new THREE.DirectionalLight(0xffffff, 2.0);
  key.position.set(3, 3, 4); scene.add(key);
  const geo = new THREE.SphereGeometry(1, 96, 96);
  sphere = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.8 }));
  scene.add(sphere);
  el.addEventListener("mousedown", e => { dragging = true; lastX = e.clientX; lastY = e.clientY; });
  window.addEventListener("mouseup", () => dragging = false);
  window.addEventListener("mousemove", e => {
    if (!dragging) return;
    yaw += (e.clientX - lastX) * 0.01; pitch += (e.clientY - lastY) * 0.01;
    pitch = Math.max(-1.4, Math.min(1.4, pitch));
    lastX = e.clientX; lastY = e.clientY;
  });
  window.addEventListener("resize", () => {
    renderer.setSize(el.clientWidth, el.clientHeight);
    camera.aspect = el.clientWidth / el.clientHeight; camera.updateProjectionMatrix();
  });
  (function loop() {
    requestAnimationFrame(loop);
    sphere.rotation.y = yaw; sphere.rotation.x = pitch;
    renderer.render(scene, camera);
  })();
}

function applyMaps(maps) {
  // maps: array of basenames like play_albedo.png. Match by suffix.
  // Real render output has no separate roughness map (roughness is packed
  // into the ORM map), so the roughness lookup falls back to "orm".
  const tex = suffix => {
    const m = maps.find(x => x.includes(suffix));
    if (!m) return null;
    const t = new THREE.TextureLoader().load("/api/maps/" + m + "?t=" + Date.now());
    return t;
  };
  const mat = sphere.material;
  mat.map = tex("albedo") || mat.map;
  const n = tex("normal"); if (n) mat.normalMap = n;
  const orm = tex("orm"); const rough = tex("roughness");
  if (rough) mat.roughnessMap = rough; else if (orm) mat.roughnessMap = orm;
  const h = tex("heightmap") || tex("height");
  if (h) { mat.bumpMap = h; mat.bumpScale = 0.15; }
  mat.needsUpdate = true;
}

async function loadGallery() {
  const out = await j("/api/materials");
  const g = document.getElementById("gallery");
  g.innerHTML = "";
  let cat = null;
  out.materials.forEach(m => {
    if (m.category !== cat) { cat = m.category;
      const h = document.createElement("h2"); h.textContent = cat; g.appendChild(h); }
    const b = document.createElement("button");
    b.textContent = m.name; b.onclick = () => loadMaterial(m.name);
    g.appendChild(b);
  });
}

async function loadMaterial(name) {
  const out = await j("/api/material/" + encodeURIComponent(name));
  if (!out.ok) { setStatus(out.error); return; }
  current = out; values = {};
  document.getElementById("material-name").textContent = name;
  document.getElementById("controls").hidden = false;
  const box = document.getElementById("sliders"); box.innerHTML = "";
  let group = null;
  out.sliders.forEach(s => {
    if (s.kind === "color") return; // v1: skip color widgets
    // Key by the slider's unique id (e.g. "dune_ripples/param0"), not the
    // subgraph-local slot_id: slot_id collides across subgraphs, and the
    // server's render_request expects values keyed by id.
    values[s.id] = s.value;
    if (s.group !== group) { group = s.group;
      const h = document.createElement("h2"); h.textContent = group; box.appendChild(h); }
    const row = document.createElement("div"); row.className = "slider-row";
    const lab = document.createElement("label"); lab.textContent = s.label; row.appendChild(lab);
    const inp = document.createElement("input"); inp.type = "range";
    inp.min = s.min != null ? s.min : 0; inp.max = s.max != null ? s.max : 1;
    inp.step = s.step != null ? s.step : 0.01; inp.value = s.value;
    inp.oninput = () => { values[s.id] = parseFloat(inp.value); };
    inp.onchange = () => scheduleRender(256);
    row.appendChild(inp); box.appendChild(row);
  });
  scheduleRender(256);
}

function scheduleRender(size) {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => doRender(size), 200);
}

async function doRender(size) {
  if (!current) return;
  setStatus("rendering...");
  const out = await j("/api/render", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ material_id: current.name, values, size })
  });
  if (!out.ok) { setStatus("render failed: " + out.error); return; }
  applyMaps(out.maps);
  setStatus(out.path === "live" ? "live" : "ready");
}

function setStatus(t) { document.getElementById("status").textContent = t; }

document.getElementById("full").onclick = () => doRender(1024);
document.getElementById("download").onclick = () => {
  if (current) window.location = "/api/export?material_id=" + encodeURIComponent(current.name);
};

initThree();
loadGallery();
