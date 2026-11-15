"""Marine Ecosystem Change Explorer · interfaz (D14/D16).

Solo UI y orquestación: toda la lógica vive en el paquete `mece`.
Ejecutar:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))  # módulos locales del dashboard

from components import globe, kpis, mission_bar, region_cards  # noqa: E402
from i18n import T  # noqa: E402
from theme import CSS  # noqa: E402

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
from mece.visualization.figures import (  # noqa: E402
    coast_lines,
    fig_series,
    fig_stripes,
    fig_trend_map,
)

st.set_page_config(
    page_title="Marine Ecosystem Change Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SETTINGS = get_settings()
DATA = SETTINGS.data_dir
REGIONS = load_regions()
STATIC = Path(__file__).resolve().parent / "static" / "globe"
PLOT_CFG = {"displayModeBar": False, "responsive": True}
st.markdown(CSS, unsafe_allow_html=True)

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
    """Widget con estado persistente aunque deje de mostrarse en otra vista."""
    wkey = f"_w_{name}"
    ss[wkey] = ss[name]

    def _sync() -> None:
        ss[name] = ss[wkey]

    persist.callbacks[wkey] = _sync
    return wkey


persist.callbacks = {}


def on(wkey: str):
    return persist.callbacks[wkey]


def _event(key: str, name: str):
    v = ss.get(key)
    return v.get(name) if hasattr(v, "get") else getattr(v, name, None)


def cb_select(key: str):
    def _cb() -> None:
        sel = _event(key, "select")
        if sel in REGIONS:
            ss.case = sel

    return _cb


def cb_analyze(key: str):
    def _cb() -> None:
        sel = _event(key, "analyze")
        if sel in REGIONS:
            ss.case = sel
        ss.view = "analysis"

    return _cb


# ------------------------------------------------------------- datos y caché
@st.cache_data(show_spinner=False, ttl=900)
def globe_assets() -> dict:
    """Publica texturas y rejillas del globo en /app/static/globe (con versión por fecha)."""
    src = DATA / "spatial" / "globe"
    STATIC.mkdir(parents=True, exist_ok=True)
    out = {"tex": {}, "grid": {}, "date": {}}
    for k in ("sst", "chl"):
        for kind, name in (("tex", f"tex_{k}.jpg"), ("grid", f"grid_{k}.json")):
            f = src / name
            if f.exists():
                shutil.copy2(f, STATIC / name)
                out[kind][k] = f"/app/static/globe/{name}?v={int(f.stat().st_mtime)}"
    stt = read_status().get("globe", {})
    out["date"] = {
        "sst": stt.get("sst", {}).get("date", ""),
        "chl": stt.get("chl", {}).get("date", ""),
    }
    return out


@st.cache_data(show_spinner=False)
def basin_arcs(lang: str) -> list[dict]:
    """Arcos 'aporte continental': punto representativo de la cuenca → zona marina receptora."""
    from shapely.geometry import shape

    def centroid(name: str):
        p = SETTINGS.regions_dir / name
        if not p.exists():
            return None, 0
        f = json.loads(p.read_text())["features"][0]
        c = shape(f["geometry"]).representative_point()
        return (c.y, c.x), f["properties"].get("area_km2", 0)

    arcs = []
    for basin, case in (
        ("gu_basin_land.geojson", "grijalva_usumacinta"),
        ("gom_basins_land.geojson", "mississippi"),
    ):
        c, area = centroid(basin)
        reg_ = REGIONS.get(case)
        if c and reg_:
            arcs.append(
                {
                    "s": list(c),
                    "e": [reg_.marker["lat"], reg_.marker["lon"]],
                    "label": T[lang]["arc_label"] + " · " + reg_.name(lang),
                    "sub": f"{T[lang]['arc_sub']} · {area:,.0f} km²",
                }
            )
    return arcs


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
    key = result_cache_key(ds_id, bbox, t0, t1, season)
    if (DATA / "results" / f"{key}.nc").exists():
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
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def bbox_txt(b) -> str:
    ns = lambda v: f"{abs(v):.1f}°{'N' if v >= 0 else 'S'}"  # noqa: E731
    ew = lambda v: f"{abs(v):.1f}°{'W' if v < 0 else 'E'}"  # noqa: E731
    return f"{ns(b[0])}–{ns(b[1])} · {ew(b[2])}–{ew(b[3])}"


def ds_label(d: str) -> str:
    return CATALOG[d].label_en if ss.lang == "en" else CATALOG[d].label_es


# ------------------------------------------------------------------ encabezado
status = read_status()
any_ready = any(v.get("state") == "ready" for k in CATALOG for v in status.get(k, {}).values())
h1, h2 = st.columns([0.56, 0.44], vertical_alignment="center")
with h1:
    mission_bar(t("brand_sub"), "agui-server · NASA Earthdata")
with h2:
    n1, n2, n3 = st.columns([0.52, 0.22, 0.26], vertical_alignment="center")
    with n1:
        st.segmented_control(
            "view",
            ["region", "analysis"],
            key="view",
            label_visibility="collapsed",
            format_func=lambda v: t("nav_region") if v == "region" else t("nav_analysis"),
        )
    with n2:
        st.segmented_control(
            "lang", ["es", "en"], key="lang", label_visibility="collapsed", format_func=str.upper
        )
    with n3:
        st.markdown(
            f'<span class="badge ok"><i></i>{t("badge_real")}</span>'
            if any_ready
            else f'<span class="badge prep"><i></i>{t("badge_prep")}</span>',
            unsafe_allow_html=True,
        )
if ss.view is None:
    ss.view = "region"
if ss.lang is None:
    ss.lang = "es"
lang = ss.lang
reg = REGIONS[ss.case]


def ticker_html() -> str:
    items = []
    for ds_id in CATALOG:
        for sid, info in status.get(ds_id, {}).items():
            if info.get("state") == "ready":
                items.append(
                    f'<span class="ticker-item"><b>{ds_label(ds_id).upper()}</b> · {sid} · '
                    f"{info.get('n_months')} {t('months')} · "
                    f"<i>{info.get('first_month')} → {info.get('last_month')}</i></span>"
                )
    g = status.get("globe", {})
    if g.get("sst"):
        items.append(
            f'<span class="ticker-item"><b>{t("tk_globe_sst")}</b> · <i>{g["sst"].get("date")}</i></span>'
        )
    if g.get("chl"):
        items.append(
            f'<span class="ticker-item"><b>{t("tk_globe_chl")}</b> · <i>{g["chl"].get("date")}</i></span>'
        )
    items += [f'<span class="ticker-item">{x}</span>' for x in T[lang]["tk_static"]]
    track = "".join(items)
    return f'<div class="ticker"><div class="ticker-track">{track}{track}</div></div>'


st.markdown(ticker_html(), unsafe_allow_html=True)


def status_cards() -> str:
    cards = []
    for ds_id, spec in CATALOG.items():
        store = store_for_bbox(reg.bbox)
        info = status.get(ds_id, {}).get(store.id if store else "", {})
        state = info.get("state", "empty")
        if state == "ready":
            body = (
                f"{info.get('n_months', 0)} {t('months')} · "
                f"{info.get('first_month', '')} → {info.get('last_month', '')}"
            )
            pct = 100
        elif state == "downloading":
            tot = info.get("total_days") or info.get("total_months") or 1
            done = info.get("done_days") or info.get("done_months") or 0
            pct = int(100 * done / tot)
            body = f"{t('downloading')} · {pct} %"
        else:
            body, pct = t("empty"), 0
        cards.append(
            f'<div class="st-card"><div class="t">{ds_label(ds_id)}</div><div class="b">{body}</div>'
            f'<div class="s">{spec.source_en if lang == "en" else spec.source_es}</div>'
            f'<div class="bar"><span style="width:{pct}%"></span></div></div>'
        )
    g = status.get("globe", {})
    for k, lbl, src in (
        ("sst", t("tk_globe_sst"), "GHRSST MUR25 v4.2 · PO.DAAC"),
        ("chl", t("tk_globe_chl"), "MODIS-Aqua L3m 9 km NRT · OB.DAAC"),
    ):
        if g.get(k):
            cards.append(
                f'<div class="st-card"><div class="t">{lbl}</div><div class="b">{g[k].get("date")}</div>'
                f'<div class="s">{src}</div><div class="bar"><span style="width:100%"></span></div></div>'
            )
    return f'<div class="status">{"".join(cards)}</div>'


# =============================================================== VISTA REGIÓN
if ss.view == "region":
    left, right = st.columns([0.34, 0.66], gap="large")
    with left, st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><p class="eyebrow">{t("choose_region")}</p>',
            unsafe_allow_html=True,
        )
        region_cards(
            [
                {
                    "id": r.id,
                    "name": r.name(lang),
                    "region": r.region_en if lang == "en" else r.region_es,
                    "bboxTxt": bbox_txt(r.bbox),
                    "abbr": "".join(w[0] for w in r.name_es.replace("–", " ").split()[:2]).upper(),
                }
                for r in REGIONS.values()
            ],
            ss.case,
            on_select=cb_select("regioncards"),
        )
        chips = "".join(f'<span class="chip">{ds_label(d)}</span>' for d in reg.datasets)
        st.markdown(
            f'<p class="eyebrow" style="margin-top:18px">{t("eyebrow_case")}</p>'
            f'<div class="case-title">{reg.name(lang)}</div>'
            f'<div class="case-region">{reg.region_en if lang == "en" else reg.region_es}</div>'
            f'<p class="case-text">{reg.summary_en if lang == "en" else reg.summary_es}</p>'
            f'<div class="specs"><span class="dt">{t("bbox")}</span><span class="dd">{bbox_txt(reg.bbox)}</span>'
            f'<span class="dt">{t("period")}</span><span class="dd">{reg.t0} — {reg.t1}</span>'
            f'<span class="dt">{t("variables")}</span><span class="dd">{chips}</span>'
            f'<span class="dt">{t("method")}</span><span class="dd"><span class="chip v">MK Hirsch-Slack</span>'
            f'<span class="chip v">Sen · IC 95 %</span><span class="chip v">FDR q = 0.10</span></span></div>',
            unsafe_allow_html=True,
        )
        st.button(t("analyze"), type="primary", on_click=go_analysis, width="stretch")
    with right:
        assets = globe_assets()
        globe(
            {
                "height": 700,
                "active": ss.case,
                "regions": [
                    {
                        "id": r.id,
                        "name": r.name(lang),
                        "region": r.region_en if lang == "en" else r.region_es,
                        "bbox": list(r.bbox),
                        "bboxTxt": bbox_txt(r.bbox),
                        "period": f"{r.t0} — {r.t1}",
                        "vars": " · ".join(ds_label(d) for d in r.datasets),
                        "lat": r.marker.get("lat", float(np.mean(r.bbox[:2]))),
                        "lng": r.marker.get("lon", float(np.mean(r.bbox[2:]))),
                    }
                    for r in REGIONS.values()
                ],
                "arcs": basin_arcs(lang),
                "tex": assets["tex"],
                "grid": assets["grid"],
                "src": {
                    "sst": f"GHRSST MUR25 v4.2 · NASA PO.DAAC · {assets['date'].get('sst', '')}",
                    "chl": f"MODIS-Aqua L3m 9 km NRT · NASA OB.DAAC · {assets['date'].get('chl', '')}",
                },
                "t": T[lang]["globe"],
            },
            on_select=cb_select("globe"),
            on_analyze=cb_analyze("globe"),
        )
    st.markdown(
        f'<p class="eyebrow" style="margin-top:26px">{t("status_title")}</p>' + status_cards(),
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
    st.markdown(
        f'<p class="eyebrow">{t("eyebrow_case")}</p><div class="case-title">{reg.name(lang)}</div>'
        f'<div class="case-region">{reg.region_en if lang == "en" else reg.region_es} · {bbox_txt(reg.bbox)}</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown('<span class="card-marker"></span>', unsafe_allow_html=True)
        c = st.columns([0.22, 0.2, 0.11, 0.11, 0.16, 0.2], vertical_alignment="bottom")
        with c[0]:
            wk = persist("case")
            st.selectbox(
                t("choose_region"),
                list(REGIONS),
                key=wk,
                on_change=on(wk),
                format_func=lambda k: REGIONS[k].name(lang),
            )
        with c[1]:
            if ss.ds not in reg.datasets:
                ss.ds = reg.datasets[0]
            wk = persist("ds")
            st.selectbox(
                t("variable"), list(reg.datasets), key=wk, on_change=on(wk), format_func=ds_label
            )
        years = list(range(y_min, y_max + 1))
        with c[2]:
            wk = persist("y0")
            st.selectbox(t("from"), years, key=wk, on_change=on(wk))
        with c[3]:
            wk = persist("y1")
            st.selectbox(t("to"), years, key=wk, on_change=on(wk))
        with c[4]:
            wk = persist("season")
            st.selectbox(
                t("season"),
                ["all", "wet", "dry"],
                key=wk,
                on_change=on(wk),
                format_func=lambda s: t(f"season_{s}"),
            )
        with c[5]:
            st.markdown(f'<div class="run-note">{t("run_note")}</div>', unsafe_allow_html=True)
    reg = REGIONS[ss.case]
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
        kpi1, u1 = percent_per_decade(tr.slope_per_decade), "%"
        kpi2 = (10 ** (tr.slope_per_decade * years_span / 10) - 1) * 100
        u2 = f"{ss.y0}–{ss.y1}"
        ci = (percent_per_decade(tr.ci_low), percent_per_decade(tr.ci_high))
        series_units, transform = "%", (lambda v: (np.power(10.0, v) - 1) * 100)
    else:
        kpi1, u1 = tr.slope_per_decade, spec.units
        clim = meta.get("clim_mean") or np.nan
        kpi2 = 100 * tr.slope_per_decade / clim if clim else np.nan
        u2 = f"{t('per_decade')} · {t('clim')} {clim:.1f} {spec.units}"
        ci = (tr.ci_low, tr.ci_high)
        series_units, transform = spec.units, None
    warm, cool = ("#fb7185", "#fbbf24"), ("#38bdf8", "#818cf8")
    tone = warm if (np.isfinite(kpi1) and kpi1 >= 0) else cool
    sig_tone = ("#34d399", "#22d3ee") if tr.significant else ("#94a3b8", "#64748b")
    sig_txt = t("significant") if tr.significant else t("not_significant")
    if not tr.robust:
        sig_txt += f" · {t('sensitive')}"
    season_lbl = "" if ss.season == "all" else f" · {t('season_' + ss.season)}"
    kpis(
        [
            {
                "label": t("kpi_sen"),
                "value": float(kpi1),
                "dec": 3 if abs(kpi1) < 1 else 2,
                "sign": True,
                "unit": f"{u1} {t('per_decade')}",
                "c1": tone[0],
                "c2": tone[1],
                "sub": f"{t('ci')} [{ci[0]:+.2f}, {ci[1]:+.2f}]",
            },
            {
                "label": t("kpi_rel"),
                "value": float(kpi2),
                "dec": 1,
                "sign": True,
                "unit": "%",
                "c1": tone[1],
                "c2": tone[0],
                "sub": u2,
            },
            {
                "label": t("kpi_p"),
                "text": fmt_p(tr.p),
                "value": None,
                "unit": "p",
                "dot": True,
                "c1": sig_tone[0],
                "c2": sig_tone[1],
                "sub": f"{sig_txt} · z = {tr.z:.2f}",
                "z": float(tr.z),
            },
            {
                "label": t("kpi_n"),
                "value": float(tr.n),
                "dec": 0,
                "unit": t("months"),
                "c1": "#a78bfa",
                "c2": "#ec4899",
                "sub": f"{ss.y0}–{ss.y1}{season_lbl}",
            },
        ],
        key=f"kpis_{ds_id}_{ss.case}_{ss.y0}_{ss.y1}_{ss.season}",
    )

    tmap_disp = tmap.copy()
    map_units = spec.trend_units_en if lang == "en" else spec.trend_units_es
    if is_log:
        tmap_disp["slope"] = (np.power(10.0, tmap["slope"]) - 1) * 100
    src = spec.source_en if lang == "en" else spec.source_es
    m1, m2 = st.columns([0.47, 0.53], gap="medium")
    with m1, st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><div class="chart-h">{t("map_title")}</div>'
            f'<div class="chart-sub">{t("map_sub")}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig_trend_map(
                tmap_disp, map_units, coast=coast_for(reg.bbox), marker=reg.marker, height=430
            ),
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
            fig_series(
                series,
                tr,
                series_units,
                labels=(t("anom"), t("sen")),
                transform=transform,
                height=430,
            ),
            config=PLOT_CFG,
            width="stretch",
            key="ts",
        )
        st.markdown(
            f'<div class="chart-src">{t("source")}: {src} · {tr.method} · '
            f"{t('clim')}: {meta.get('clim_period', '')}</div>",
            unsafe_allow_html=True,
        )
    with st.container(border=True):
        st.markdown(
            f'<span class="card-marker"></span><div class="chart-h">{t("stripes_title")}</div>'
            f'<div class="chart-sub">{t("stripes_sub")}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            fig_stripes(series, series_units, transform=transform),
            config=PLOT_CFG,
            width="stretch",
            key="stripes",
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
