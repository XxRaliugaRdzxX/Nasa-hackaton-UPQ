"""Tema visual global · 'Deep Ocean Mission Control'."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{
  --bg:#020617; --ink:#f1f5f9; --ink-2:#cbd5e1; --muted:#94a3b8; --dim:#64748b;
  --cyan:#22d3ee; --sky:#38bdf8; --blue:#3b82f6; --indigo:#6366f1; --violet:#a855f7; --pink:#ec4899;
  --amber:#fbbf24; --coral:#fb7185; --green:#34d399;
  --glass:linear-gradient(160deg,rgba(15,23,42,.78),rgba(15,23,42,.42));
  --stroke:rgba(148,163,184,.16);
  --display:"Archivo",system-ui,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
}
/* ---------- lienzo: espacio profundo + nebulosas + estrellas + rejilla HUD ---------- */
html,body{background:var(--bg)!important;color:var(--ink)}
/* el lienzo de Streamlit es transparente: deja ver la galaxia (#mece-galaxy, z-index -1) */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:transparent!important;color:var(--ink)}
.stApp::before{content:"";position:fixed;inset:-20%;z-index:0;pointer-events:none;
  background:
   radial-gradient(40% 35% at 12% 8%,rgba(56,189,248,.22),transparent 70%),
   radial-gradient(35% 30% at 92% 12%,rgba(168,85,247,.22),transparent 70%),
   radial-gradient(45% 40% at 60% 105%,rgba(20,184,166,.18),transparent 70%),
   radial-gradient(30% 25% at 30% 70%,rgba(236,72,153,.10),transparent 70%);
  animation:nebula 26s ease-in-out infinite alternate;filter:saturate(1.2)}
@keyframes nebula{0%{transform:translate3d(0,0,0) scale(1)}50%{transform:translate3d(-2%,1.5%,0) scale(1.05)}100%{transform:translate3d(2%,-1%,0) scale(1.02)}}
.stApp::after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.9;
  background-image:
   radial-gradient(1px 1px at 20px 30px,#fff,transparent),radial-gradient(1px 1px at 120px 80px,#bae6fd,transparent),
   radial-gradient(1.5px 1.5px at 210px 150px,#fff,transparent),radial-gradient(1px 1px at 300px 40px,#e9d5ff,transparent),
   radial-gradient(1px 1px at 380px 190px,#fff,transparent),radial-gradient(1.2px 1.2px at 460px 110px,#a5f3fc,transparent),
   linear-gradient(rgba(56,189,248,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(56,189,248,.035) 1px,transparent 1px);
  background-size:520px 240px,520px 240px,520px 240px,520px 240px,520px 240px,520px 240px,56px 56px,56px 56px;
  animation:twinkle 7s ease-in-out infinite alternate;
  -webkit-mask-image:radial-gradient(ellipse at 50% 30%,#000 30%,transparent 85%);mask-image:radial-gradient(ellipse at 50% 30%,#000 30%,transparent 85%)}
@keyframes twinkle{0%{opacity:.55}100%{opacity:1}}
[data-testid="stAppViewContainer"]>.main,.block-container{position:relative;z-index:1}
/* encabezado nativo: transparente; se ocultan sus acciones pero NO el botón para reabrir el menú
   lateral (vive dentro de stToolbar: ocultar stToolbar entero deja al usuario sin menú) */
[data-testid="stHeader"]{background:transparent!important;pointer-events:none}
[data-testid="stHeader"] [data-testid="stExpandSidebarButton"]{pointer-events:auto}
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],
[data-testid="stStatusWidget"],[data-testid="stDecoration"],footer,#MainMenu{display:none!important}
[data-testid="stExpandSidebarButton"]{position:fixed!important;top:14px;left:14px;z-index:1000002;
  width:46px!important;height:46px!important;border-radius:14px!important;display:grid!important;place-items:center;
  background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7)!important;color:#fff!important;border:none!important;
  box-shadow:0 0 0 1px rgba(255,255,255,.18) inset,0 10px 30px -8px rgba(99,102,241,.95)!important;
  animation:sbpulse 2.4s ease-in-out infinite;transition:transform .25s}
[data-testid="stExpandSidebarButton"]:hover{transform:scale(1.08)}
[data-testid="stExpandSidebarButton"] *{color:#fff!important}
@keyframes sbpulse{0%,100%{box-shadow:0 0 0 1px rgba(255,255,255,.18) inset,0 0 0 0 rgba(56,189,248,.55)}
  50%{box-shadow:0 0 0 1px rgba(255,255,255,.18) inset,0 0 0 10px rgba(56,189,248,0)}}
[data-testid="stSidebarCollapseButton"] button{color:#7dd3fc!important}

/* ---------- menú lateral ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(2,6,23,.94),rgba(9,16,38,.88))!important;
  border-right:1px solid rgba(56,189,248,.16);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
  box-shadow:12px 0 40px -20px rgba(14,165,233,.35)}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{background:transparent!important}
[data-testid="stSidebarUserContent"]{padding-top:18px}
.sb-brand{display:flex;align-items:center;gap:12px;padding:6px 4px 18px;margin-bottom:6px;border-bottom:1px solid rgba(148,163,184,.12)}
.sb-emblem svg{width:58px;height:58px;overflow:visible;filter:drop-shadow(0 0 16px rgba(56,189,248,.75))}
.sb-emblem .glow{transform-origin:40px 40px;animation:sbglow 3.2s ease-in-out infinite}
.sb-emblem .ring{transform-origin:40px 40px;transform:rotate(-18deg)}
.sb-emblem .orbit{transform-origin:40px 40px;animation:sborbit 5s linear infinite}
.sb-emblem .spark{transform-origin:62px 20px;animation:sbspark 2.6s ease-in-out infinite}
@keyframes sbglow{0%,100%{opacity:.25;transform:scale(1)}50%{opacity:.55;transform:scale(1.25)}}
@keyframes sborbit{from{transform:rotate(-18deg) rotate(0) scaleY(1)}to{transform:rotate(-18deg) rotate(360deg)}}
@keyframes sbspark{0%,100%{opacity:.2;transform:scale(.6)}50%{opacity:1;transform:scale(1.1)}}
.sb-name{font-family:var(--display);font-weight:900;font-size:19px;letter-spacing:.02em;line-height:1.1;
  background:linear-gradient(90deg,#f0f9ff,#7dd3fc,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
.sb-tag{font-family:var(--mono);font-size:9.5px;color:#7dd3fc;letter-spacing:.04em;margin-top:3px;line-height:1.4}
p.sb-h{font-family:var(--mono);font-size:10px!important;letter-spacing:.22em;text-transform:uppercase;color:#64748b;margin:18px 0 8px 2px}
.st-key-nav [data-testid="stVerticalBlock"],.st-key-langs [data-testid="stVerticalBlock"]{gap:8px}
.st-key-langs button{justify-content:flex-start!important;border-radius:12px!important;padding:8px 14px!important;
  font-family:var(--mono)!important;font-size:13px!important;transition:all .3s cubic-bezier(.2,.8,.2,1)!important}
.st-key-langs button[kind="secondary"]{background:rgba(15,23,42,.5)!important;border:1px solid rgba(148,163,184,.14)!important;color:#cbd5e1!important}
.st-key-langs button[kind="secondary"]:hover{transform:translateX(5px);color:#fff!important;border-color:rgba(56,189,248,.6)!important;
  box-shadow:0 0 22px -8px rgba(56,189,248,.9)}
.st-key-langs button[kind="primary"]{border:none!important;color:#fff!important;
  background:linear-gradient(135deg,rgba(14,165,233,.85),rgba(99,102,241,.85))!important;box-shadow:0 8px 24px -10px rgba(99,102,241,.95)!important}
.st-key-nav button{justify-content:flex-start!important;border-radius:14px!important;padding:12px 16px!important;
  font-family:var(--display)!important;font-weight:700!important;font-size:15px!important;letter-spacing:.02em;
  transition:all .3s cubic-bezier(.2,.8,.2,1)!important;position:relative;overflow:hidden}
.st-key-nav button[kind="secondary"]{background:rgba(15,23,42,.55)!important;border:1px solid rgba(148,163,184,.14)!important;color:#cbd5e1!important}
.st-key-nav button[kind="secondary"]:hover{transform:translateX(5px);color:#fff!important;border-color:rgba(56,189,248,.6)!important;
  background:rgba(56,189,248,.12)!important;box-shadow:0 0 26px -8px rgba(56,189,248,.9)}
.st-key-nav button[kind="primary"]{border:none!important;color:#fff!important;
  background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7)!important;background-size:200% 100%!important;
  box-shadow:0 0 0 1px rgba(255,255,255,.15) inset,0 10px 30px -10px rgba(99,102,241,.95)!important;animation:flow 6s ease infinite}
.st-key-nav button[kind="primary"]::before{content:"";position:absolute;left:0;top:18%;bottom:18%;width:3px;border-radius:3px;
  background:#e0f2fe;box-shadow:0 0 12px #e0f2fe}
.st-key-nav button span[data-testid="stIconMaterial"]{font-size:20px!important;margin-right:6px}

.block-container{max-width:1360px;padding:10px 26px 50px!important}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-thumb{background:linear-gradient(var(--sky),var(--violet));border-radius:10px}
::-webkit-scrollbar-track{background:#020617}
::selection{background:rgba(56,189,248,.35)}

/* ---------- entrada escalonada de bloques ---------- */
[data-testid="stVerticalBlock"]>div{animation:rise .7s cubic-bezier(.2,.8,.2,1) both}
[data-testid="stVerticalBlock"]>div:nth-child(2){animation-delay:.05s}
[data-testid="stVerticalBlock"]>div:nth-child(3){animation-delay:.1s}
[data-testid="stVerticalBlock"]>div:nth-child(4){animation-delay:.15s}
[data-testid="stVerticalBlock"]>div:nth-child(5){animation-delay:.2s}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

/* ---------- paneles de vidrio ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-marker){
  background:var(--glass)!important;border:1px solid var(--stroke)!important;border-radius:20px!important;
  backdrop-filter:blur(16px) saturate(140%);-webkit-backdrop-filter:blur(16px) saturate(140%);
  box-shadow:0 1px 0 rgba(255,255,255,.05) inset,0 30px 60px -35px rgba(0,0,0,.9);
  transition:transform .35s cubic-bezier(.2,.8,.2,1),box-shadow .35s,border-color .35s;position:relative}
[data-testid="stVerticalBlockBorderWrapper"]:has(.card-marker):hover{
  transform:translateY(-3px);border-color:rgba(56,189,248,.45)!important;
  box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 0 0 1px rgba(56,189,248,.15),0 30px 70px -30px rgba(14,165,233,.55)}
.card-marker{display:none}

/* ---------- menú (segmented control) ---------- */
[data-testid="stButtonGroup"]{background:rgba(2,6,23,.55);border:1px solid var(--stroke);border-radius:16px;padding:5px;
  backdrop-filter:blur(10px);box-shadow:0 10px 30px -15px rgba(56,189,248,.5)}
[data-testid="stButtonGroup"] button{border:none!important;border-radius:12px!important;background:transparent!important;
  color:var(--ink-2)!important;font-family:var(--mono)!important;font-size:12.5px!important;letter-spacing:.04em;
  transition:all .3s cubic-bezier(.2,.8,.2,1)!important;padding:8px 18px!important}
[data-testid="stButtonGroup"] button:hover{color:#fff!important;background:rgba(56,189,248,.14)!important;
  transform:translateY(-1px);box-shadow:0 0 20px -6px rgba(56,189,248,.8)}
[data-testid="stButtonGroup"] button[kind*="Active"],[data-testid="stButtonGroup"] button[aria-checked="true"]{
  color:#fff!important;background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7)!important;background-size:200% 100%!important;
  box-shadow:0 0 0 1px rgba(255,255,255,.15) inset,0 8px 26px -8px rgba(99,102,241,.9)!important;animation:flow 6s ease infinite}
@keyframes flow{0%,100%{background-position:0 0}50%{background-position:100% 0}}

/* ---------- controles ---------- */
[data-testid="stWidgetLabel"] p{font-family:var(--mono)!important;font-size:10.5px!important;letter-spacing:.14em;
  text-transform:uppercase;color:#7dd3fc!important}
div[data-baseweb="select"]>div{background:rgba(2,6,23,.6)!important;border:1px solid rgba(148,163,184,.22)!important;
  border-radius:12px!important;transition:all .25s;color:var(--ink)!important}
div[data-baseweb="select"]>div:hover{border-color:rgba(56,189,248,.7)!important;box-shadow:0 0 18px -6px rgba(56,189,248,.8)}
div[data-baseweb="popover"] ul{background:#0b1224!important;border:1px solid rgba(56,189,248,.35)!important;border-radius:12px}
div[data-baseweb="popover"] li:hover{background:rgba(56,189,248,.18)!important}
div.stButton>button[kind="primary"]{position:relative;overflow:hidden;border:none!important;border-radius:14px!important;
  font-family:var(--display)!important;font-weight:800!important;font-size:15px!important;letter-spacing:.02em;padding:12px 26px!important;
  background:linear-gradient(135deg,#0ea5e9,#6366f1 55%,#a855f7)!important;background-size:200% 100%!important;
  box-shadow:0 0 0 1px rgba(255,255,255,.15) inset,0 14px 34px -12px rgba(99,102,241,.95)!important;
  transition:all .3s cubic-bezier(.2,.8,.2,1)!important}
div.stButton>button[kind="primary"]::after{content:"";position:absolute;inset:0;
  background:linear-gradient(110deg,transparent 35%,rgba(255,255,255,.45) 50%,transparent 65%);transform:translateX(-120%);
  animation:sheen 3.6s ease-in-out infinite}
@keyframes sheen{0%,60%{transform:translateX(-120%)}100%{transform:translateX(120%)}}
div.stButton>button[kind="primary"]:hover{transform:translateY(-2px) scale(1.02);background-position:100% 0!important;
  box-shadow:0 0 40px -6px rgba(168,85,247,.95)!important}

/* ---------- tipografía de secciones ---------- */
.eyebrow{display:flex;align-items:center;gap:9px;font-family:var(--mono);font-size:10.5px!important;letter-spacing:.2em;
  color:#7dd3fc;text-transform:uppercase;margin:0 0 8px}
.eyebrow::before{content:"";width:22px;height:2px;border-radius:2px;background:linear-gradient(90deg,var(--cyan),var(--violet));
  box-shadow:0 0 10px var(--cyan)}
.case-title{font-family:var(--display);font-weight:900;font-size:clamp(24px,2.4vw,32px);line-height:1.08;margin:2px 0 6px;
  background:linear-gradient(90deg,#f0f9ff,#7dd3fc 60%,#c4b5fd);-webkit-background-clip:text;background-clip:text;color:transparent}
.case-region{font-family:var(--mono);font-size:11.5px;color:#a78bfa;letter-spacing:.06em;margin-bottom:12px}
p.case-text{color:var(--ink-2);font-size:14.5px!important;line-height:1.6;margin:0 0 14px}
.specs{display:grid;grid-template-columns:auto 1fr;gap:9px 16px;padding:14px 16px;border-radius:14px;
  background:rgba(2,6,23,.45);border:1px solid rgba(148,163,184,.12);font-size:13px;margin-bottom:16px}
.specs .dt{color:#64748b;font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;padding-top:2px}
.specs .dd{color:var(--ink)}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:999px;font-family:var(--mono);font-size:11px;
  margin:0 6px 6px 0;background:rgba(56,189,248,.12);border:1px solid rgba(56,189,248,.35);color:#bae6fd}
.chip.v{background:rgba(168,85,247,.12);border-color:rgba(168,85,247,.4);color:#e9d5ff}

/* ---------- cinta de telemetría ---------- */
.ticker{position:relative;overflow:hidden;border-radius:12px;border:1px solid rgba(56,189,248,.18);
  background:linear-gradient(90deg,rgba(2,6,23,.85),rgba(15,23,42,.6),rgba(2,6,23,.85));margin:4px 0 18px;height:34px}
.ticker::before,.ticker::after{content:"";position:absolute;top:0;bottom:0;width:80px;z-index:2}
.ticker::before{left:0;background:linear-gradient(90deg,#020617,transparent)}.ticker::after{right:0;background:linear-gradient(-90deg,#020617,transparent)}
.ticker-track{display:flex;gap:46px;white-space:nowrap;animation:tick 55s linear infinite;padding:8px 0;width:max-content}
.ticker:hover .ticker-track{animation-play-state:paused}
@keyframes tick{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.ticker-item{font-family:var(--mono);font-size:11.5px;color:#cbd5e1;letter-spacing:.04em}
.ticker-item b{color:#67e8f9;font-weight:600}.ticker-item i{color:#a78bfa;font-style:normal}

/* ---------- estado de datos ---------- */
.status{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin-top:6px}
.st-card{position:relative;overflow:hidden;padding:16px 18px;border-radius:16px;background:var(--glass);border:1px solid var(--stroke);
  transition:all .3s}
.st-card:hover{transform:translateY(-3px);border-color:rgba(56,189,248,.5);box-shadow:0 18px 40px -20px rgba(56,189,248,.7)}
.st-card .t{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;color:#7dd3fc;text-transform:uppercase}
.st-card .b{font-family:var(--display);font-weight:700;font-size:17px;color:#fff;margin-top:6px}
.st-card .s{font-family:var(--mono);font-size:11px;color:var(--muted);margin-top:3px}
.bar{height:5px;background:rgba(148,163,184,.14);border-radius:5px;margin-top:12px;overflow:hidden}
.bar>span{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,var(--cyan),var(--indigo),var(--violet));
  background-size:200% 100%;animation:flow 3s linear infinite;box-shadow:0 0 12px var(--cyan)}

/* ---------- gráficas ---------- */
.chart-h{font-family:var(--display);font-weight:800;font-size:17px;margin:0;color:#fff}
.chart-sub{color:var(--muted);font-size:12.5px;margin:3px 0 4px}
.chart-src{font-family:var(--mono);font-size:10.5px;color:var(--dim);border-top:1px solid rgba(148,163,184,.12);padding-top:10px;margin-top:2px}
.limit{margin-top:20px;position:relative;padding:16px 20px 16px 22px;border-radius:16px;font-size:13.5px;color:var(--ink-2);
  background:linear-gradient(90deg,rgba(251,191,36,.10),rgba(15,23,42,.55));border:1px solid rgba(251,191,36,.28)}
.limit::before{content:"";position:absolute;left:0;top:12px;bottom:12px;width:3px;border-radius:3px;
  background:linear-gradient(var(--amber),var(--coral));box-shadow:0 0 14px var(--amber)}
.limit strong{color:#fde68a}
.run-note{font-family:var(--mono);font-size:10.5px;color:var(--dim);text-align:right;padding-top:24px;line-height:1.5}
.notready{padding:30px;border-radius:20px;background:var(--glass);border:1px dashed rgba(56,189,248,.4);color:var(--ink-2)}
.notready h3{font-family:var(--display);color:#fff;margin:0 0 8px}
.mece-footer{margin-top:40px;padding-top:16px;border-top:1px solid rgba(148,163,184,.12);font-family:var(--mono);
  font-size:11px;color:var(--dim);display:flex;flex-wrap:wrap;gap:6px 26px}
.mece-footer span:hover{color:#7dd3fc}
.badge{display:inline-flex;align-items:center;gap:8px;font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;
  padding:7px 12px;border-radius:999px;white-space:nowrap;border:1px solid}
.badge.ok{color:#a7f3d0;background:rgba(16,185,129,.12);border-color:rgba(52,211,153,.45);box-shadow:0 0 22px -8px #34d399}
.badge.prep{color:#fde68a;background:rgba(251,191,36,.12);border-color:rgba(251,191,36,.45)}
.badge i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 10px currentColor;animation:blink 1.4s infinite}
@keyframes blink{50%{opacity:.3}}
.js-plotly-plot .rangeselector .button rect{rx:8px}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
</style>
"""
