"""Componentes interactivos (st.components.v2): globo 3D, barra de misión, KPI y tarjetas.

Solo presentación: reciben datos ya calculados por `mece` y devuelven eventos
(`select`, `analyze`) a Python. No contienen lógica de análisis.
"""

from __future__ import annotations

import streamlit as st

GLOBE_LIB = "https://cdn.jsdelivr.net/npm/globe.gl@2.46.2/dist/globe.gl.min.js"
IMG = "https://cdn.jsdelivr.net/npm/three-globe@2.45.6/example/img/"

# =============================================================== GLOBO 3D
_GLOBE_HTML = """
<div class="mg-root">
  <div class="mg-canvas"></div>
  <div class="mg-vignette"></div>
  <div class="mg-hud mg-tl">
    <div class="mg-eyebrow"><span class="mg-live"></span><span class="mg-t-layers"></span></div>
    <div class="mg-layers"></div>
  </div>
  <div class="mg-hud mg-tr">
    <button class="mg-btn" data-act="rotate" title=""><svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg></button>
    <button class="mg-btn" data-act="center" title=""><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/></svg></button>
    <button class="mg-btn" data-act="in" title="+"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg></button>
    <button class="mg-btn" data-act="out" title="−"><svg viewBox="0 0 24 24"><path d="M5 12h14"/></svg></button>
    <button class="mg-btn" data-act="full" title=""><svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button>
  </div>
  <div class="mg-hud mg-bl"><div class="mg-panel"><div class="mg-legend"></div>
    <div class="mg-readout"><span class="mg-coord">—</span><span class="mg-val"></span></div></div></div>
  <div class="mg-card"></div>
  <div class="mg-loading"><div class="mg-spinner"></div><span class="mg-t-loading"></span></div>
</div>
"""

_GLOBE_CSS = """
:host{all:initial}
.mg-root{position:relative;width:100%;height:var(--h,660px);border-radius:18px;overflow:hidden;
  background:radial-gradient(circle at 50% 45%,#0b1b3a 0%,#030712 70%);font-family:"IBM Plex Mono",ui-monospace,monospace;
  color:#e2e8f0;box-shadow:inset 0 0 0 1px rgba(56,189,248,.18),0 30px 80px -30px rgba(14,165,233,.45)}
.mg-root:fullscreen{border-radius:0}
.mg-canvas{position:absolute;inset:0}
.mg-vignette{position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse at center,transparent 55%,rgba(2,6,23,.75) 100%)}
.mg-hud{position:absolute;z-index:3;display:flex;gap:8px}
.mg-tl{top:16px;left:16px;flex-direction:column;align-items:flex-start}
.mg-tr{top:16px;right:16px;flex-direction:column}
.mg-bl{bottom:16px;left:16px}
.mg-br{bottom:16px;right:16px}
.mg-eyebrow{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:#7dd3fc;display:flex;align-items:center;gap:8px}
.mg-live{width:8px;height:8px;border-radius:50%;background:#22d3ee;box-shadow:0 0 0 0 rgba(34,211,238,.7);animation:mgpulse 1.8s infinite}
@keyframes mgpulse{0%{box-shadow:0 0 0 0 rgba(34,211,238,.7)}70%{box-shadow:0 0 0 10px rgba(34,211,238,0)}100%{box-shadow:0 0 0 0 rgba(34,211,238,0)}}
.mg-layers{display:flex;flex-wrap:wrap;gap:6px;padding:6px;border-radius:14px;background:rgba(2,6,23,.55);
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(148,163,184,.18)}
.mg-layer{all:unset;cursor:pointer;font-size:11.5px;padding:7px 12px;border-radius:10px;color:#cbd5e1;
  display:flex;align-items:center;gap:7px;transition:all .25s ease}
.mg-layer i{width:22px;height:8px;border-radius:4px;display:inline-block}
.mg-layer:hover{background:rgba(56,189,248,.14);color:#fff;transform:translateY(-1px)}
.mg-layer.on{background:linear-gradient(135deg,rgba(14,165,233,.35),rgba(139,92,246,.35));color:#fff;
  box-shadow:0 0 0 1px rgba(125,211,252,.5),0 0 22px -4px rgba(56,189,248,.7)}
.mg-btn{all:unset;cursor:pointer;width:38px;height:38px;border-radius:12px;display:grid;place-items:center;
  background:rgba(2,6,23,.55);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border:1px solid rgba(148,163,184,.2);transition:all .2s ease}
.mg-btn svg{width:18px;height:18px;fill:none;stroke:#bae6fd;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.mg-btn:hover{transform:scale(1.08);border-color:rgba(56,189,248,.7);box-shadow:0 0 18px -2px rgba(56,189,248,.6)}
.mg-btn.on{background:linear-gradient(135deg,rgba(14,165,233,.45),rgba(139,92,246,.45))}
.mg-panel{padding:10px 12px;border-radius:14px;background:rgba(2,6,23,.62);backdrop-filter:blur(10px);
  -webkit-backdrop-filter:blur(10px);border:1px solid rgba(148,163,184,.18);width:250px}
.mg-legend{min-width:0}
.mg-legend .lt{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:#94a3b8;margin-bottom:6px}
.mg-legend .bar{height:9px;border-radius:5px;box-shadow:0 0 14px -2px rgba(56,189,248,.45)}
.mg-legend .ticks{display:flex;justify-content:space-between;font-size:10.5px;color:#cbd5e1;margin-top:4px}
.mg-legend .src{font-size:10px;color:#64748b;margin-top:6px}
.mg-readout{margin-top:9px;padding-top:8px;border-top:1px solid rgba(148,163,184,.15);font-size:11px;display:flex;
  justify-content:space-between;align-items:baseline;gap:8px}
.mg-coord{color:#94a3b8}.mg-val{color:#f8fafc;font-size:15px;font-weight:600}
.mg-card{position:absolute;z-index:3;right:16px;bottom:16px;display:flex;align-items:center;gap:14px;
  padding:10px 12px 10px 16px;border-radius:16px;background:rgba(2,6,23,.62);backdrop-filter:blur(12px);
  -webkit-backdrop-filter:blur(12px);border:1px solid rgba(56,189,248,.35);box-shadow:0 10px 40px -10px rgba(56,189,248,.45);
  font-family:"Archivo",system-ui,sans-serif;max-width:min(430px,46%);animation:mgrise .6s ease both}
@keyframes mgrise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.mg-card .nm{font-weight:800;font-size:15px;color:#fff;line-height:1.15}
.mg-card .sb{font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:#7dd3fc;letter-spacing:.06em}
.mg-go{all:unset;cursor:pointer;white-space:nowrap;font-weight:700;font-size:13px;color:#fff;padding:9px 16px;border-radius:12px;
  background:linear-gradient(135deg,#0ea5e9,#6366f1 60%,#a855f7);background-size:200% 100%;
  box-shadow:0 0 0 1px rgba(255,255,255,.12) inset,0 8px 24px -6px rgba(99,102,241,.8);transition:all .25s ease}
.mg-go:hover{background-position:100% 0;transform:translateY(-1px) scale(1.03);box-shadow:0 0 30px -2px rgba(168,85,247,.8)}
.mg-loading{position:absolute;inset:0;z-index:5;display:flex;flex-direction:column;gap:14px;align-items:center;justify-content:center;
  background:radial-gradient(circle,#0b1b3a,#020617);color:#7dd3fc;font-size:12px;letter-spacing:.2em;text-transform:uppercase;
  transition:opacity .8s ease}
.mg-loading.done{opacity:0;pointer-events:none}
.mg-spinner{width:54px;height:54px;border-radius:50%;border:2px solid rgba(56,189,248,.15);border-top-color:#22d3ee;
  border-right-color:#a78bfa;animation:mgspin 1s linear infinite}
@keyframes mgspin{to{transform:rotate(360deg)}}
.float-tooltip-kap,.scene-tooltip{font-family:"IBM Plex Mono",monospace!important}
.mg-tip{padding:12px 14px;border-radius:14px;background:rgba(2,6,23,.88);border:1px solid rgba(56,189,248,.45);
  box-shadow:0 12px 40px -8px rgba(56,189,248,.6);min-width:220px;color:#e2e8f0}
.mg-tip .n{font-family:"Archivo",system-ui;font-weight:800;font-size:15px;color:#fff}
.mg-tip .r{font-size:11px;color:#7dd3fc;margin:2px 0 8px}
.mg-tip .k{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:11px}
.mg-tip .k span:nth-child(odd){color:#64748b}
.mg-tip .h{margin-top:8px;font-size:10.5px;color:#a78bfa}
@media (max-width:760px){.mg-card{max-width:calc(100% - 32px);bottom:auto;top:110px}.mg-panel{width:200px}}
"""

_GLOBE_JS = r"""
const LIB = "%LIB%";
const IMG = "%IMG%";
function loadLib(){
  if (window.Globe) return Promise.resolve();
  if (!window.__meceGlobeLib){
    window.__meceGlobeLib = new Promise((ok, ko) => {
      const s = document.createElement("script"); s.src = LIB; s.onload = ok; s.onerror = ko;
      document.head.appendChild(s);
    });
  }
  return window.__meceGlobeLib;
}
const LAYERS = {
  sst:   {img: d => d.tex.sst, grid: d => d.grid.sst, grad: "linear-gradient(90deg,#04142f,#3a2a8c,#a3378f,#f0644e,#fcd34d,#f6f8a0)",
          ticks: ["−2","8","18","28 °C"], unit: "°C", dec: 1},
  chl:   {img: d => d.tex.chl, grid: d => d.grid.chl, grad: "linear-gradient(90deg,#30123b,#4662d7,#1ae4b6,#a2fc3c,#faba39,#e4460a,#7a0403)",
          ticks: ["0.01","0.1","1","10 mg·m⁻³"], unit: "mg·m⁻³", dec: 2},
  night: {img: () => IMG + "earth-night.jpg", grid: () => null, grad: null},
  blue:  {img: () => IMG + "earth-blue-marble.jpg", grid: () => null, grad: null},
};
function ring(b){ // bbox -> polígono GeoJSON densificado
  const [la0, la1, lo0, lo1] = b, n = 16, pts = [];
  for (let i=0;i<=n;i++) pts.push([lo0 + (lo1-lo0)*i/n, la0]);
  for (let i=1;i<=n;i++) pts.push([lo1, la0 + (la1-la0)*i/n]);
  for (let i=1;i<=n;i++) pts.push([lo1 - (lo1-lo0)*i/n, la1]);
  for (let i=1;i<=n;i++) pts.push([lo0, la1 - (la1-la0)*i/n]);
  // d3-geo (usado por three-globe) espera el anillo exterior en sentido HORARIO;
  // en sentido antihorario el polígono sería "todo el planeta menos la caja".
  return {type: "Polygon", coordinates: [pts.reverse()]};
}
function esc(s){ return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

function init(root, S){
  const canvas = root.querySelector(".mg-canvas");
  const d = S.data;
  const g = Globe({animateIn: true, waitForGlobeReady: true})(canvas)
    .backgroundImageUrl(IMG + "night-sky.png")
    .bumpImageUrl(IMG + "earth-topology.png")
    .showAtmosphere(true).atmosphereColor("#38bdf8").atmosphereAltitude(0.16)
    .showGraticules(true)
    .polygonsTransitionDuration(350)
    .polygonGeoJsonGeometry(r => r.geom)
    .polygonCapColor(r => r.id === S.hover ? "rgba(34,211,238,0.55)" : r.id === S.data.active ? "rgba(34,211,238,0.38)" : "rgba(192,132,252,0.26)")
    .polygonSideColor(r => r.id === S.data.active ? "rgba(34,211,238,0.35)" : "rgba(167,139,250,0.18)")
    .polygonStrokeColor(r => r.id === S.data.active ? "#a5f3fc" : "#e9d5ff")
    .polygonAltitude(r => r.id === S.hover ? 0.07 : r.id === S.data.active ? 0.035 : 0.012)
    .polygonLabel(r => `<div class="mg-tip"><div class="n">${esc(r.name)}</div><div class="r">${esc(r.region)}</div>
        <div class="k"><span>bbox</span><span>${esc(r.bboxTxt)}</span><span>${esc(S.data.t.period)}</span><span>${esc(r.period)}</span>
        <span>${esc(S.data.t.vars)}</span><span>${esc(r.vars)}</span></div><div class="h">${esc(S.data.t.clickHint)}</div></div>`)
    .onPolygonHover(r => { S.hover = r ? r.id : null; canvas.style.cursor = r ? "pointer" : "grab"; g.polygonsData(g.polygonsData()); })
    .onPolygonClick(r => select(r.id))
    .ringColor(r => t => `rgba(${r.active ? "34,211,238" : "196,181,253"},${Math.max(0, 1 - t)})`)
    .ringMaxRadius(r => r.active ? 5.5 : 2.6).ringPropagationSpeed(r => r.active ? 2.6 : 1.4)
    .ringRepeatPeriod(r => r.active ? 850 : 1700)
    .labelLat(r => r.lat).labelLng(r => r.lng).labelText(r => r.name)
    .labelSize(r => r.active ? 1.05 : 0.62).labelDotRadius(r => r.active ? 0.42 : 0.26)
    .labelColor(r => r.active ? "#e0f2fe" : "rgba(221,214,254,0.85)").labelResolution(3).labelAltitude(0.02)
    .onLabelClick(r => select(r.id))
    .arcStartLat(a => a.s[0]).arcStartLng(a => a.s[1]).arcEndLat(a => a.e[0]).arcEndLng(a => a.e[1])
    .arcColor(() => ["rgba(251,191,36,0.95)", "rgba(34,211,238,0.95)"])
    .arcDashLength(0.35).arcDashGap(0.18).arcDashInitialGap(() => Math.random()).arcDashAnimateTime(2600)
    .arcStroke(0.55).arcAltitudeAutoScale(0.45)
    .arcLabel(a => `<div class="mg-tip"><div class="n">${esc(a.label)}</div><div class="r">${esc(a.sub)}</div></div>`);
  const ctl = g.controls();
  ctl.autoRotate = true; ctl.autoRotateSpeed = 0.32; ctl.enableDamping = true; ctl.dampingFactor = 0.08;
  S.g = g; S.root = root; S.layer = S.layer || "sst"; S.rotate = true;

  // tamaño
  const fit = () => { const r = root.getBoundingClientRect(); g.width(r.width).height(r.height); };
  new ResizeObserver(fit).observe(root); fit();
  document.addEventListener("fullscreenchange", () => setTimeout(fit, 120));

  // pausa del giro al interactuar
  let idle;
  canvas.addEventListener("pointerdown", () => { ctl.autoRotate = false; clearTimeout(idle);
    idle = setTimeout(() => { ctl.autoRotate = S.rotate; }, 7000); });

  // lectura bajo el cursor
  const coord = root.querySelector(".mg-coord"), val = root.querySelector(".mg-val");
  canvas.addEventListener("mousemove", ev => {
    const b = canvas.getBoundingClientRect();
    const c = g.toGlobeCoords(ev.clientX - b.left, ev.clientY - b.top);
    if (!c){ coord.textContent = "—"; val.textContent = ""; return; }
    const ns = c.lat >= 0 ? "N" : "S", ew = c.lng >= 0 ? "E" : "W";
    coord.textContent = `${Math.abs(c.lat).toFixed(2)}° ${ns} · ${Math.abs(c.lng).toFixed(2)}° ${ew}`;
    const L = LAYERS[S.layer], G = S.grids[S.layer];
    if (!G){ val.textContent = ""; return; }
    const i = Math.round((c.lat - G.lat0) / G.dlat), j = Math.round((c.lng - G.lon0) / G.dlon);
    const v = (i >= 0 && i < G.nlat && j >= 0 && j < G.nlon) ? G.v[i * G.nlon + j] : null;
    val.textContent = v === null || v === undefined ? S.data.t.land : `${v.toFixed(L.dec)} ${L.unit}`;
  });

  // botones
  root.querySelectorAll(".mg-btn").forEach(b => b.addEventListener("click", () => {
    const a = b.dataset.act, pov = g.pointOfView();
    if (a === "rotate"){ S.rotate = !S.rotate; ctl.autoRotate = S.rotate; b.classList.toggle("on", S.rotate); }
    if (a === "center") fly(1.55);
    if (a === "in") g.pointOfView({...pov, altitude: Math.max(0.35, pov.altitude * 0.7)}, 600);
    if (a === "out") g.pointOfView({...pov, altitude: Math.min(4.5, pov.altitude * 1.4)}, 600);
    if (a === "full"){ document.fullscreenElement ? document.exitFullscreen() : root.requestFullscreen(); }
  }));
  root.querySelector('[data-act="rotate"]').classList.add("on");

  // material: la textura emite su propia luz → colores vivos del dato
  const vivid = () => {
    const m = g.globeMaterial();
    // casi sin iluminar: color final ≈ textura (fiel al dato) + 15 % de sombreado para el volumen
    if (m && m.map){ m.emissiveMap = m.map; if (m.emissive) m.emissive.setRGB(0.8, 0.8, 0.8);
      if (m.color) m.color.setRGB(0.15, 0.15, 0.15); if (m.specular) m.specular.setRGB(0.02, 0.02, 0.03);
      m.shininess = 4; m.bumpScale = 3; m.needsUpdate = true; }
  };
  S.vivid = vivid;
  // intro cinematográfica: gira llegando y se detiene sobre la región
  const act = activeRegion();
  g.pointOfView({lat: act.lat + 25, lng: act.lng - 70, altitude: 3.6});
  g.onGlobeReady(() => {
    vivid();
    root.querySelector(".mg-loading").classList.add("done");
    setTimeout(() => { fly(1.55, 2600); setTimeout(() => { S.rotate = false; ctl.autoRotate = false;
      root.querySelector('[data-act="rotate"]').classList.remove("on"); }, 2600); }, 250);
  });
  setTimeout(() => root.querySelector(".mg-loading").classList.add("done"), 9000);
}

function activeRegion(){ const S = window.__meceGlobe; return S.data.regions.find(r => r.id === S.data.active) || S.data.regions[0]; }
function fly(alt = 1.55, ms = 1800){ const S = window.__meceGlobe, a = activeRegion(); S.g.pointOfView({lat: a.lat, lng: a.lng, altitude: alt}, ms); }
function select(id){
  const S = window.__meceGlobe;
  if (id === S.data.active){ fly(1.2); return; }
  S.data.active = id; refresh(); fly(1.55);
  S.trigger("select", id);
}
function setLayer(k){
  const S = window.__meceGlobe, L = LAYERS[k];
  S.layer = k; S.g.globeImageUrl(L.img(S.data));
  if (S.vivid) [300, 1200, 2500].forEach(ms => setTimeout(S.vivid, ms));  // tras cargar la nueva textura
  S.root.querySelectorAll(".mg-layer").forEach(b => b.classList.toggle("on", b.dataset.k === k));
  const leg = S.root.querySelector(".mg-legend");
  if (L.grad){
    leg.style.display = "";
    leg.innerHTML = `<div class="lt">${esc(S.data.t.layers[k])}</div><div class="bar" style="background:${L.grad}"></div>
      <div class="ticks">${L.ticks.map(t => `<span>${t}</span>`).join("")}</div><div class="src">${esc(S.data.src[k])}</div>`;
  } else {
    leg.innerHTML = `<div class="lt">${esc(S.data.t.layers[k])}</div><div class="src">NASA Visible Earth · Blue Marble / Black Marble</div>`;
  }
  const url = L.grid(S.data);
  if (url && !S.grids[k]) fetch(url).then(r => r.json()).then(j => { S.grids[k] = j; }).catch(() => {});
}
function refresh(){
  const S = window.__meceGlobe, d = S.data;
  const polys = d.regions.map(r => ({...r, geom: ring(r.bbox)}));
  S.g.polygonsData(polys);
  const pts = d.regions.map(r => ({...r, active: r.id === d.active}));
  S.g.ringsData(pts).labelsData(pts).arcsData(d.arcs);
  const a = activeRegion();
  const card = S.root.querySelector(".mg-card");
  card.innerHTML = `<div><div class="sb">${esc(d.t.active)}</div><div class="nm">${esc(a.name)}</div><div class="sb" style="color:#94a3b8">${esc(a.region)}</div></div>
    <button class="mg-go">${esc(d.t.analyze)}</button>`;
  card.style.animation = "none"; void card.offsetWidth; card.style.animation = "";
  card.querySelector(".mg-go").onclick = () => S.trigger("analyze", d.active);
}

export default function (component){
  const {data, parentElement, setTriggerValue} = component;
  const root = parentElement.querySelector(".mg-root");
  root.style.setProperty("--h", (data.height || 660) + "px");
  const prev = window.__meceGlobe;
  const S = window.__meceGlobe = (prev && prev.root === root) ? prev : {grids: {}, layer: (prev && prev.layer) || "sst"};
  S.data = data; S.trigger = setTriggerValue;
  root.querySelector(".mg-t-layers").textContent = data.t.layersTitle;
  root.querySelector(".mg-t-loading").textContent = data.t.loading;
  const tips = {rotate: data.t.rotate, center: data.t.center, full: data.t.full};
  root.querySelectorAll(".mg-btn").forEach(b => { if (tips[b.dataset.act]) b.title = tips[b.dataset.act]; });
  const lay = root.querySelector(".mg-layers");
  lay.innerHTML = Object.keys(LAYERS).map(k => `<button class="mg-layer" data-k="${k}"><i style="background:${LAYERS[k].grad ||
      (k === "night" ? "linear-gradient(90deg,#0b1020,#f59e0b)" : "linear-gradient(90deg,#1e3a8a,#16a34a,#e7e5e4)")}"></i>${esc(data.t.layers[k])}</button>`).join("");
  lay.querySelectorAll(".mg-layer").forEach(b => b.onclick = () => setLayer(b.dataset.k));
  loadLib().then(() => {
    if (!S.g) init(root, S);
    setLayer(S.layer); refresh();
    if (prev && prev.root === root && prev.lastActive !== data.active) fly(1.55);
    S.lastActive = data.active;
  }).catch(() => { root.querySelector(".mg-t-loading").textContent = "WebGL / CDN no disponible"; });
}
""".replace("%LIB%", GLOBE_LIB).replace("%IMG%", IMG)

_globe = st.components.v2.component("mece_globe", html=_GLOBE_HTML, css=_GLOBE_CSS, js=_GLOBE_JS)


def globe(data: dict, on_select=None, on_analyze=None, key: str = "globe"):
    return _globe(
        key=key,
        data=data,
        height=data.get("height", 660),
        on_select_change=on_select or (lambda: None),
        on_analyze_change=on_analyze or (lambda: None),
    )


# ========================================================= BARRA DE MISIÓN
_BAR_HTML = """
<div class="mb">
  <div class="mb-logo"><svg viewBox="0 0 64 64"><defs><linearGradient id="mbg" x1="0" x2="1">
    <stop offset="0" stop-color="#22d3ee"/><stop offset=".55" stop-color="#6366f1"/><stop offset="1" stop-color="#e879f9"/></linearGradient></defs>
    <circle cx="32" cy="32" r="13" fill="url(#mbg)"/><ellipse class="orb" cx="32" cy="32" rx="28" ry="10" fill="none" stroke="url(#mbg)" stroke-width="2"/>
    <circle class="sat" cx="60" cy="32" r="3" fill="#f0f9ff"/></svg></div>
  <div class="mb-txt"><div class="mb-title">Marine Ecosystem Change Explorer</div>
    <div class="mb-sub"><span class="mb-dot"></span><span class="mb-subt"></span></div></div>
  <div class="mb-clock">
    <div class="mb-cl"><span class="mb-zone"></span></div>
    <div class="mb-time">--:--:--</div>
    <div class="mb-date"></div>
    <div class="mb-utc"></div>
  </div>
  <div class="mb-upd"><div class="mb-cl mb-updl"></div><div class="mb-updv">—</div><div class="mb-updd"></div></div>
</div>
"""
_BAR_CSS = """
.mb{display:flex;align-items:center;gap:18px;padding:12px 2px 8px;font-family:"IBM Plex Mono",ui-monospace,monospace;color:#e2e8f0}
.mb-logo svg{width:58px;height:58px;filter:drop-shadow(0 0 14px rgba(56,189,248,.65))}
.mb-logo .orb{transform-origin:32px 32px;animation:mbspin 9s linear infinite}
.mb-logo .sat{transform-origin:32px 32px;animation:mbsat 4.5s linear infinite}
@keyframes mbspin{to{transform:rotate(360deg)}}
@keyframes mbsat{0%{transform:rotate(0) scaleY(.36)}100%{transform:rotate(360deg) scaleY(.36)}}
.mb-title{font-family:"Archivo",system-ui,sans-serif;font-weight:800;font-size:clamp(18px,2.1vw,28px);letter-spacing:.03em;
  text-transform:uppercase;line-height:1.05;background:linear-gradient(90deg,#e0f2fe,#38bdf8,#818cf8,#e879f9,#38bdf8,#e0f2fe);
  background-size:300% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:mbshine 9s ease-in-out infinite}
@keyframes mbshine{0%,100%{background-position:0 0}50%{background-position:100% 0}}
.mb-sub{display:flex;align-items:center;gap:8px;font-size:11.5px;color:#94a3b8;margin-top:5px;letter-spacing:.06em}
.mb-dot{width:7px;height:7px;border-radius:50%;background:#34d399;box-shadow:0 0 10px #34d399;animation:mbblink 1.6s infinite}
@keyframes mbblink{50%{opacity:.25}}
.mb-clock,.mb-upd{text-align:right;padding:9px 15px;border-radius:14px;background:rgba(2,6,23,.45);
  border:1px solid rgba(56,189,248,.22);box-shadow:inset 0 0 20px -8px rgba(56,189,248,.5)}
.mb-clock{margin-left:auto}
.mb-cl{font-size:9.5px;letter-spacing:.16em;color:#7dd3fc;text-transform:uppercase;white-space:nowrap}
.mb-time{font-size:22px;font-weight:600;color:#f0f9ff;letter-spacing:.06em;text-shadow:0 0 12px rgba(56,189,248,.6);line-height:1.25}
.mb-date{font-size:10.5px;color:#cbd5e1;white-space:nowrap}
.mb-utc{font-size:9.5px;color:#64748b;margin-top:2px;letter-spacing:.04em;white-space:nowrap}
.mb-updv{font-family:"Archivo",system-ui;font-weight:700;font-size:16px;color:#a7f3d0;margin-top:3px;text-shadow:0 0 12px rgba(52,211,153,.5)}
.mb-updd{font-size:9.5px;color:#64748b;margin-top:2px}
@media (max-width:900px){.mb-upd{display:none}}
@media (max-width:640px){.mb-clock{display:none}}
"""
_BAR_JS = r"""
// Fondo de galaxia: se inyecta UNA vez en <body>, fuera de los contenedores de Streamlit,
// detrás de todo el contenido (z-index -1) y sin capturar eventos.
function galaxy(){
  if (document.getElementById("mece-galaxy")) return;
  const css = document.createElement("style");
  css.id = "mece-galaxy-css";
  css.textContent = `
  #mece-galaxy{position:fixed;inset:0;z-index:-1;pointer-events:none;overflow:hidden}
  #mece-galaxy .milky{position:absolute;left:-30%;top:18%;width:160%;height:46%;transform:rotate(-17deg);filter:blur(28px);opacity:.55;
    background:radial-gradient(50% 50% at 50% 50%,rgba(148,163,184,.13),rgba(129,140,248,.07) 45%,transparent 72%),
               radial-gradient(22% 30% at 34% 46%,rgba(244,114,182,.06),transparent 70%),
               radial-gradient(26% 34% at 68% 54%,rgba(56,189,248,.07),transparent 70%)}
  #mece-galaxy .dust{position:absolute;inset:0;opacity:.6;transform:rotate(-17deg) scale(1.3);
    background-image:radial-gradient(1px 1px at 12% 41%,rgba(255,255,255,.7),transparent),radial-gradient(1px 1px at 27% 52%,rgba(191,219,254,.6),transparent),
      radial-gradient(1px 1px at 43% 47%,rgba(255,255,255,.6),transparent),radial-gradient(1px 1px at 58% 55%,rgba(233,213,255,.6),transparent),
      radial-gradient(1px 1px at 71% 44%,rgba(255,255,255,.55),transparent),radial-gradient(1px 1px at 86% 50%,rgba(165,243,252,.55),transparent);
    background-size:340px 180px}
  #mece-galaxy .ast{position:absolute;left:0;top:0;will-change:transform;animation:mece-fly linear infinite}
  #mece-galaxy .ast .rock{display:block;animation:mece-spin linear infinite}
  #mece-galaxy .ast .trail{position:absolute;right:55%;top:50%;height:1.5px;transform:translateY(-50%);border-radius:2px;
    background:linear-gradient(90deg,transparent,rgba(186,230,253,.28))}
  @keyframes mece-fly{from{transform:translate(var(--x0),var(--y0)) rotate(var(--a))}to{transform:translate(var(--x1),var(--y1)) rotate(var(--a))}}
  @keyframes mece-spin{to{transform:rotate(360deg)}}
  @media (prefers-reduced-motion:reduce){#mece-galaxy .ast{display:none}}`;
  document.head.appendChild(css);
  const g = document.createElement("div"); g.id = "mece-galaxy";
  g.innerHTML = '<div class="milky"></div><div class="dust"></div>';
  // asteroides: forma irregular, tamaño, trayectoria, velocidad y retraso distintos; opacidad baja
  const rnd = (a, b) => a + Math.random() * (b - a);
  const rock = (sz, i) => { const n = 9, pts = [];
    for (let k = 0; k < n; k++){ const ang = 2 * Math.PI * k / n, r = sz / 2 * rnd(.62, 1);
      pts.push(`${(sz / 2 + r * Math.cos(ang)).toFixed(1)},${(sz / 2 + r * Math.sin(ang)).toFixed(1)}`); }
    return `<svg width="${sz}" height="${sz}" viewBox="0 0 ${sz} ${sz}"><defs><radialGradient id="ag${i}" cx="35%" cy="30%">
      <stop offset="0" stop-color="#cbd5e1"/><stop offset=".55" stop-color="#64748b"/><stop offset="1" stop-color="#1e293b"/></radialGradient></defs>
      <polygon points="${pts.join(" ")}" fill="url(#ag${i})"/><circle cx="${sz * .62}" cy="${sz * .6}" r="${sz * .09}" fill="rgba(15,23,42,.55)"/>
      <circle cx="${sz * .4}" cy="${sz * .66}" r="${sz * .06}" fill="rgba(15,23,42,.5)"/></svg>`; };
  for (let i = 0; i < 9; i++){
    const sz = rnd(5, 17), dur = rnd(55, 120), ltr = Math.random() < .7;
    const y0 = rnd(-5, 95), y1 = y0 + rnd(-25, 25);
    const a = document.createElement("span"); a.className = "ast";
    a.style.cssText = `--x0:${ltr ? "-12vw" : "112vw"};--x1:${ltr ? "112vw" : "-12vw"};--y0:${y0}vh;--y1:${y1}vh;` +
      `--a:${ltr ? 0 : 180}deg;animation-duration:${dur}s;animation-delay:-${rnd(0, dur)}s;opacity:${rnd(.28, .55).toFixed(2)}`;
    a.innerHTML = `<span class="trail" style="width:${sz * rnd(4, 9)}px"></span>` +
      `<span class="rock" style="animation-duration:${rnd(14, 40)}s">${rock(sz, i)}</span>`;
    g.appendChild(a);
  }
  document.body.appendChild(g);
}

export default function(component){
  const {data, parentElement} = component;
  galaxy();
  const L = data.labels, locale = {en: "en-US", pt: "pt-BR"}[data.lang] || "es-MX";
  parentElement.querySelector(".mb-subt").textContent = data.sub;
  parentElement.querySelector(".mb-updl").textContent = L.updated;
  const $ = s => parentElement.querySelector(s);
  const fT = new Intl.DateTimeFormat(locale, {hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false});
  const fD = new Intl.DateTimeFormat(locale, {weekday: "long", day: "numeric", month: "long", year: "numeric"});
  const zone = () => {
    try {
      const ab = new Intl.DateTimeFormat(locale, {timeZoneName: "short"}).formatToParts(new Date())
                   .find(p => p.type === "timeZoneName").value;
      const city = (Intl.DateTimeFormat().resolvedOptions().timeZone || "").split("/").pop().replace(/_/g, " ");
      return city ? `${city} (${ab})` : ab;
    } catch (e) { return ""; } };
  const upd = data.updated ? Date.parse(data.updated) : NaN;
  const rel = () => {
    if (!isFinite(upd)) return L.never;
    const m = Math.max(0, (Date.now() - upd) / 60000);
    if (m < 2) return L.now;
    if (m < 90) return `${L.ago} ${Math.round(m)} ${L.min}`.trim();
    if (m < 60 * 36) return `${L.ago} ${Math.round(m / 60)} ${L.h}`.trim();
    return `${L.ago} ${Math.round(m / 1440)} ${L.d}`.trim();
  };
  const tick = () => {
    const n = new Date();
    $(".mb-zone").textContent = `${L.local} · ${zone()}`;
    $(".mb-time").textContent = fT.format(n);
    $(".mb-date").textContent = fD.format(n);
    $(".mb-utc").textContent = `${n.toISOString().slice(11, 19)} ${L.utc}`;
    $(".mb-updv").textContent = rel();
    $(".mb-updd").textContent = isFinite(upd) ? new Date(upd).toLocaleString(locale, {dateStyle: "medium", timeStyle: "short"}) : "";
  };
  tick(); const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}
"""
_bar = st.components.v2.component("mece_missionbar", html=_BAR_HTML, css=_BAR_CSS, js=_BAR_JS)


def mission_bar(sub: str, lang: str, updated_iso: str, labels: dict):
    return _bar(key="missionbar", height=118,
                data={"sub": sub, "lang": lang, "updated": updated_iso, "labels": labels})


# ================================================================== KPI
_KPI_HTML = '<div class="kp"></div>'
_KPI_CSS = """
.kp{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;font-family:"IBM Plex Mono",ui-monospace,monospace;perspective:900px}
.k{position:relative;padding:18px 20px 16px;border-radius:18px;overflow:hidden;color:#e2e8f0;
  background:linear-gradient(160deg,rgba(15,23,42,.82),rgba(15,23,42,.45));border:1px solid rgba(148,163,184,.16);
  box-shadow:0 20px 50px -25px rgba(2,6,23,.9);transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease;
  transform-style:preserve-3d;animation:krise .7s cubic-bezier(.2,.8,.2,1) both}
.k:nth-child(2){animation-delay:.08s}.k:nth-child(3){animation-delay:.16s}.k:nth-child(4){animation-delay:.24s}
@keyframes krise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
.k::before{content:"";position:absolute;inset:-1px;border-radius:18px;padding:1px;pointer-events:none;
  background:linear-gradient(135deg,var(--c1),transparent 40%,transparent 60%,var(--c2));
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;opacity:.75}
.k::after{content:"";position:absolute;width:180px;height:180px;right:-60px;top:-70px;border-radius:50%;
  background:radial-gradient(circle,var(--c1),transparent 70%);opacity:.22;filter:blur(6px);pointer-events:none}
.k:hover{box-shadow:0 0 0 1px var(--c1),0 25px 60px -20px var(--c1)}
.l{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:#94a3b8}
.v{font-family:"Archivo",system-ui,sans-serif;font-weight:800;font-size:clamp(26px,2.6vw,36px);line-height:1.15;margin-top:6px;
  background:linear-gradient(90deg,var(--c1),var(--c2));-webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 0 16px color-mix(in srgb,var(--c1) 45%,transparent))}
.v small{font-size:.45em;-webkit-text-fill-color:#cbd5e1;margin-left:4px;font-weight:500}
.f{font-size:11.5px;color:#cbd5e1;margin-top:6px;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.dot{width:9px;height:9px;border-radius:50%;background:var(--c1);box-shadow:0 0 12px var(--c1)}
.g{position:absolute;right:14px;top:14px;width:84px;height:48px;opacity:.95}
@media (max-width:980px){.kp{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:480px){.kp{grid-template-columns:1fr}}
"""
_KPI_JS = """
const ease = t => 1 - Math.pow(1 - t, 3);
function gauge(z){ // semicírculo z ∈ [-4,4], zonas significativas |z|>1.96
  const ang = v => Math.PI * (1 - (Math.max(-4, Math.min(4, v)) + 4) / 8);
  const P = v => [46 + 38 * Math.cos(ang(v)), 48 - 38 * Math.sin(ang(v))];
  const arc = (a, b, c) => { const [x1,y1] = P(a), [x2,y2] = P(b); return `<path d="M${x1} ${y1} A38 38 0 0 1 ${x2} ${y2}" stroke="${c}" stroke-width="7" fill="none" stroke-linecap="round"/>`; };
  const [nx, ny] = P(z);
  return `<svg class="g" viewBox="0 0 92 52">${arc(-4,-1.96,"#38bdf8")}${arc(-1.96,1.96,"#334155")}${arc(1.96,4,"#fb7185")}
    <line x1="46" y1="48" x2="${nx}" y2="${ny}" stroke="#f8fafc" stroke-width="2.4" stroke-linecap="round"/><circle cx="46" cy="48" r="4" fill="#f8fafc"/></svg>`;
}
export default function(component){
  const {data, parentElement} = component;
  const box = parentElement.querySelector(".kp");
  box.innerHTML = data.cards.map((c, i) => `<div class="k" style="--c1:${c.c1};--c2:${c.c2}">
    <div class="l">${c.label}</div><div class="v"><span data-i="${i}">0</span><small>${c.unit || ""}</small></div>
    <div class="f">${c.dot ? '<span class="dot"></span>' : ""}${c.sub}</div>${c.z !== undefined && c.z !== null ? gauge(c.z) : ""}</div>`).join("");
  const t0 = performance.now(), D = 1300;
  const spans = box.querySelectorAll("[data-i]");
  let raf;
  const step = now => {
    const p = ease(Math.min(1, (now - t0) / D));
    spans.forEach(s => { const c = data.cards[+s.dataset.i];
      if (c.text) { s.textContent = c.text; return; }
      if (c.value === null || !isFinite(c.value)) { s.textContent = "—"; return; }
      const v = c.value * p; s.textContent = (c.sign && v >= 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(c.dec); });
    if (p < 1) raf = requestAnimationFrame(step);
  };
  raf = requestAnimationFrame(step);
  box.querySelectorAll(".k").forEach(k => {
    k.onmousemove = e => { const r = k.getBoundingClientRect(), x = (e.clientX - r.left) / r.width - .5, y = (e.clientY - r.top) / r.height - .5;
      k.style.transform = `rotateY(${x * 10}deg) rotateX(${-y * 10}deg) translateY(-3px)`; };
    k.onmouseleave = () => { k.style.transform = ""; };
  });
  return () => cancelAnimationFrame(raf);
}
"""
_kpis = st.components.v2.component("mece_kpis", html=_KPI_HTML, css=_KPI_CSS, js=_KPI_JS)


def kpis(cards: list[dict], key: str = "kpis"):
    return _kpis(key=key, data={"cards": cards}, height=150)


# ======================================================= TARJETAS DE REGIÓN
_CARDS_HTML = '<div class="rc"></div>'
_CARDS_CSS = """
.rc{display:flex;flex-direction:column;gap:10px;font-family:"IBM Plex Mono",ui-monospace,monospace}
.c{all:unset;cursor:pointer;display:grid;grid-template-columns:42px 1fr auto;align-items:center;gap:12px;padding:12px 14px;border-radius:14px;
  background:linear-gradient(160deg,rgba(15,23,42,.75),rgba(15,23,42,.4));border:1px solid rgba(148,163,184,.14);
  transition:all .25s cubic-bezier(.2,.8,.2,1);position:relative;overflow:hidden}
.c::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(125,211,252,.12) 50%,transparent 70%);
  transform:translateX(-100%);transition:transform .7s ease}
.c:hover{transform:translateX(4px);border-color:rgba(56,189,248,.55);box-shadow:0 0 28px -8px rgba(56,189,248,.7)}
.c:hover::after{transform:translateX(100%)}
.c.on{border-color:rgba(103,232,249,.85);background:linear-gradient(135deg,rgba(14,165,233,.28),rgba(99,102,241,.22));
  box-shadow:0 0 0 1px rgba(103,232,249,.35) inset,0 0 34px -8px rgba(34,211,238,.8)}
.ic{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-family:"Archivo",system-ui;font-weight:800;color:#fff;font-size:15px;
  background:linear-gradient(135deg,var(--a),var(--b));box-shadow:0 6px 18px -6px var(--a)}
.n{font-family:"Archivo",system-ui,sans-serif;font-weight:700;font-size:14.5px;color:#f1f5f9}
.r{font-size:10.5px;color:#7dd3fc;margin-top:2px;letter-spacing:.04em}
.bb{font-size:10px;color:#64748b;margin-top:2px}
.ar{color:#67e8f9;font-size:18px;opacity:.0;transition:all .25s}
.c:hover .ar,.c.on .ar{opacity:1;transform:translateX(2px)}
"""
_CARDS_JS = """
export default function(component){
  const {data, parentElement, setTriggerValue} = component;
  const box = parentElement.querySelector(".rc");
  const pal = [["#06b6d4","#6366f1"],["#3b82f6","#22d3ee"],["#a855f7","#ec4899"],["#f59e0b","#ef4444"],["#10b981","#06b6d4"]];
  box.innerHTML = data.regions.map((r, i) => `<button class="c ${r.id === data.active ? "on" : ""}" data-id="${r.id}"
     style="--a:${pal[i % pal.length][0]};--b:${pal[i % pal.length][1]}"><span class="ic">${r.abbr}</span>
     <span><div class="n">${r.name}</div><div class="r">${r.region}</div><div class="bb">${r.bboxTxt}</div></span><span class="ar">➜</span></button>`).join("");
  box.querySelectorAll(".c").forEach(b => b.onclick = () => {
    box.querySelectorAll(".c").forEach(x => x.classList.toggle("on", x === b));
    setTriggerValue("select", b.dataset.id);
  });
}
"""
_cards = st.components.v2.component(
    "mece_regioncards", html=_CARDS_HTML, css=_CARDS_CSS, js=_CARDS_JS
)


def region_cards(regions: list[dict], active: str, on_select=None, key: str = "regioncards"):
    return _cards(
        key=key,
        data={"regions": regions, "active": active},
        height=94 * len(regions) + 10 * (len(regions) - 1) + 8,
        on_select_change=on_select or (lambda: None),
    )
