/* Play surface frontend. Talks to the local server, shows a cookbook gallery,
   renders author-named sliders, and shades a three.js sphere with the returned
   PBR maps. Rotate: drag the viewport. Slider release triggers a small render. */
"use strict";

let current = null;      // {name, sliders}
let values = {};         // slider id (e.g. "dune_ripples/param0") -> value
let debounceTimer = null;
let generation = 0;
let completedPreview = null;
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
  // ResizeObserver on the container fires on any size change (window resize,
  // sidebar layout shifts), unlike window "resize" which the canvas could
  // outgrow when a stale pixel width pinned the flex viewport open.
  const fit = () => {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  };
  new ResizeObserver(fit).observe(el);
  (function loop() {
    requestAnimationFrame(loop);
    sphere.rotation.y = yaw; sphere.rotation.x = pitch;
    renderer.render(scene, camera);
  })();
}

function applyMaps(maps, previewId) {
  if (!sphere) return;  // 3D preview unavailable (e.g. no WebGL); nothing to shade
  // maps: array of basenames like play_albedo.png. Match by suffix.
  // Real render output has no separate roughness map (roughness is packed
  // into the ORM map), so the roughness lookup falls back to "orm".
  const tex = suffix => {
    const m = maps.find(x => x.includes(suffix));
    if (!m) return null;
    const t = new THREE.TextureLoader().load("/api/maps/" + encodeURIComponent(m)
      + "?preview_id=" + encodeURIComponent(previewId));
    return t;
  };
  const mat = sphere.material;
  const previous = new Set([mat.map, mat.normalMap, mat.roughnessMap, mat.bumpMap]);
  mat.map = tex("albedo");
  mat.normalMap = tex("normal");
  mat.roughnessMap = tex("roughness") || tex("orm");
  const h = tex("heightmap") || tex("height");
  mat.bumpMap = h; mat.bumpScale = h ? 0.15 : 0;
  previous.forEach(t => { if (t) t.dispose(); });
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
  invalidatePreview();
  const version = generation;
  current = null;
  document.getElementById("controls").hidden = true;
  let out;
  try { out = await j("/api/material/" + encodeURIComponent(name)); }
  catch (e) {
    if (version === generation) setStatus("material request failed: " + e.message);
    return;
  }
  if (version !== generation) return;
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
    inp.oninput = () => { values[s.id] = parseFloat(inp.value); invalidatePreview(); };
    inp.onchange = () => scheduleRender(256);
    row.appendChild(inp); box.appendChild(row);
  });
  scheduleRender(256);
}

function invalidatePreview() {
  clearTimeout(debounceTimer);
  generation += 1;
  completedPreview = null;
  document.getElementById("download").disabled = true;
}

function scheduleRender(size) {
  invalidatePreview();
  debounceTimer = setTimeout(() => doRender(size), 200);
}

async function doRender(size) {
  if (!current) return;
  invalidatePreview();
  const version = generation;
  setStatus("rendering...");
  let out;
  try {
    out = await j("/api/render", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ material_id: current.name, values, size })
    });
  } catch (e) {
    if (version !== generation) return;
    // The request itself failed (server crashed the connection, network error).
    // Surface it instead of leaving the status stuck on "rendering..." forever.
    setStatus("render request failed: " + (e && e.message ? e.message : e));
    return;
  }
  if (version !== generation) return;
  if (!out.ok) { setStatus("render failed: " + out.error); return; }
  applyMaps(out.maps, out.preview_id);
  completedPreview = out.preview_id;
  document.getElementById("download").disabled = false;
  setStatus(out.path === "live" ? "live" : "ready");
}

function setStatus(t) { document.getElementById("status").textContent = t; }

document.getElementById("full").onclick = () => doRender(1024);
document.getElementById("download").onclick = () => {
  if (completedPreview) window.location = "/api/export?preview_id=" + encodeURIComponent(completedPreview);
};
invalidatePreview();

// A 3D-preview init failure (e.g. no WebGL context) must not blank the whole
// page: surface it and still load the gallery so the sliders remain usable.
try { initThree(); }
catch (e) { setStatus("3D preview unavailable: " + (e && e.message ? e.message : e)); }
loadGallery();
