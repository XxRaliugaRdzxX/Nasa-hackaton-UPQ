"""Marine Ecosystem Change Explorer · interfaz (D14/D16).

Solo UI y orquestación: toda la lógica vive en el paquete `mece`.
Ejecutar:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import xarray as xr

sys.path.insert(0, str(Path(__file__).resolve().parent))  # i18n local

from i18n import T  # noqa: E402

from mece.acquisition.data import DataUnavailable, RegionNotPrepared, fetch_dataset, read_status  # noqa: E402
from mece.catalog import CATALOG, default_region_id, load_regions, store_for_bbox  # noqa: E402
from mece.config import get_settings  # noqa: E402
from mece.statistics.analysis import (  # noqa: E402
    SEASONS,
    TrendResult,
    compute_anomalies,
    percent_per_decade,
    regional_series,
    result_cache_key,
    trend_map,
    trend_test,
)
from mece.visualization.figures import coast_lines, fig_globe, fig_series, fig_trend_map  # noqa: E402

st.set_page_config(
    page_title="Marine Ecosystem Change Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SETTINGS = get_settings()
DATA = SETTINGS.data_dir
REGIONS = load_regions()
PLOT_CFG = {"displayModeBar": False, "responsive": True}

# ------------------------------------------------------------------ estilo
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{--page:#0d0d0d;--surface:#1a1a19;--surface-2:#222221;--ink:#f0efec;--ink-2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--baseline:#383835;--accent:#3987e5;--accent-2:#d95926;
--border:rgba(255,255,255,.10);--display:"Archivo",system-ui,sans-serif;--mono:"IBM Plex Mono",ui-monospace,monospace}
html,body,[data-testid="stAppViewContainer"]{background:var(--page)!important;color:var(--ink)}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],footer,#MainMenu{display:none!important}
.block-container{max-width:1280px;padding:0 20px 40px!important}
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .card-marker){
  background:var(--surface);border:1px solid var(--border)!important;border-radius:10px}
[data-testid="stWidgetLabel"] p{font-family:var(--mono)!important;font-size:11px!important;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted)!important}
div[data-baseweb="select"]>div{background:var(--surface-2)!important;border-color:var(--baseline)!important}
.mece-header{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px;padding:18px 0 10px}
.mece-brand h1{font-family:var(--display);font-weight:800;font-size:21px;letter-spacing:.04em;margin:0;
  text-transform:uppercase;line-height:1.15;color:var(--ink)}
.mece-brand .sub{color:var(--muted);font-family:var(--mono);font-size:12px}
.mece-badge{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:#0b0b0b;background:#fab219;
  padding:4px 10px;border-radius:4px;font-weight:500;white-space:nowrap;display:inline-block}
.mece-badge.ok{background:#0ca30c;color:#fff}
.hr{border-bottom:1px solid var(--border);margin:4px 0 18px}
[data-testid="stMarkdownContainer"] p.eyebrow{font-size:11px!important;line-height:1.4}
[data-testid="stMarkdownContainer"] p.case-text{font-size:14.5px!important;line-height:1.55}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.12em;color:var(--accent);text-transform:uppercase;margin:0 0 6px}
.case-title{font-family:var(--display);font-weight:700;font-size:25px;margin:0 0 4px;line-height:1.2;color:var(--ink)}
.case-region{font-family:var(--mono);font-size:12px;color:var(--muted);margin-bottom:10px}
.case-text{color:var(--ink-2);font-size:14.5px;max-width:46ch;margin:0 0 10px}
.specs{border-top:1px solid var(--grid);margin-top:4px;padding-top:10px;display:grid;grid-template-columns:auto 1fr;gap:6px 16px;font-size:13px}
.specs .dt{color:var(--muted);font-family:var(--mono);font-size:12px}.specs .dd{color:var(--ink-2)}
.hint{font-family:var(--mono);font-size:12px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:6px 0 18px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 18px}
.kpi .l{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.kpi .v{font-size:28px;font-weight:700;line-height:1.25;margin-top:2px;color:var(--ink)}
.kpi .u{font-size:13px;color:var(--ink-2);font-weight:400}
.kpi .f{display:flex;align-items:center;gap:6px;font-size:12px;margin-top:4px;color:var(--ink-2)}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.chart-h{font-family:var(--display);font-weight:700;font-size:15px;margin:0;color:var(--ink)}
.chart-sub{color:var(--muted);font-size:12.5px;margin:2px 0 4px}
.chart-src{font-family:var(--mono);font-size:11px;color:var(--muted);border-top:1px solid var(--grid);padding-top:8px;margin-top:2px}
.limit{margin-top:18px;border-left:3px solid var(--accent-2);background:var(--surface);border-radius:0 10px 10px 0;
  padding:14px 18px;font-size:13.5px;color:var(--ink-2);max-width:95ch}
.limit strong{color:var(--ink)}
.run-note{font-family:var(--mono);font-size:11px;color:var(--muted);text-align:right;padding-top:26px}
.status{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:16px}
.st-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px}
.st-card .t{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.st-card .b{font-size:14px;color:var(--ink);margin-top:4px}.st-card .s{font-size:12px;color:var(--ink-2)}
.bar{height:4px;background:var(--grid);border-radius:4px;margin-top:8px;overflow:hidden}
.bar>span{display:block;height:100%;background:var(--accent)}
.notready{background:var(--surface);border:1px dashed var(--baseline);border-radius:10px;padding:26px;color:var(--ink-2)}
.notready h3{font-family:var(--display);color:var(--ink);margin:0 0 6px}
.mece-footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--border);font-family:var(--mono);
  font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:6px 24px}
div.stButton>button[kind="primary"]{font-family:var(--display);font-weight:700;font-size:15px;border-radius:8px;
  padding:10px 22px;background:var(--accent);border:none}
div.stButton>button[kind="primary"]:hover{background:#2a78d6}
[data-testid="stSegmentedControl"] button{font-family:var(--mono)!important;font-size:12px!important}
@media (max-width:980px){.kpis{grid-template-columns:repeat(2,1fr)}}
@media (max-width:460px){.kpis{grid-template-columns:1fr}}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ estado
ss = st.session_state
ss.setdefault("view", "region")
ss.setdefault("lang", "es")
ss.setdefault("case", default_region_id())
ss.setdefault("ds", "chl")
ss.setdefault("season", "all")


def t(key: str) -> str:
    return T[ss.lang].get(key, key)


def go_analysis() -> None:
    ss.view = "analysis"


def persist(name: str) -> str:
    """Widget con estado persistente aunque deje de mostrarse en otra vista.

    Streamlit borra el estado de un widget que no se dibuja; por eso el valor real
    vive en ss[name] y el widget usa la clave espejo '_w_<name>'.
    """
    wkey = f"_w_{name}"
    ss[wkey] = ss[name]

    def _sync() -> None:
        ss[name] = ss[wkey]

    persist.callbacks[wkey] = _sync
    return wkey


persist.callbacks = {}


def on(wkey: str):
    return persist.callbacks[wkey]


# ------------------------------------------------------------- datos y caché
@st.cache_resource(show_spinner=False)
def globe_field():
    p = DATA / "spatial" / "globe" / "sst_global_latest.nc"
    if not p.exists():
        return None, None
    with xr.open_dataarray(p) as da:
        return da.load(), da.attrs.get("date")


@st.cache_data(show_spinner=False, max_entries=16)
def globe_figure(active: str, lang: str):
    field, _ = globe_field()
    g = DATA / "spatial" / "globe"
    return fig_globe(
        list(REGIONS.values()),
        active,
        field=field,
        lang=lang,
        coast_path=g / "ne_110m_coastline.geojson",
        land_path=g / "ne_110m_land.geojson",
    )


@st.cache_data(show_spinner=False, max_entries=64)
def analysis_series(ds_id: str, bbox: tuple, t0: str, t1: str, season: str):
    da = fetch_dataset(ds_id, bbox, t0, t1, download_missing=False)
    if int(da.attrs.get("months_missing", 0)) > 0:  # nunca se calcula con datos incompletos
        raise DataUnavailable(f"{ds_id}: faltan {da.attrs['months_missing']} meses")
    anom = compute_anomalies(da)
    s = regional_series(anom, season)
    tr = trend_test(s)
    meta = {k: anom.attrs.get(k) for k in ("clim_mean", "anomaly_space", "clim_period")}
    meta["months_missing"] = int(da.attrs.get("months_missing", 0))
    return s, tr.as_dict(), meta


@st.cache_data(show_spinner=False, max_entries=32)
def analysis_map(ds_id: str, bbox: tuple, t0: str, t1: str, season: str):
    """Mapa de tendencia: carga el precálculo o lo calcula (a 0.25° si es grande)."""
    from mece.config import get_settings as _gs

    key = result_cache_key(ds_id, bbox, t0, t1, season)
    if (_gs().data_dir / "results" / f"{key}.nc").exists():
        return trend_map(None, cache_key=key), False
    da = fetch_dataset(ds_id, bbox, t0, t1, download_missing=False)
    anom = compute_anomalies(da)
    if season != "all":
        anom = anom.sel(time=anom["time"].dt.month.isin(SEASONS[season]))
    reduced = False
    res = float(abs(anom["lat"].diff("lat").mean()))
    if anom.size > 1_500_000 and res < 0.2:
        f = max(2, int(round(0.25 / res)))
        anom = anom.coarsen(lat=f, lon=f, boundary="trim").mean()
        key += "_r025"
        reduced = True
    min_valid = max(24, int(0.7 * anom.sizes["time"]))
    return trend_map(anom, min_valid=min_valid, cache_key=key), reduced


@st.cache_data(show_spinner=False, max_entries=16)
def coast_for(bbox: tuple):
    land = DATA / "raw" / "ancillary" / "natural_earth" / "ne_10m_land.zip"
    return coast_lines(tuple(bbox), str(land))


def fmt_p(p: float) -> str:
    if not np.isfinite(p):
        return "—"
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def sgn(v: float, d: int) -> str:
    return "—" if not np.isfinite(v) else f"{'+' if v >= 0 else '−'}{abs(v):.{d}f}"


# ------------------------------------------------------------------ encabezado
status = read_status()
any_ready = any(v.get("state") == "ready" for k in CATALOG for v in status.get(k, {}).values())
badge = (
    f'<span class="mece-badge ok">{t("badge_real")}</span>'
    if any_ready
    else f'<span class="mece-badge">{t("badge_prep")}</span>'
)
h1, h2, h3 = st.columns([0.46, 0.34, 0.20], vertical_alignment="center")
with h1:
    st.markdown(
        f'<div class="mece-header"><div class="mece-brand"><h1>Marine Ecosystem Change Explorer</h1>'
        f'<span class="sub">{t("brand_sub")}</span></div></div>',
        unsafe_allow_html=True,
    )
with h2:
    st.segmented_control(
        "view",
        ["region", "analysis"],
        key="view",
        label_visibility="collapsed",
        format_func=lambda v: t("nav_region") if v == "region" else t("nav_analysis"),
    )
with h3:
    c1, c2 = st.columns([0.45, 0.55], vertical_alignment="center")
    with c1:
        st.segmented_control(
            "lang", ["es", "en"], key="lang", label_visibility="collapsed", format_func=str.upper
        )
    with c2:
        st.markdown(badge, unsafe_allow_html=True)
st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
if ss.view is None:
    ss.view = "region"
if ss.lang is None:
    ss.lang = "es"

reg = REGIONS[ss.case]
lang = ss.lang


def status_cards() -> str:
    cards = []
    for ds_id, spec in CATALOG.items():
        store = store_for_bbox(reg.bbox)
        info = status.get(ds_id, {}).get(store.id if store else "", {})
        state = info.get("state", "empty")
        label = spec.label_en if lang == "en" else spec.label_es
        if state == "ready":
            body = f"{info.get('n_months', 0)} {t('months')} · {info.get('first_month', '')} → {info.get('last_month', '')}"
            pct = 100
        elif state == "downloading":
            if "total_days" in info:
                tot, done = info.get("total_days", 1) or 1, info.get("done_days", 0)
            else:
                tot, done = info.get("total_months", 1) or 1, info.get("done_months", 0)
            pct = int(100 * done / tot)
            body = f"{t('downloading')} · {pct} %"
        else:
            body, pct = t("empty"), 0
        cards.append(
            f'<div class="st-card"><div class="t">{label}</div><div class="b">{body}</div>'
            f'<div class="s">{(spec.source_en if lang == "en" else spec.source_es)}</div>'
            f'<div class="bar"><span style="width:{pct}%"></span></div></div>'
        )
    _, gdate = globe_field()
    if gdate:
        cards.append(
            f'<div class="st-card"><div class="t">{t("globe_date")}</div><div class="b">{gdate}</div>'
            f'<div class="s">GHRSST MUR25 v4.2 · NASA PO.DAAC</div><div class="bar"><span style="width:100%"></span></div></div>'
        )
    return f'<div class="status">{"".join(cards)}</div>'


# =============================================================== VISTA REGIÓN
if ss.view == "region":
    left, right = st.columns([0.36, 0.64], gap="large")
    with left, st.container(border=True):
        st.markdown('<span class="card-marker"></span>', unsafe_allow_html=True)
        wk = persist("case")
        st.selectbox(
            t("choose_region"),
            list(REGIONS),
            key=wk,
            on_change=on(wk),
            format_func=lambda c: REGIONS[c].name(lang),
        )
        reg = REGIONS[ss.case]
        b = reg.bbox
        ns = lambda v: f"{abs(v):.1f} {'N' if v >= 0 else 'S'}"  # noqa: E731
        ew = lambda v: f"{abs(v):.1f} {'W' if v < 0 else 'E'}"  # noqa: E731
        dsl = " · ".join(
            (CATALOG[d].label_en if lang == "en" else CATALOG[d].label_es) for d in reg.datasets
        )
        st.markdown(
            f'<p class="eyebrow">{t("eyebrow_case")}</p>'
            f'<div class="case-title">{reg.name(lang)}</div>'
            f'<div class="case-region">{reg.region_en if lang == "en" else reg.region_es}</div>'
            f'<p class="case-text">{reg.summary_en if lang == "en" else reg.summary_es}</p>'
            f'<div class="specs"><span class="dt">{t("bbox")}</span><span class="dd">{ns(b[0])}–{ns(b[1])} · {ew(b[2])}–{ew(b[3])}</span>'
            f'<span class="dt">{t("period")}</span><span class="dd">{reg.t0} — {reg.t1}</span>'
            f'<span class="dt">{t("variables")}</span><span class="dd">{dsl}</span>'
            f'<span class="dt">{t("method")}</span><span class="dd">{t("method_val")}</span></div>',
            unsafe_allow_html=True,
        )
        st.button(t("analyze"), type="primary", on_click=go_analysis)
    with right, st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><p class="eyebrow">{t("eyebrow_catalog")}</p>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(globe_figure(ss.case, lang), config=PLOT_CFG, width="stretch", key="globe")
        st.markdown(f'<span class="hint">{t("globe_hint")}</span>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="eyebrow" style="margin-top:22px">{t("status_title")}</p>' + status_cards(),
        unsafe_allow_html=True,
    )

# ============================================================== VISTA ANÁLISIS
else:
    y_min, y_max = int(reg.t0[:4]), int(reg.t1[:4])
    ss.setdefault("y0", y_min)
    ss.setdefault("y1", y_max)
    if not (y_min <= ss.y0 <= y_max):
        ss.y0 = y_min
    if not (y_min <= ss.y1 <= y_max):
        ss.y1 = y_max
    with st.container(border=True):
        st.markdown('<span class="card-marker"></span>', unsafe_allow_html=True)
        c = st.columns([0.24, 0.12, 0.12, 0.18, 0.34], vertical_alignment="bottom")
        with c[0]:
            if ss.ds not in reg.datasets:
                ss.ds = reg.datasets[0]
            wk = persist("ds")
            st.selectbox(
                t("variable"),
                list(reg.datasets),
                key=wk,
                on_change=on(wk),
                format_func=lambda d: CATALOG[d].label_en if lang == "en" else CATALOG[d].label_es,
            )
        years = list(range(y_min, y_max + 1))
        with c[1]:
            wk = persist("y0")
            st.selectbox(t("from"), years, key=wk, on_change=on(wk))
        with c[2]:
            wk = persist("y1")
            st.selectbox(t("to"), years, key=wk, on_change=on(wk))
        with c[3]:
            wk = persist("season")
            st.selectbox(
                t("season"),
                ["all", "wet", "dry"],
                key=wk,
                on_change=on(wk),
                format_func=lambda s: t(f"season_{s}"),
            )
        with c[4]:
            st.markdown(f'<div class="run-note">{t("run_note")}</div>', unsafe_allow_html=True)
    if ss.y0 > ss.y1:
        ss.y1 = ss.y0
    ds_id = ss.ds if ss.ds in reg.datasets else reg.datasets[0]
    spec = CATALOG[ds_id]
    t0, t1 = f"{ss.y0}-01", f"{ss.y1}-12"
    is_log = spec.log_transform
    try:
        with st.spinner(t("computing")):
            series, trd, meta = analysis_series(ds_id, reg.bbox, t0, t1, ss.season)
            tmap, reduced = analysis_map(ds_id, reg.bbox, t0, t1, ss.season)
    except (DataUnavailable, RegionNotPrepared, FileNotFoundError):
        st.markdown(
            f'<div class="notready"><h3>{t("not_ready_title")}</h3><p>{t("not_ready_body")}</p></div>'
            + status_cards(),
            unsafe_allow_html=True,
        )
        st.stop()

    tr = TrendResult(**trd)
    years_span = ss.y1 - ss.y0 + 1
    if is_log:
        kpi1, u1 = percent_per_decade(tr.slope_per_decade), "% " + t("per_decade")
        total = (10 ** (tr.slope_per_decade * years_span / 10) - 1) * 100
        kpi2, u2 = total, f"% · {ss.y0}–{ss.y1}"
        ci = (percent_per_decade(tr.ci_low), percent_per_decade(tr.ci_high))
        series_units, transform = "%", (lambda v: (np.power(10.0, v) - 1) * 100)
    else:
        kpi1, u1 = tr.slope_per_decade, f"{spec.units} {t('per_decade')}"
        clim = meta.get("clim_mean") or np.nan
        kpi2 = 100 * tr.slope_per_decade / clim if clim else np.nan
        u2 = f"% {t('per_decade')} · {t('clim')} {clim:.1f} {spec.units}"
        ci = (tr.ci_low, tr.ci_high)
        series_units, transform = spec.units, None
    sig_col = "#0ca30c" if tr.significant else "#898781"
    sig_txt = t("significant") if tr.significant else t("not_significant")
    if not tr.robust:
        sig_txt += f" · {t('sensitive')}"
    season_lbl = "" if ss.season == "all" else f" · {t('season_' + ss.season)}"
    st.markdown(
        f"""<div class="kpis">
<div class="kpi"><span class="l">{t("kpi_sen")}</span><div class="v">{sgn(kpi1, 3 if abs(kpi1) < 1 else 2)}</div>
<span class="f">{u1} · {t("ci")} [{sgn(ci[0], 2)}, {sgn(ci[1], 2)}]</span></div>
<div class="kpi"><span class="l">{t("kpi_rel")}</span><div class="v">{sgn(kpi2, 1)}<span class="u"> %</span></div>
<span class="f">{u2}</span></div>
<div class="kpi"><span class="l">{t("kpi_p")}</span><div class="v">{fmt_p(tr.p)}</div>
<span class="f"><span class="dot" style="background:{sig_col}"></span>{sig_txt} · z = {tr.z:.2f}</span></div>
<div class="kpi"><span class="l">{t("kpi_n")}</span><div class="v">{tr.n}</div>
<span class="f">{ss.y0}–{ss.y1}{season_lbl}</span></div></div>""",
        unsafe_allow_html=True,
    )

    tmap_disp = tmap.copy()
    map_units = spec.trend_units_en if lang == "en" else spec.trend_units_es
    if is_log:
        tmap_disp["slope"] = (np.power(10.0, tmap["slope"]) - 1) * 100
    src = spec.source_en if lang == "en" else spec.source_es
    m1, m2 = st.columns(2, gap="medium")
    with m1, st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><div class="chart-h">{t("map_title")}</div>'
            f'<div class="chart-sub">{t("map_sub")}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig_trend_map(tmap_disp, map_units, coast=coast_for(reg.bbox), marker=reg.marker),
            config=PLOT_CFG,
            width="stretch",
            key="map",
        )
        extra = f" · {t('map_reduced')}" if reduced else ""
        st.markdown(
            f'<div class="chart-src">{t("source")}: {src} · {tmap.attrs.get("period", "")} · '
            f"{tmap.attrs.get('n_pixels_significant', 0)}/{tmap.attrs.get('n_pixels_tested', 0)} px{extra}</div>",
            unsafe_allow_html=True,
        )
    with m2, st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><div class="chart-h">{t("ts_title")}</div>'
            f'<div class="chart-sub">{t("ts_sub")}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig_series(series, tr, series_units, labels=(t("anom"), t("sen")), transform=transform),
            config=PLOT_CFG,
            width="stretch",
            key="ts",
        )
        st.markdown(
            f'<div class="chart-src">{t("source")}: {src} · {tr.method} · '
            f"{t('clim')}: {meta.get('clim_period', '')}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="limit">{spec.limitation_en if lang == "en" else spec.limitation_es}</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    f'<div class="mece-footer"><span>{t("footer_1")}</span><span>{t("footer_2")}</span>'
    f"<span>{t('footer_3')}</span></div>",
    unsafe_allow_html=True,
)
_ = pd  # pandas disponible para extensiones del equipo
