"""Vista Historia (storytelling): componente interactivo de desplazamiento por capítulos.

Solo presentación. Las cifras llegan de mece.research (results.json) vía `build_story_data`.
"""

from __future__ import annotations

import json

import numpy as np
import streamlit as st

_HTML = '<div class="st-root"></div>'

_CSS = r"""
:host{all:initial}
.st-root{font-family:"Archivo",system-ui,sans-serif;color:#e2e8f0;--c:#22d3ee;--v:#a78bfa;--w:#fb7185;--a:#fbbf24}
.st-root *{box-sizing:border-box}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
section{position:relative;padding:72px 0;max-width:1080px;margin:0 auto}
.reveal{opacity:0;transform:translateY(40px);transition:opacity 1s cubic-bezier(.2,.8,.2,1),transform 1s cubic-bezier(.2,.8,.2,1)}
.reveal.in{opacity:1;transform:none}
.kick{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.22em;text-transform:uppercase;color:#7dd3fc;
  display:flex;align-items:center;gap:10px;margin-bottom:14px}
.kick::before{content:"";width:28px;height:2px;background:linear-gradient(90deg,var(--c),var(--v));box-shadow:0 0 10px var(--c)}
h2{font-weight:900;font-size:clamp(30px,4.4vw,52px);line-height:1.04;margin:0 0 18px;letter-spacing:-.01em;
  background:linear-gradient(95deg,#f0f9ff 10%,#7dd3fc 55%,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
p.lead{font-family:system-ui,sans-serif;font-size:clamp(16px,1.5vw,19px);line-height:1.7;color:#cbd5e1;max-width:62ch;margin:0}
.glass{background:linear-gradient(160deg,rgba(15,23,42,.78),rgba(15,23,42,.42));border:1px solid rgba(148,163,184,.16);
  border-radius:22px;backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);box-shadow:0 30px 70px -40px rgba(0,0,0,.9)}
.hint{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:#64748b;margin-top:14px}
.btn{all:unset;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:13px;padding:10px 18px;border-radius:12px;color:#e0f2fe;
  border:1px solid rgba(56,189,248,.4);background:rgba(2,6,23,.5);transition:all .3s cubic-bezier(.2,.8,.2,1)}
.btn:hover{transform:translateY(-2px);box-shadow:0 0 26px -6px rgba(56,189,248,.9)}
.btn.on{background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7);border-color:transparent;color:#fff;
  box-shadow:0 10px 30px -10px rgba(99,102,241,.95)}
/* --- hero --- */
.hero{min-height:88vh;display:flex;flex-direction:column;justify-content:center;padding:40px 0 80px;max-width:none;overflow:hidden;
  border-radius:28px;isolation:isolate}
.hero .bg{position:absolute;inset:0;z-index:-2;background-size:cover;background-position:30% 50%;opacity:.55;
  animation:pan 60s linear infinite alternate;filter:saturate(1.3) contrast(1.05)}
@keyframes pan{from{background-position:20% 50%}to{background-position:80% 50%}}
.hero .shade{position:absolute;inset:0;z-index:-1;background:
  radial-gradient(80% 70% at 30% 40%,rgba(2,6,23,.15),rgba(2,6,23,.92)),linear-gradient(180deg,rgba(2,6,23,.2),#020617 96%)}
.hero .inner{padding:0 min(6vw,64px);max-width:1080px}
.hero h1{font-weight:900;font-size:clamp(38px,6.4vw,84px);line-height:.98;letter-spacing:-.02em;margin:18px 0 22px;
  background:linear-gradient(95deg,#ffffff,#a5f3fc 45%,#c4b5fd 80%);-webkit-background-clip:text;background-clip:text;color:transparent;
  text-shadow:0 0 60px rgba(56,189,248,.25)}
.hero .lead{font-size:clamp(17px,1.7vw,21px)}
.scroll{margin-top:44px;display:flex;align-items:center;gap:12px;font-family:"IBM Plex Mono",monospace;font-size:12px;
  letter-spacing:.2em;text-transform:uppercase;color:#7dd3fc}
.mouse{width:22px;height:36px;border:2px solid #7dd3fc;border-radius:12px;position:relative}
.mouse::after{content:"";position:absolute;left:50%;top:7px;width:4px;height:8px;margin-left:-2px;border-radius:2px;background:#7dd3fc;
  animation:wheel 1.8s ease-in-out infinite}
@keyframes wheel{0%{opacity:0;transform:translateY(0)}30%{opacity:1}100%{opacity:0;transform:translateY(12px)}}
/* --- satélites --- */
.sats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:34px}
.sat{all:unset;cursor:pointer;padding:22px 18px;border-radius:18px;text-align:left;position:relative;overflow:hidden;
  background:rgba(15,23,42,.6);border:1px solid rgba(148,163,184,.16);transition:all .35s cubic-bezier(.2,.8,.2,1)}
.sat:hover,.sat.on{transform:translateY(-6px);border-color:rgba(56,189,248,.6);box-shadow:0 20px 50px -20px rgba(56,189,248,.8)}
.sat .y{font-family:"IBM Plex Mono",monospace;font-size:12px;color:#a78bfa;letter-spacing:.1em}
.sat .n{font-weight:800;font-size:17px;color:#fff;margin-top:6px}
.sat .orb{position:absolute;right:14px;top:14px;width:34px;height:34px;border-radius:50%;border:1px dashed rgba(125,211,252,.5);
  animation:spin 6s linear infinite}
.sat .orb::after{content:"";position:absolute;top:-4px;left:50%;width:8px;height:8px;margin-left:-4px;border-radius:50%;background:#e0f2fe;
  box-shadow:0 0 10px #7dd3fc}
@keyframes spin{to{transform:rotate(360deg)}}
.satinfo{margin-top:18px;padding:18px 22px;min-height:66px;font-family:system-ui;font-size:15px;line-height:1.6;color:#cbd5e1}
/* --- franjas --- */
.stripes{display:flex;height:180px;border-radius:16px;overflow:hidden;margin-top:30px;box-shadow:0 20px 60px -30px rgba(251,113,133,.6)}
.stripe{flex:1;transform:scaleY(0);transform-origin:bottom;transition:transform .35s ease,filter .2s;position:relative}
.stripe.show{transform:scaleY(1)}
.stripe:hover{filter:brightness(1.35)}
.years{display:flex;justify-content:space-between;font-family:"IBM Plex Mono",monospace;font-size:11px;color:#64748b;margin-top:8px}
.row{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-top:20px}
.yearnow{font-family:"IBM Plex Mono",monospace;font-size:34px;font-weight:600;color:#fff;min-width:110px}
.anomnow{font-family:"IBM Plex Mono",monospace;font-size:15px}
.note{margin-top:18px;padding:14px 18px;border-left:3px solid var(--a);border-radius:0 14px 14px 0;background:rgba(251,191,36,.08);
  font-family:system-ui;color:#fde68a;font-size:15px}
.gridwrap{display:grid;grid-template-columns:1fr 1fr;gap:26px;align-items:center;margin-top:30px;padding:26px}
.dots{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;max-width:340px}
.dot{aspect-ratio:1;border-radius:50%;background:rgba(56,189,248,.18);border:1px solid rgba(56,189,248,.35);transition:all .5s cubic-bezier(.2,.8,.2,1)}
.dot.hot{background:radial-gradient(circle at 35% 30%,#fecaca,#fb7185 45%,#be123c);border-color:#fb7185;box-shadow:0 0 22px -2px #fb7185;transform:scale(1.06)}
.big{font-weight:900;font-size:clamp(56px,7vw,96px);line-height:1;color:#fff}
.big small{font-size:.32em;color:#94a3b8;font-weight:600;margin-left:8px}
/* --- mapa --- */
.mapwrap{display:grid;grid-template-columns:1.35fr 1fr;gap:22px;margin-top:30px;align-items:stretch}
svg.map{width:100%;height:auto;display:block;border-radius:20px;background:radial-gradient(circle at 50% 40%,#0b2347,#030b1c)}
.map .land{fill:#1e293b;stroke:#334155;stroke-width:.6}
.map .gulf{fill:none;stroke:rgba(125,211,252,.35);stroke-width:1}
.map .reg{cursor:pointer;stroke:#e0f2fe;stroke-width:1.2;transition:all .35s;fill-opacity:.55}
.map .reg:hover,.map .reg.on{fill-opacity:.9;stroke-width:2.6;filter:drop-shadow(0 0 10px rgba(255,255,255,.6))}
.map .basin{fill:rgba(251,191,36,.18);stroke:#fbbf24;stroke-width:1.3;stroke-dasharray:5 4}
.panel{padding:24px}
.panel .rn{font-weight:900;font-size:24px;color:#fff;margin-bottom:16px}
.ind{display:flex;align-items:center;gap:14px;padding:14px;border-radius:14px;background:rgba(2,6,23,.45);margin-bottom:12px}
.ind .ic{width:34px;height:34px;display:inline-block;flex:none}
.ind .lb{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#94a3b8}
.ind .vl{font-weight:800;font-size:18px}
.up{color:#fb7185}.down{color:#38bdf8}.flat{color:#94a3b8}
/* --- ríos --- */
.river{display:grid;grid-template-columns:1.2fr 1fr;gap:24px;margin-top:30px;padding:26px;align-items:center}
.flow{position:relative;height:150px;border-radius:16px;overflow:hidden;background:linear-gradient(90deg,#14532d 0%,#14532d 38%,#0c4a6e 38%,#082f49 100%)}
.flow .lab{position:absolute;bottom:10px;font-family:"IBM Plex Mono",monospace;font-size:11px;color:#e2e8f0;opacity:.85}
.flow .drop{position:absolute;width:8px;height:8px;border-radius:50%;background:#7dd3fc;box-shadow:0 0 8px #7dd3fc;animation:flow linear infinite}
@keyframes flow{from{transform:translateX(0);opacity:0}10%{opacity:1}to{transform:translateX(var(--dist));opacity:.0}}
.flow .bloom{position:absolute;right:8%;top:50%;width:110px;height:110px;margin-top:-55px;border-radius:50%;
  background:radial-gradient(circle,rgba(52,211,153,.85),rgba(52,211,153,0) 70%);transition:all .6s}
input[type=range]{width:100%;accent-color:#22d3ee;margin-top:18px}
.lagbar{height:14px;border-radius:8px;background:rgba(148,163,184,.15);overflow:hidden;margin-top:14px}
.lagbar>i{display:block;height:100%;background:linear-gradient(90deg,#22d3ee,#34d399);transition:width .5s;box-shadow:0 0 14px #34d399}
.lagval{font-weight:900;font-size:40px;color:#fff;margin-top:6px}
/* --- giro --- */
.twist{margin-top:30px;padding:26px}
.twist .msg{margin-top:18px;font-family:system-ui;font-size:17px;line-height:1.6;color:#e2e8f0;min-height:56px;transition:opacity .4s}
.lesson{margin-top:18px;font-family:"IBM Plex Mono",monospace;font-size:13px;color:#a7f3d0;letter-spacing:.02em}
/* --- tarjetas --- */
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-top:30px;perspective:1200px}
.card{all:unset;cursor:pointer;height:240px;position:relative;transform-style:preserve-3d;transition:transform .8s cubic-bezier(.2,.8,.2,1)}
.card.flip{transform:rotateY(180deg)}
.face{position:absolute;inset:0;backface-visibility:hidden;-webkit-backface-visibility:hidden;border-radius:20px;padding:22px;
  display:flex;flex-direction:column;justify-content:flex-end;border:1px solid rgba(148,163,184,.16);overflow:hidden}
.front{background:linear-gradient(160deg,rgba(14,165,233,.35),rgba(99,102,241,.25) 60%,rgba(2,6,23,.8))}
.front .t{font-weight:900;font-size:22px;color:#fff}.front .f{font-family:system-ui;font-size:14px;color:#cbd5e1;margin-top:8px}
.front .em{position:absolute;top:18px;left:20px;width:46px;height:46px;color:#e0f2fe;filter:drop-shadow(0 6px 18px rgba(56,189,248,.5))}
.front .em svg,.ic svg{width:100%;height:100%}
.ico{display:inline-flex;gap:2px;vertical-align:-4px;font-style:normal}.ico svg{width:18px;height:18px}
.flow:not(.live) .drop{animation-play-state:paused}
.back{transform:rotateY(180deg);background:linear-gradient(160deg,rgba(168,85,247,.35),rgba(2,6,23,.9));font-family:system-ui;
  font-size:15px;line-height:1.55;color:#f1f5f9;justify-content:center}
/* --- años necesarios --- */
.need{margin-top:30px;padding:28px}
.nrow{margin-bottom:30px}.nl{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.08em;color:#94a3b8;margin-bottom:8px}
.ntrack{position:relative;height:22px;border-radius:12px;background:rgba(148,163,184,.12);overflow:visible}
.nfill{height:100%;border-radius:12px;width:0;transition:width 1.6s cubic-bezier(.2,.8,.2,1)}
.nmark{position:absolute;top:-8px;bottom:-8px;width:2px;background:#f8fafc;box-shadow:0 0 10px #fff}
.nmark span{position:absolute;top:calc(100% + 4px);left:8px;white-space:nowrap;text-align:left;font-family:"IBM Plex Mono",monospace;font-size:11px;color:#f8fafc}
.nv{font-family:"IBM Plex Mono",monospace;font-size:13px;color:#e2e8f0;margin-top:6px}
/* --- cierre --- */
.end{text-align:center;padding:80px 20px 40px}
.end h2{margin-left:auto;margin-right:auto}
.end p{margin:0 auto 30px}
.end .row{justify-content:center}
.cta{all:unset;cursor:pointer;font-weight:800;font-size:16px;padding:16px 28px;border-radius:16px;color:#fff;
  background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7);box-shadow:0 14px 40px -12px rgba(99,102,241,.95);transition:all .3s}
.cta:hover{transform:translateY(-3px) scale(1.03);box-shadow:0 0 50px -6px rgba(168,85,247,.95)}
.cta.ghost{background:rgba(2,6,23,.6);border:1px solid rgba(56,189,248,.5);box-shadow:none}
.foot{margin-top:46px;font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:#64748b;line-height:1.8}
.prep{padding:40px;text-align:center;font-family:"IBM Plex Mono",monospace;color:#7dd3fc}
@media (max-width:860px){.sats,.cards{grid-template-columns:1fr 1fr}.mapwrap,.river,.gridwrap{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}*{animation:none!important}.flow .drop{display:none}}
"""

_JS = r"""
function esc(s){ return String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }
function color(v, lim){ // franjas: azul ↔ rojo
  const x = Math.max(-1, Math.min(1, v / lim));
  const cold = [[12,42,107],[29,78,216],[125,211,252]], warm = [[253,164,175],[225,29,72],[127,29,29]];
  const lerp = (a,b,t) => a.map((v,i) => Math.round(v + (b[i]-v)*t));
  let c;
  if (x < 0){ const t = -x; c = t < .5 ? lerp(cold[2], cold[1], t*2) : lerp(cold[1], cold[0], (t-.5)*2); }
  else { const t = x; c = t < .5 ? lerp([226,232,240], warm[1], t*2) : lerp(warm[1], warm[2], (t-.5)*2); }
  return `rgb(${c})`;
}
const IC = {sat:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="6" height="6" rx="1"/><path d="M3 6l4 4M17 14l4 4M6 3l4 4M14 17l4 4"/><path d="M4 20a6 6 0 0 1 4-4"/></svg>`,temp:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/><path d="M12 9v7"/></svg>`,leaf:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15"/><path d="M5 19l7-7"/></svg>`,fish:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12c3-5 9-6 13-3l5-3v12l-5-3c-4 3-10 2-13-3z"/><circle cx="8" cy="11" r=".8" fill="currentColor"/></svg>`,coral:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21V11M12 11c0-3-3-4-3-7M12 11c0-3 3-4 3-7M12 15c-3 0-5-2-6-5M12 15c3 0 5-2 6-5"/></svg>`,storm:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 8a8 8 0 0 0-14-2M4 16a8 8 0 0 0 14 2"/><circle cx="12" cy="12" r="3"/></svg>`,wave:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12c3-3 5-3 8 0s5 3 8 0 3-2 4-2M2 17c3-3 5-3 8 0s5 3 8 0 3-2 4-2M2 7c3-3 5-3 8 0s5 3 8 0 3-2 4-2"/></svg>`,globe:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>`,chart:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>`};
  const ICON = {up: "▲", down: "▼", flat: "■"};

export default function(component){
  const {data, parentElement, setTriggerValue} = component;
  const root = parentElement.querySelector(".st-root");
  const T = data.t;
  if (!data.ready){ root.innerHTML = `<div class="prep">${esc(T.preparing)}</div>`; return; }
  const lim = Math.max(...data.stripes.map(s => Math.abs(s.anom))) || 1;
  root.innerHTML = `
  <section class="hero">
    <div class="bg" style="background-image:url('${data.hero_img}')"></div><div class="shade"></div>
    <div class="inner"><div class="kick">${esc(T.hero_kicker)}</div><h1>${esc(T.hero_title)}</h1>
      <p class="lead">${esc(T.hero_lead)}</p>
      <div class="scroll"><span class="mouse"></span>${esc(T.hero_scroll)}</div></div>
  </section>

  <section class="reveal"><div class="kick">${esc(T.c1_k)}</div><h2>${esc(T.c1_t)}</h2><p class="lead">${esc(T.c1_p)}</p>
    <div class="sats">${T.sats.map((s,i) => `<button class="sat" data-i="${i}"><span class="orb"></span>
      <div class="y">${esc(s.y)}</div><div class="n">${esc(s.n)}</div></button>`).join("")}</div>
    <div class="satinfo glass">${esc(T.sats[0].d)}</div><div class="hint">${esc(T.c1_hint)}</div></section>

  <section class="reveal"><div class="kick">${esc(T.c2_k)}</div><h2>${esc(T.c2_t)}</h2><p class="lead">${esc(T.c2_p)}</p>
    <div class="stripes">${data.stripes.map(s => `<div class="stripe" style="background:${color(s.anom, lim)}"
       title="${s.year}: ${s.anom >= 0 ? "+" : ""}${s.anom.toFixed(2)} °C"></div>`).join("")}</div>
    <div class="years mono"><span>${data.stripes[0].year}</span><span>${data.stripes[data.stripes.length-1].year}</span></div>
    <div class="row"><button class="btn on" data-act="play">▶ ${esc(T.c2_play)}</button>
      <div class="yearnow">—</div><div class="anomnow mono"></div></div>
    <div class="note">${esc(T.c2_jump)}</div>
    <div class="gridwrap glass"><div><div class="kick" style="margin-bottom:8px">${esc(T.c2_grid_t)}</div>
        <div class="big"><span class="gn">${data.extreme.before}</span><small>/ 10</small></div>
        <div class="hint">${esc(T.c2_grid_cap)}</div>
        <div class="row"><button class="btn on" data-g="before">${esc(T.c2_grid_before)}</button>
          <button class="btn" data-g="after">${esc(T.c2_grid_after)}</button></div></div>
      <div class="dots">${Array.from({length: 10}, () => '<span class="dot"></span>').join("")}</div></div></section>

  <section class="reveal"><div class="kick">${esc(T.c3_k)}</div><h2>${esc(T.c3_t)}</h2><p class="lead">${esc(T.c3_p)}</p>
    <div class="mapwrap"><svg class="map" viewBox="0 0 ${data.map.w} ${data.map.h}">
        <path class="land" d="${data.map.land}"/><path class="gulf" d="${data.map.gulf}"/>
        ${data.regions.map(r => `<path class="reg" data-id="${r.id}" d="${r.path}" fill="${r.color}"/>`).join("")}</svg>
      <div class="panel glass"></div></div></section>

  <section class="reveal"><div class="kick">${esc(T.c4_k)}</div><h2>${esc(T.c4_t)}</h2><p class="lead">${esc(T.c4_p)}</p>
    <div class="river glass"><div class="flow"><span class="lab" style="left:12px">${esc(data.river.basin)}</span>
        <span class="lab" style="right:12px">${esc(data.river.sea)}</span><span class="bloom"></span></div>
      <div><div class="kick" style="margin-bottom:4px">${esc(T.c4_slider)}</div><div class="lagval">1</div>
        <div class="lagbar"><i></i></div><div class="mono lagtxt" style="margin-top:8px;color:#a7f3d0"></div>
        <input type="range" min="0" max="4" step="1" value="1"></div></div>
    <div class="note">${esc(T.c4_warn)}</div></section>

  <section class="reveal"><div class="kick">${esc(T.c5_k)}</div><h2>${esc(T.c5_t)}</h2><p class="lead">${esc(T.c5_p)}</p>
    <div class="twist glass"><div class="row" style="margin-top:0"><button class="btn on" data-s="one"><i class="ico">${IC.sat}</i> ${esc(T.c5_one)}</button>
        <button class="btn" data-s="two"><i class="ico">${IC.sat}${IC.sat}</i> ${esc(T.c5_two)}</button></div>
      <svg class="map" style="margin-top:20px" viewBox="0 0 ${data.map.w} ${data.map.h}">
        <path class="land" d="${data.map.land}"/><path class="gulf" d="${data.map.gulf}"/>
        ${data.regions.map(r => `<path class="reg tw" data-id="${r.id}" d="${r.path}"/>`).join("")}</svg>
      <div class="msg"></div><div class="lesson">◆ ${esc(T.c5_lesson)}</div></div></section>

  <section class="reveal"><div class="kick">${esc(T.c6_k)}</div><h2>${esc(T.c6_t)}</h2>
    <div class="cards">${T.cards.map((c,i) => `<button class="card"><div class="face front"><span class="em">${[IC.fish, IC.coral, IC.storm, IC.wave][i]}</span>
        <div class="t">${esc(c.t)}</div><div class="f">${esc(c.f)}</div></div>
        <div class="face back">${esc(c.b)}</div></button>`).join("")}</div><div class="hint">${esc(T.c6_hint)}</div></section>

  <section class="reveal"><div class="kick">${esc(T.c7_k)}</div><h2>${esc(T.c7_t)}</h2><p class="lead">${esc(T.c7_p)}</p>
    <div class="need glass">
      ${[["sst", T.c7_need_sst, "linear-gradient(90deg,#fb7185,#fbbf24)"], ["chl", T.c7_need_chl, "linear-gradient(90deg,#22d3ee,#a78bfa)"]].map(([k, lb, g]) => `
      <div class="nrow"><div class="nl">${esc(lb)}</div><div class="ntrack">
        <div class="nfill" data-w="${Math.min(100, 100 * data.need[k] / data.need.scale)}" style="background:${g}"></div>
        <div class="nmark" style="left:${100 * data.need.have / data.need.scale}%"><span>${data.need.have} ${esc(T.c7_have)}</span></div></div>
        <div class="nv">≈ ${Math.round(data.need[k])}</div></div>`).join("")}</div></section>

  <section class="reveal end"><h2>${esc(T.end_t)}</h2><p class="lead">${esc(T.end_p)}</p>
    <div class="row"><button class="cta" data-nav="region"><i class="ico">${IC.globe}</i> ${esc(T.end_region)}</button>
      <button class="cta ghost" data-nav="analysis"><i class="ico">${IC.chart}</i> ${esc(T.end_analysis)}</button></div>
    <div class="foot">${esc(T.team)}<br>${esc(T.sources)}</div></section>`;

  // aparición al desplazarse
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting){ e.target.classList.add("in");
    const f = e.target.querySelectorAll(".nfill"); f.forEach(x => x.style.width = x.dataset.w + "%"); } }), {threshold: .15});
  root.querySelectorAll(".reveal").forEach(s => io.observe(s));

  // capítulo 1: satélites
  const info = root.querySelector(".satinfo");
  root.querySelectorAll(".sat").forEach(b => b.onclick = () => {
    root.querySelectorAll(".sat").forEach(x => x.classList.toggle("on", x === b));
    info.style.opacity = 0; setTimeout(() => { info.textContent = T.sats[+b.dataset.i].d; info.style.opacity = 1; }, 180); });
  root.querySelector(".sat").classList.add("on");

  // capítulo 2: franjas
  const stripes = [...root.querySelectorAll(".stripe")], yNow = root.querySelector(".yearnow"), aNow = root.querySelector(".anomnow");
  let timer = null;
  const play = () => { clearInterval(timer); stripes.forEach(s => s.classList.remove("show")); let i = 0;
    timer = setInterval(() => { if (i >= stripes.length){ clearInterval(timer); return; }
      stripes[i].classList.add("show"); const s = data.stripes[i]; yNow.textContent = s.year;
      aNow.innerHTML = `<span style="color:${color(s.anom, lim)}">${s.anom >= 0 ? "+" : ""}${s.anom.toFixed(2)} °C</span>`; i++; }, 170); };
  root.querySelector('[data-act="play"]').onclick = play;
  const io2 = new IntersectionObserver(es => { if (es[0].isIntersecting){ play(); io2.disconnect(); } }, {threshold: .5});
  io2.observe(root.querySelector(".stripes"));
  const dots = [...root.querySelectorAll(".dot")], gn = root.querySelector(".gn");
  const setGrid = k => { const n = data.extreme[k]; gn.textContent = n;
    root.querySelectorAll("[data-g]").forEach(b => b.classList.toggle("on", b.dataset.g === k));
    dots.forEach((d, i) => setTimeout(() => d.classList.toggle("hot", i < n), i * 70)); };
  root.querySelectorAll("[data-g]").forEach(b => b.onclick = () => setGrid(b.dataset.g)); setGrid("before");

  // capítulo 3: mapa
  const panel = root.querySelector(".panel");
  const lbl = k => ({up: T.up, down: T.down, flat: T.flat}[k]);
  const showReg = id => { const r = data.regions.find(x => x.id === id);
    root.querySelectorAll(".mapwrap .reg").forEach(p => p.classList.toggle("on", p.dataset.id === id));
    panel.innerHTML = `<div class="rn">${esc(r.name)}</div>
      <div class="ind"><span class="ic up">${IC.temp}</span><div><div class="lb">${esc(T.c3_temp)}</div><div class="vl ${r.sst}">${ICON[r.sst]} ${esc(lbl(r.sst))}</div></div></div>
      <div class="ind"><span class="ic" style="color:#34d399">${IC.leaf}</span><div><div class="lb">${esc(T.c3_chl)}</div><div class="vl ${r.chl}">${ICON[r.chl]} ${esc(lbl(r.chl))}</div></div></div>`; };
  root.querySelectorAll(".mapwrap .reg").forEach(p => { p.onclick = () => showReg(p.dataset.id); p.onmouseenter = () => showReg(p.dataset.id); });
  showReg(data.regions.find(r => r.id === "banco") ? "banco" : data.regions[0].id);

  // capítulo 4: lluvia → clorofila
  const lagIn = root.querySelector('input[type=range]'), flow = root.querySelector(".flow");
  for (let i = 0; i < 16; i++){ const d = document.createElement("span"); d.className = "drop";
    d.style.left = (Math.random() * 30) + "%"; d.style.top = (15 + Math.random() * 70) + "%";
    d.style.setProperty("--dist", (260 + Math.random() * 200) + "px");
    d.style.animationDuration = (2.5 + Math.random() * 2) + "s"; d.style.animationDelay = (-Math.random() * 4) + "s"; flow.appendChild(d); }
  const setLag = v => { const r = data.river.lags[v]; root.querySelector(".lagval").textContent = v;
    const max = Math.max(...data.river.lags.map(x => x.r));
    root.querySelector(".lagbar i").style.width = (100 * Math.max(0, r.r) / max) + "%";
    root.querySelector(".lagtxt").textContent = r.sig ? T.c4_strong : T.c4_weak;
    const b = root.querySelector(".bloom"); b.style.opacity = Math.max(.15, r.r / max); b.style.transform = `scale(${.6 + r.r / max * .7})`; };
  lagIn.oninput = () => setLag(+lagIn.value); setLag(1);
  new IntersectionObserver(es => flow.classList.toggle("live", es[0].isIntersecting)).observe(flow);

  // capítulo 5: uno o dos satélites
  const msg = root.querySelector(".twist .msg"), pal = {up: "#34d399", down: "#38bdf8", flat: "#475569"};
  const setSat = k => { root.querySelectorAll("[data-s]").forEach(b => b.classList.toggle("on", b.dataset.s === k));
    root.querySelectorAll(".tw").forEach(p => { const r = data.regions.find(x => x.id === p.dataset.id);
      p.style.fill = pal[k === "one" ? r.chl_modis : r.chl]; });
    msg.style.opacity = 0; setTimeout(() => { msg.textContent = k === "one" ? T.c5_one_msg : T.c5_two_msg; msg.style.opacity = 1; }, 200); };
  root.querySelectorAll("[data-s]").forEach(b => b.onclick = () => setSat(b.dataset.s)); setSat("one");

  // capítulo 6: tarjetas
  root.querySelectorAll(".card").forEach(c => c.onclick = () => c.classList.toggle("flip"));
  // cierre
  root.querySelectorAll("[data-nav]").forEach(b => b.onclick = () => setTriggerValue("nav", b.dataset.nav));
  return () => { clearInterval(timer); io.disconnect(); };
}
"""

_story = st.components.v2.component("mece_story", html=_HTML, css=_CSS, js=_JS)


def story(data: dict, on_nav=None, key: str = "story"):
    return _story(key=key, data=data, height="content", on_nav_change=on_nav or (lambda: None))


# ------------------------------------------------------------------- datos
def _project(lon, lat, box, w, h):
    lon0, lon1, lat0, lat1 = box
    x = (np.asarray(lon) - lon0) / (lon1 - lon0) * w
    y = (lat1 - np.asarray(lat)) / (lat1 - lat0) * h
    return x, y


def _path(geom, box, w, h, tol: float = 0.025) -> str:
    """Geometría → path SVG. Se simplifica (tol en grados) porque a ~800 px de ancho un
    detalle menor a 0.025° (~1 px) no se ve y el HTML pesaría cientos de KB."""
    geom = geom.simplify(tol, preserve_topology=True)
    out = []
    polys = getattr(geom, "geoms", [geom])
    for p in polys:
        if p.is_empty or p.geom_type != "Polygon" or p.area < 0.05:  # sin islotes diminutos
            continue
        for ring in [p.exterior]:  # sin huecos interiores (islas): solo ilustrativo
            x, y = _project(*ring.xy, box, w, h)
            if len(x) < 4:
                continue
            out.append("M" + "L".join(f"{a:.0f},{b:.0f}" for a, b in zip(x, y, strict=True)) + "Z")
    return "".join(out)


def build_story_data(results: dict | None, regions_geojson: dict | None, lang: str, texts: dict,
                     land_zip: str, hero_img: str) -> dict:
    """Prepara solo lo que el relato necesita (pocas cifras, todas de results.json)."""
    if not results or not regions_geojson:
        return {"ready": False, "t": texts}
    import geopandas as gpd
    import shapely
    from shapely.geometry import shape

    box, w, h = (-98.5, -79.5, 17.5, 31.5), 800, 590
    land = gpd.read_file(f"zip://{land_zip}", bbox=(box[0], box[2], box[1], box[3]))
    land_geom = shapely.clip_by_rect(shapely.union_all(land.geometry.values), box[0], box[2], box[1], box[3])
    feats = {f["properties"]["id"]: f for f in regions_geojson["features"] if f["properties"]["kind"] == "marine"}
    gulf_path = _path(shape(feats["gulf"]["geometry"]), box, w, h)

    def arrow(res: str) -> str:
        return "up" if res.startswith("increase") else ("down" if res.startswith("decrease") else "flat")

    trends = {(t["variable"], t["region"]): t for t in results["trends"]}
    drift = {d["region"]: d for d in results.get("drift", [])}
    regions = []
    for rid, f in feats.items():
        if rid == "gulf":
            continue
        sst = arrow(trends[("sst", rid)]["result"])
        chl_modis = arrow(trends[("chl", rid)]["result"])
        chl = arrow(drift[rid]["result"]) if rid in drift else chl_modis
        regions.append({"id": rid, "name": f["properties"].get(f"name_{lang}") or f["properties"]["name_es"],
                        "path": _path(shape(f["geometry"]), box, w, h), "sst": sst, "chl": chl,
                        "chl_modis": chl_modis,
                        "color": {"up": "#fb7185", "down": "#38bdf8", "flat": "#64748b"}[sst]})
    stripes = [{"year": int(a["anio"]), "anom": float(a["anomalia"])} for a in results["annual_anomalies"]
               if a["variable"] == "sst" and a["region"] == "gulf"]
    ext = next(e for e in results["extremes"] if e["variable"] == "sst" and e["region"] == "gulf")
    lags = sorted((c for c in results["corr_rain_chl"] if c["basin"] == "grijalva" and c["region"] == "bahia"),
                  key=lambda c: c["lag"])
    w_sst = np.median([x["years_needed"] for x in results["weatherhead"] if x["variable"] == "sst"])
    w_chl = np.median([x["years_needed"] for x in results["weatherhead"] if x["variable"] == "chl"])
    names = {k: v for k, v in (("bahia", feats["bahia"]["properties"]),)}
    return {
        "ready": True, "t": texts, "hero_img": hero_img,
        "stripes": sorted(stripes, key=lambda s: s["year"]),
        "extreme": {"before": int(round(ext["freq_early"] / 10)), "after": int(round(ext["freq_late"] / 10))},
        "map": {"w": w, "h": h, "land": _path(land_geom, box, w, h), "gulf": gulf_path},
        "regions": regions,
        "river": {"basin": "Grijalva–Usumacinta", "sea": names["bahia"].get(f"name_{lang}") or "Bahía de Campeche",
                  "lags": [{"r": float(c["r"]), "sig": bool(c["q"] < 0.05)} for c in lags]},
        "need": {"sst": float(w_sst), "chl": float(w_chl), "have": 23, "scale": float(max(w_chl, 60) * 1.1)},
    }


def json_safe(d):
    """Tipos de numpy → nativos y NaN/inf → None (JSON válido para el navegador)."""
    import math

    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [clean(v) for v in x]
        if isinstance(x, float) and not math.isfinite(x):
            return None
        return x

    return clean(json.loads(json.dumps(d, default=float)))
