"""Sección de investigación dentro de la vista Análisis (D18–D20).

Solo presentación: lee data/research/results (mece research run) y dibuja. Ningún cálculo
estadístico ocurre aquí.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import xarray as xr
from plotly.subplots import make_subplots

from mece.research.fetch import research_config
from mece.visualization.figures import FONT, TOK, _base_layout, coast_lines

CFG = {"displayModeBar": False, "responsive": True}
WARM, COOL, MUTED = "#fb7185", "#38bdf8", "#64748b"
REG_COLORS = ["#e2e8f0", "#fbbf24", "#34d399", "#f472b6", "#a78bfa", "#fb7185", "#38bdf8"]


def _name(kind: str, key: str, lang: str) -> str:
    d = research_config()[kind][key]
    return d.get(f"name_{lang}") or d["name_es"]


def _axis(**kw):
    return {"gridcolor": TOK["grid"], "linecolor": TOK["base"], "tickfont": FONT, "zeroline": False} | kw


def _fmt(v, d=2, sign=True):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "—"
    return f"{v:+.{d}f}" if sign else f"{v:.{d}f}"


def _fmt_p(p):
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def _card(title: str, sub: str):
    st.markdown(f'<span class="card-marker"></span><div class="chart-h">{title}</div>'
                f'<div class="chart-sub">{sub}</div>', unsafe_allow_html=True)


# ============================================================ hallazgos
def findings(res: dict, lang: str, tx: dict, kpis_fn):
    tr = {(t["variable"], t["region"]): t for t in res["trends"]}
    drift = {d["region"]: d for d in res.get("drift", [])}
    mur = {m["region"]: m for m in res.get("mur_validation", [])}
    rain = {p["basin"]: p for p in res["precip_trends"]}
    ext = next(e for e in res["extremes"] if e["variable"] == "sst" and e["region"] == "gulf")
    sst_g = tr[("sst", "gulf")]
    chl_g = drift.get("gulf", {}).get("combined", tr[("chl", "gulf")]["sen"])
    chl_b = drift.get("banco", {}).get("combined", tr[("chl", "banco")]["sen"])
    kpis_fn([
        {"label": tx["h_sst"], "value": float(sst_g["sen"]), "dec": 2, "sign": True, "unit": "°C / déc",
         "c1": "#fb7185", "c2": "#fbbf24",
         "sub": f'{tx["h_sst_s"]} {_fmt(mur.get("gulf", {}).get("mur"))} · p {_fmt_p(sst_g["p_hr"])}'},
        {"label": tx["h_chl"], "value": float(chl_g), "dec": 1, "sign": True, "unit": "% / déc",
         "c1": "#38bdf8", "c2": "#818cf8", "sub": tx["h_chl_s"]},
        {"label": tx["h_banco"], "value": float(chl_b), "dec": 1, "sign": True, "unit": "% / déc",
         "c1": "#38bdf8", "c2": "#a78bfa", "sub": tx["h_banco_s"]},
        {"label": tx["h_rain"], "value": float(rain["grijalva"]["sen_pct"]), "dec": 1, "sign": True,
         "unit": "% / déc", "c1": "#fbbf24", "c2": "#fb7185",
         "sub": f'{tx["h_rain_s"]} · p {_fmt_p(rain["grijalva"]["p_hr"])}'},
    ], key=f"rk_{lang}")
    st.markdown(
        f'<div class="limit" style="margin:4px 0 18px;border-color:rgba(251,113,133,.4);'
        f'background:linear-gradient(90deg,rgba(251,113,133,.12),rgba(15,23,42,.55))">'
        f'<strong>{tx["h_ext"]}:</strong> {ext["freq_early"] / 10:.0f} → <strong>{ext["freq_late"] / 10:.0f}</strong> '
        f'{tx["h_ext_s"]}</div>', unsafe_allow_html=True)

    rows = []
    ev_cls = {"solid": "#34d399", "weak": "#fbbf24", "none": "#64748b"}
    for t in res["trends"]:
        var = t["variable"]
        if var == "chl" and t["region"] in drift:  # D18: titular corregido
            d = drift[t["region"]]
            how = f'{_fmt(d["combined"], 1)} %/déc ({_fmt(d["comb_lo"], 1)} a {_fmt(d["comb_hi"], 1)})'
            what, p, q = d["result"], d["p_combined"], d["q_combined"]
            ev = "solid" if (p < 0.05 and q < 0.05) else ("weak" if p < 0.10 else "none")
            vlabel = tx["v_chl_c"]
        else:
            u = "%/déc" if var == "chl" else "°C/déc"
            how = f'{_fmt(t["sen"], 2 if var == "sst" else 1)} {u} ({_fmt(t["lo"], 2)} a {_fmt(t["hi"], 2)})'
            what, p, q, ev = t["result"], t["p_hr"], t["q"], t["evidence"]
            vlabel = tx["v_sst"] if var == "sst" else tx["v_chl"]
        rows.append((vlabel, _name("regions", t["region"], lang), tx[f"res_{what}"], how, p, q, ev))
    for b in res["precip_trends"]:
        rows.append((tx["v_pp"], _name("basins", b["basin"], lang), tx[f'res_{b["result"]}'],
                     f'{_fmt(b["sen"], 0)} mm/año/déc ({_fmt(b["sen_pct"], 1)} %)', b["p_hr"], None, b["evidence"]))
    head = "".join(f"<th>{tx[k]}</th>" for k in ("col_var", "col_where", "col_what", "col_how", "col_p", "col_q", "col_ev"))
    body = "".join(
        f'<tr><td>{v}</td><td>{w}</td><td>{wh}</td><td class="mono">{h}</td><td class="mono">{_fmt_p(p)}</td>'
        f'<td class="mono">{"—" if q is None else _fmt_p(q)}</td>'
        f'<td><span class="evb" style="--c:{ev_cls[e]}">{tx["ev_" + e]}</span></td></tr>'
        for v, w, wh, h, p, q, e in rows)
    with st.container(border=True):
        _card(tx["matrix_t"], tx["matrix_s"])
        st.markdown(f'<div class="mtx"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>',
                    unsafe_allow_html=True)


# ============================================================ tendencias
def trends(res: dict, lang: str, tx: dict):
    regs = list(research_config()["regions"])[::-1]
    tr = {(t["variable"], t["region"]): t for t in res["trends"]}
    drift = {d["region"]: d for d in res.get("drift", [])}
    mur = {m["region"]: m for m in res.get("mur_validation", [])}
    names = [_name("regions", r, lang) for r in regs]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=(f'{tx["v_chl"]} (%/déc)', f'{tx["v_sst"]} (°C/déc)'))

    def add(col, xs, lo, hi, sig, name, color, off, symbol="circle"):
        y = np.arange(len(regs)) + off
        fig.add_trace(go.Scatter(
            x=xs, y=y, mode="markers", name=name, legendgroup=name, showlegend=col == 1 or name == "MUR25",
            error_x={"type": "data", "symmetric": False, "array": np.array(hi) - np.array(xs),
                     "arrayminus": np.array(xs) - np.array(lo), "color": color, "thickness": 2, "width": 4},
            marker={"size": 12, "symbol": symbol, "color": [color if s else "rgba(2,6,23,1)" for s in sig],
                    "line": {"color": color, "width": 2}},
            customdata=np.c_[names], hovertemplate="%{customdata[0]}<br>%{x:+.2f}<extra>" + name + "</extra>",
        ), row=1, col=col)

    add(1, [tr[("chl", r)]["sen"] for r in regs], [tr[("chl", r)]["lo"] for r in regs],
        [tr[("chl", r)]["hi"] for r in regs], [tr[("chl", r)]["p_hr"] < 0.05 for r in regs],
        tx["modis_only"], "#94a3b8", 0.16)
    if drift:
        add(1, [drift[r]["combined"] for r in regs], [drift[r]["comb_lo"] for r in regs],
            [drift[r]["comb_hi"] for r in regs], [drift[r]["p_combined"] < 0.05 for r in regs],
            tx["corrected"], "#22d3ee", -0.16, "diamond")
    add(2, [tr[("sst", r)]["sen"] for r in regs], [tr[("sst", r)]["lo"] for r in regs],
        [tr[("sst", r)]["hi"] for r in regs], [tr[("sst", r)]["p_hr"] < 0.05 for r in regs],
        "MODIS", "#fb7185", 0.16)
    if mur:
        add(2, [mur[r]["mur"] for r in regs], [mur[r]["mur_lo"] for r in regs], [mur[r]["mur_hi"] for r in regs],
            [mur[r]["p"] < 0.05 for r in regs], "MUR25", "#fbbf24", -0.16, "diamond")
    for c in (1, 2):
        fig.add_vline(x=0, line={"color": "rgba(226,232,240,.4)", "width": 1}, row=1, col=c)
    fig.update_yaxes(tickvals=list(range(len(regs))), ticktext=names, **_axis())
    fig.update_xaxes(**_axis())
    fig.update_layout(**_base_layout(height=470, legend={"orientation": "h", "y": -0.12, "font": FONT},
                                     margin={"l": 10, "r": 10, "t": 40, "b": 30}))
    fig.update_annotations(font={**FONT, "size": 13, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["trend_t"], tx["trend_s"])
        st.plotly_chart(fig, config=CFG, width="stretch", key="r_forest")


# ============================================================ mapas por celda
def maps(results_dir: Path, lang: str, tx: dict, land_zip: str):
    cols = st.columns(2, gap="medium")
    box = research_config()["bbox_ocean"]
    coast = coast_lines((box[0], box[1], box[2], box[3]), land_zip)
    for col, var, unit, scale in ((cols[0], "chl", "%/déc", [[0, "#7c2d12"], [.25, "#d97706"], [.5, "#1e293b"],
                                                            [.75, "#0d9488"], [1, "#134e4a"]]),
                                  (cols[1], "sst", "°C/déc", [[0, "#1e293b"], [.35, "#fbbf24"], [.7, "#f43f5e"],
                                                             [1, "#7f1d1d"]])):
        f = results_dir / f"map_trend_{var}.nc"
        if not f.exists():
            continue
        with xr.open_dataset(f) as ds:
            ds = ds.load()
        z = ds.slope.values
        lim = float(np.nanpercentile(np.abs(z), 98)) or 1
        zmin, zmax = (-lim, lim) if var == "chl" else (0, float(np.nanpercentile(z, 98)))
        lon2, lat2 = np.meshgrid(ds.lon.values, ds.lat.values)
        sig = ds.sig_fdr.values.astype(bool)
        fig = go.Figure(go.Heatmap(x=ds.lon.values, y=ds.lat.values, z=z, colorscale=scale, zmin=zmin, zmax=zmax,
                                   colorbar={"title": {"text": unit, "font": FONT}, "tickfont": FONT, "thickness": 12},
                                   hovertemplate="%{x:.2f}, %{y:.2f}<br>%{z:+.2f} " + unit + "<extra></extra>"))
        fig.add_trace(go.Scatter(x=lon2[sig], y=lat2[sig], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker={"size": 2.6, "color": "rgba(2,6,23,.85)"}))
        if coast[0]:
            fig.add_trace(go.Scatter(x=coast[0], y=coast[1], mode="lines", hoverinfo="skip", showlegend=False,
                                     line={"color": TOK["coast"], "width": 1}))
        fig.update_layout(**_base_layout(height=430, plot_bgcolor="#060a14", xaxis=_axis(range=[box[2], box[3]], constrain="domain"),
                                         yaxis=_axis(range=[box[0], box[1]], scaleanchor="x", scaleratio=1.08, constrain="domain"),
                                         margin={"l": 40, "r": 10, "t": 10, "b": 30}))
        with col, st.container(border=True):
            _card(f'{tx["v_" + var]} · 2003–2025', f'{tx["maps_s"]} {int(sig.sum())}/{int(np.isfinite(z).sum())} '
                                                  f'{tx["sig_cells"]}.' + (f' {tx["maps_chl_note"]}' if var == "chl" else ""))
            st.plotly_chart(fig, config=CFG, width="stretch", key=f"r_map_{var}")


# ============================================================ series y ciclos
def series(df: pd.DataFrame, res: dict, lang: str, tx: dict):
    regs = list(research_config()["regions"])
    sel = st.selectbox(tx["region"], regs, format_func=lambda r: _name("regions", r, lang), key="r_series_reg")
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.07,
                        subplot_titles=(f'{tx["v_chl"]} (%)', f'{tx["v_sst"]} (°C)'))
    for c, var, color in ((1, "chl", "#34d399"), (2, "sst", "#fb7185")):
        d = df[(df.variable == var) & (df.region == sel)].set_index("fecha").sort_index()
        y = d.anomalia_pct if var == "chl" else d.anomalia
        fig.add_trace(go.Scatter(x=y.index, y=y, mode="lines", line={"color": "rgba(148,163,184,.55)", "width": 1},
                                 showlegend=False, hovertemplate="%{x|%b %Y}: %{y:+.2f}<extra></extra>"), row=1, col=c)
        fig.add_trace(go.Scatter(x=y.index, y=y.rolling(12, center=True).mean(), mode="lines",
                                 line={"color": color, "width": 2.6}, showlegend=False, hoverinfo="skip"), row=1, col=c)
        fig.add_hline(y=0, line={"color": "rgba(226,232,240,.35)", "width": 1}, row=1, col=c)
    fig.update_xaxes(**_axis())
    fig.update_yaxes(**_axis())
    fig.update_layout(**_base_layout(height=360, margin={"l": 40, "r": 10, "t": 40, "b": 30}, hovermode="x unified"))
    fig.update_annotations(font={**FONT, "size": 13, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["series_t"], tx["series_s"])
        st.plotly_chart(fig, config=CFG, width="stretch", key="r_series")
    clim = pd.DataFrame(res["climatology"])
    fig2 = make_subplots(rows=1, cols=2, horizontal_spacing=0.07,
                         subplot_titles=(f'{tx["v_chl"]} (mg/m³, log)', f'{tx["v_sst"]} (°C)'))
    for i, r in enumerate(regs):
        for c, var in ((1, "chl"), (2, "sst")):
            d = clim[(clim.variable == var) & (clim.region == r)].sort_values("mes")
            fig2.add_trace(go.Scatter(x=d.mes, y=d.valor, mode="lines+markers", name=_name("regions", r, lang),
                                      legendgroup=r, showlegend=c == 1, line={"color": REG_COLORS[i], "width": 2},
                                      marker={"size": 5}), row=1, col=c)
    fig2.update_yaxes(type="log", row=1, col=1)
    fig2.update_xaxes(**_axis(tickvals=list(range(1, 13))))
    fig2.update_yaxes(**_axis())
    fig2.update_layout(**_base_layout(height=380, legend={"orientation": "h", "y": -0.18, "font": FONT},
                                      margin={"l": 40, "r": 10, "t": 40, "b": 30}))
    fig2.update_annotations(font={**FONT, "size": 13, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["cycle_t"], "")
        st.plotly_chart(fig2, config=CFG, width="stretch", key="r_cycle")


# ============================================================ ríos y clima
def rivers(res: dict, lang: str, tx: dict):
    corr = pd.DataFrame(res["corr_rain_chl"])
    pairs = corr[["basin", "region"]].drop_duplicates().values.tolist()
    fig = make_subplots(rows=2, cols=3, shared_yaxes=True, vertical_spacing=0.3, horizontal_spacing=0.04,
                        subplot_titles=[f'{_name("basins", b, lang)}<br>→ {_name("regions", r, lang)}'
                                        + (f' ({tx["control"]})' if i == len(pairs) - 1 else "")
                                        for i, (b, r) in enumerate(pairs)])
    for i, (b, r) in enumerate(pairs):
        d = corr[(corr.basin == b) & (corr.region == r)].sort_values("lag")
        sig = d.q < 0.05
        fig.add_trace(go.Bar(x=d.lag, y=d.r, showlegend=False,
                             marker={"color": ["#22d3ee" if s else "rgba(34,211,238,.12)" for s in sig],
                                     "line": {"color": "#22d3ee", "width": 1.5}},
                             hovertemplate="lag %{x}: r = %{y:.2f}<extra></extra>"), row=i // 3 + 1, col=i % 3 + 1)
    fig.update_xaxes(**_axis(title={"text": tx["lag"], "font": FONT}, dtick=1))
    fig.update_yaxes(**_axis())
    fig.update_layout(**_base_layout(height=600, margin={"l": 40, "r": 10, "t": 60, "b": 40}))
    fig.update_annotations(font={**FONT, "size": 11, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["rain_t"], tx["rain_s"])
        st.plotly_chart(fig, config=CFG, width="stretch", key="r_lags")

    c1, c2 = st.columns(2, gap="medium")
    pt = pd.DataFrame(res["precip_trends"])
    fig_r = go.Figure(go.Bar(
        y=[_name("basins", b, lang) for b in pt.basin], x=pt.sen_pct, orientation="h",
        marker={"color": [WARM if p < 0.05 else "rgba(148,163,184,.35)" for p in pt.p_hr]},
        error_x={"type": "data", "symmetric": False, "array": (pt.hi - pt.sen) / pt.annual_mm * 100,
                 "arrayminus": (pt.sen - pt.lo) / pt.annual_mm * 100, "color": "#cbd5e1"},
        hovertemplate="%{y}: %{x:+.1f} %/déc<extra></extra>"))
    fig_r.update_layout(**_base_layout(height=320, xaxis=_axis(title={"text": "%/década", "font": FONT}),
                                       yaxis=_axis(), margin={"l": 10, "r": 10, "t": 10, "b": 40}))
    with c1, st.container(border=True):
        _card(tx["rain_tr_t"], "")
        st.plotly_chart(fig_r, config=CFG, width="stretch", key="r_rain")
    cs = pd.DataFrame(res["corr_sst_chl"])
    fig_s = go.Figure(go.Bar(y=[_name("regions", r, lang) for r in cs.region], x=cs.r, orientation="h",
                             marker={"color": COOL}, hovertemplate="%{y}: r = %{x:.2f}<extra></extra>"))
    fig_s.update_layout(**_base_layout(height=320, xaxis=_axis(title={"text": "r (Spearman)", "font": FONT}),
                                       yaxis=_axis(), margin={"l": 10, "r": 10, "t": 10, "b": 40}))
    with c2, st.container(border=True):
        _card(tx["sstchl_t"], tx["sstchl_s"])
        st.plotly_chart(fig_s, config=CFG, width="stretch", key="r_sstchl")

    co = pd.DataFrame(res["regression"])
    preds = [p for p in ("SST", "Lluvia", "ONI", "Tiempo") if p in co.predictor.unique()]
    regs = list(research_config()["models"])
    b = co.pivot(index="region", columns="predictor", values="beta").reindex(index=regs, columns=preds)
    q = co.pivot(index="region", columns="predictor", values="q").reindex(index=regs, columns=preds)
    txt = [[("" if not np.isfinite(v) else (f"<b>{v:+.2f}</b>" if qq < 0.05 else f"{v:+.2f}"))
            for v, qq in zip(rb, rq, strict=True)] for rb, rq in zip(b.values, q.values, strict=True)]
    lim = float(np.nanmax(np.abs(b.values)))
    pred_lbl = {"SST": "SST", "Lluvia": tx["v_pp"], "ONI": "El Niño (ONI)", "Tiempo": "t"}
    fig_b = go.Figure(go.Heatmap(z=b.values, x=[pred_lbl[p] for p in preds], y=[_name("regions", r, lang) for r in regs],
                                 text=txt, texttemplate="%{text}", textfont={"size": 13, "family": FONT["family"]}, zmin=-lim, zmax=lim, zmid=0,
                                 xgap=3, ygap=3, colorscale=[[0, "#4c1d95"], [.5, "#1e293b"], [1, "#c2410c"]],
                                 colorbar={"title": {"text": "β", "font": FONT}, "tickfont": FONT, "thickness": 12},
                                 hovertemplate="%{y} · %{x}: β = %{z:+.2f}<extra></extra>"))
    fig_b.update_layout(**_base_layout(height=420, xaxis=_axis(tickangle=0, side="top"), yaxis=_axis(), margin={"l": 10, "r": 10, "t": 30, "b": 10}))
    at = pd.DataFrame(res["attribution"])
    fig_a = go.Figure()
    for col, color in (("SST", WARM), ("Lluvia", COOL), ("ONI", "#fbbf24"), ("residual", MUTED)):
        fig_a.add_trace(go.Bar(y=[_name("regions", r, lang) for r in at.region], x=at[col].fillna(0), orientation="h",
                               name=pred_lbl.get(col, col), marker={"color": color}))
    fig_a.add_trace(go.Scatter(y=[_name("regions", r, lang) for r in at.region], x=at.total, mode="markers",
                               name="total", marker={"symbol": "diamond", "size": 11, "color": "#f8fafc"}))
    fig_a.update_layout(**_base_layout(height=380, barmode="group", xaxis=_axis(title={"text": "%/década", "font": FONT}),
                                       yaxis=_axis(), legend={"orientation": "h", "y": -0.2, "font": FONT},
                                       margin={"l": 10, "r": 10, "t": 10, "b": 40}))
    c3, c4 = st.columns(2, gap="medium")
    with c3, st.container(border=True):
        _card(tx["reg_t"], tx["reg_s"])
        st.plotly_chart(fig_b, config=CFG, width="stretch", key="r_beta")
    with c4, st.container(border=True):
        _card(tx["attr_t"], tx["attr_s"])
        st.plotly_chart(fig_a, config=CFG, width="stretch", key="r_attr")


# ============================================================ extremos y régimen
def extremes(res: dict, lang: str, tx: dict):
    cv = res["extreme_curves"]
    regs = list(research_config()["regions"])
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.05,
                        subplot_titles=("SST > p90", f'{tx["v_chl"]} < p10'))
    for c, var in ((1, "sst"), (2, "chl")):
        for i, r in enumerate(regs):
            d = next(x for x in cv if x["variable"] == var and x["region"] == r)
            hl = r in ("gulf", "banco")
            fig.add_trace(go.Scatter(x=d["year"], y=d["prob"], mode="lines", name=_name("regions", r, lang),
                                     legendgroup=r, showlegend=c == 1,
                                     line={"color": REG_COLORS[i], "width": 3.4 if hl else 1.4},
                                     opacity=1 if hl else .7, hovertemplate="%{x:.0f}: %{y:.0f} %<extra></extra>"),
                          row=1, col=c)
        fig.add_hline(y=10, line={"dash": "dash", "color": "rgba(226,232,240,.4)"}, row=1, col=c)
    fig.update_xaxes(**_axis())
    fig.update_yaxes(**_axis(title={"text": "%", "font": FONT}))
    fig.update_layout(**_base_layout(height=400, legend={"orientation": "h", "y": -0.18, "font": FONT},
                                     margin={"l": 40, "r": 10, "t": 40, "b": 30}))
    fig.update_annotations(font={**FONT, "size": 13, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["ext_t"], tx["ext_s"])
        st.plotly_chart(fig, config=CFG, width="stretch", key="r_ext")

    an = pd.DataFrame(res["annual_anomalies"])
    rg = {(r["variable"], r["region"]): r for r in res["regime"]}
    g = an[(an.variable == "sst") & (an.region == "gulf")].sort_values("anio")
    yr = rg[("sst", "gulf")]["year"]
    before, after = g[g.anio < yr].anomalia.mean(), g[g.anio >= yr].anomalia.mean()
    fig_g = go.Figure(go.Bar(x=g.anio, y=g.anomalia, marker={"color": [WARM if v > 0 else COOL for v in g.anomalia]},
                             hovertemplate="%{x}: %{y:+.2f} °C<extra></extra>", showlegend=False))
    fig_g.add_trace(go.Scatter(x=[g.anio.min() - .5, yr - .5, yr - .5, g.anio.max() + .5],
                               y=[before, before, after, after], mode="lines", showlegend=False,
                               line={"color": "#fbbf24", "width": 3, "shape": "hv"}))
    fig_g.update_layout(**_base_layout(height=320, xaxis=_axis(), yaxis=_axis(title={"text": "°C", "font": FONT}),
                                       margin={"l": 40, "r": 10, "t": 10, "b": 30}))
    reg_rows = "".join(
        f'<tr><td>{tx["v_" + r["variable"]]}</td><td>{_name("regions", r["region"], lang)}</td><td class="mono">{r["year"]}</td>'
        f'<td class="mono">{_fmt_p(r["p"])}</td><td class="mono">{_fmt(r["jump"], 2)} {"°C" if r["variable"] == "sst" else "%"}</td>'
        f'<td class="mono">{_fmt(r["dbic"], 1)}</td><td>{tx["m_" + r["model"]]}</td></tr>' for r in res["regime"])
    with st.container(border=True):
        _card(tx["regime_t"], tx["regime_s"])
        st.plotly_chart(fig_g, config=CFG, width="stretch", key="r_regime")
        st.markdown(f'<div class="mtx" style="max-height:360px;margin-top:8px"><table><thead><tr><th>{tx["col_var"]}</th>'
                    f'<th>{tx["col_where"]}</th><th>{tx["col_year"]} (Pettitt)</th><th>p</th><th>Δ</th><th>ΔBIC</th>'
                    f'<th>{tx["col_model"]}</th></tr></thead><tbody>{reg_rows}</tbody></table></div>',
                    unsafe_allow_html=True)

    se = pd.DataFrame(res["seasonal"])
    order = ["DEF", "MAM", "JJA", "SON"]
    fig_s = make_subplots(rows=1, cols=2, horizontal_spacing=0.03, shared_yaxes=True,
                          subplot_titles=(f'{tx["v_chl"]} (%/déc)', f'{tx["v_sst"]} (°C/déc)'))
    for c, var, scale in ((1, "chl", [[0, "#7c2d12"], [.5, "#1e293b"], [1, "#0d9488"]]),
                          (2, "sst", [[0, "#1e3a8a"], [.5, "#1e293b"], [1, "#be123c"]])):
        m = se[se.variable == var].pivot(index="region", columns="season", values="trend").reindex(index=regs, columns=order)
        q = se[se.variable == var].pivot(index="region", columns="season", values="q").reindex(index=regs, columns=order)
        lim = float(np.nanmax(np.abs(m.values)))
        txt = [[(f"<b>{v:+.1f}</b>" if qq < 0.05 else f"{v:+.1f}") if var == "chl" else
                (f"<b>{v:+.2f}</b>" if qq < 0.05 else f"{v:+.2f}") for v, qq in zip(rm, rq, strict=True)]
               for rm, rq in zip(m.values, q.values, strict=True)]
        fig_s.add_trace(go.Heatmap(z=m.values, x=order, y=[_name("regions", r, lang) for r in regs], text=txt,
                                   texttemplate="%{text}", zmin=-lim, zmax=lim, zmid=0, colorscale=scale,
                                   showscale=False), row=1, col=c)
    fig_s.update_xaxes(**_axis())
    fig_s.update_yaxes(**_axis())
    fig_s.update_layout(**_base_layout(height=380, margin={"l": 10, "r": 10, "t": 40, "b": 30}))
    fig_s.update_annotations(font={**FONT, "size": 13, "color": TOK["ink"]})
    with st.container(border=True):
        _card(tx["seas_t"], tx["seas_s"])
        st.plotly_chart(fig_s, config=CFG, width="stretch", key="r_seas")

    cols = st.columns(len(res["anova"]), gap="medium")
    for col, a in zip(cols, res["anova"], strict=True):
        fig_v = go.Figure(go.Bar(x=a["periods"], y=a["means"],
                                 marker={"color": [COOL if v < 0 else WARM for v in a["means"]]},
                                 text=[f"{v:+.2f}" for v in a["means"]], textposition="outside"))
        fig_v.update_layout(**_base_layout(height=280, xaxis=_axis(), yaxis=_axis(), margin={"l": 30, "r": 10, "t": 10, "b": 30}))
        with col, st.container(border=True):
            _card(f'{tx["anova_t"]} · {tx["v_" + a["variable"]]}',
                  f'F = {a["F"]:.1f} · p {_fmt_p(a["p"])} · Kruskal p {_fmt_p(a["kruskal_p"])}')
            st.plotly_chart(fig_v, config=CFG, width="stretch", key=f'r_anova_{a["variable"]}')


# ============================================================ validación
def validation(res: dict, lang: str, tx: dict):
    regs = list(research_config()["regions"])
    ds = pd.DataFrame(res.get("drift_series", []))
    if len(ds):
        ds["fecha"] = pd.to_datetime(ds.fecha)
        fig = go.Figure()
        for i, r in enumerate(regs):
            d = ds[ds.region == r]
            fig.add_trace(go.Scatter(x=d.fecha, y=d.pct, mode="lines", name=_name("regions", r, lang),
                                     line={"color": REG_COLORS[i], "width": 3.2 if r == "gulf" else 1.4}))
        fig.add_hline(y=0, line={"color": "rgba(226,232,240,.4)"})
        fig.update_layout(**_base_layout(height=380, xaxis=_axis(), yaxis=_axis(title={"text": "MODIS vs VIIRS (%)", "font": FONT}),
                                         legend={"orientation": "h", "y": -0.3, "yanchor": "top", "font": FONT},
                                         margin={"l": 40, "r": 10, "t": 10, "b": 90}))
        fig.update_layout(height=430)
        with st.container(border=True):
            _card(tx["drift_t"], tx["drift_s"])
            st.plotly_chart(fig, config=CFG, width="stretch", key="r_drift")
        dr = pd.DataFrame(res["drift"])
        rows = "".join(
            f'<tr><td>{_name("regions", d.region, lang)}</td><td class="mono">{_fmt(d.drift, 1)} %/déc '
            f'(p {_fmt_p(d.p_drift)})</td><td class="mono">{_fmt(d.modis, 1)} (p {_fmt_p(d.p_modis)})</td>'
            f'<td class="mono"><b>{_fmt(d.combined, 1)}</b> ({_fmt(d.comb_lo, 1)} a {_fmt(d.comb_hi, 1)}) · '
            f'q {_fmt_p(d.q_combined)}</td></tr>' for d in dr.itertuples())
        with st.container(border=True):
            _card(tx["drift_tab"], "")
            st.markdown('<div class="mtx"><table><thead><tr><th></th><th>MODIS − VIIRS</th>'
                        f'<th>{tx["modis_only"]}</th><th>{tx["corrected"]}</th></tr></thead><tbody>{rows}</tbody></table></div>',
                        unsafe_allow_html=True)
            banco = dr[dr.region == "banco"]
            if len(banco):
                st.markdown(f'<div class="chart-src">{tx["corr_note"]} <b>{_fmt(float(banco.combined.iloc[0]), 1)} '
                            f'%/década</b>.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    mur = pd.DataFrame(res.get("mur_validation", []))
    if len(mur):
        names = [_name("regions", r, lang) for r in mur.region]
        fig_m = go.Figure([go.Bar(y=names, x=mur.modis, name="MODIS (equipo)", orientation="h", marker={"color": WARM}),
                           go.Bar(y=names, x=mur.mur, name="MUR25", orientation="h", marker={"color": "#fbbf24"},
                                  error_x={"type": "data", "symmetric": False, "array": mur.mur_hi - mur.mur,
                                           "arrayminus": mur.mur - mur.mur_lo, "color": "#e2e8f0"})])
        fig_m.update_layout(**_base_layout(height=380, barmode="group", xaxis=_axis(title={"text": "°C/década", "font": FONT}),
                                           yaxis=_axis(), legend={"orientation": "h", "y": -0.18, "font": FONT},
                                           margin={"l": 10, "r": 10, "t": 10, "b": 40}))
        with c1, st.container(border=True):
            _card(tx["mur_t"], tx["mur_s"])
            st.plotly_chart(fig_m, config=CFG, width="stretch", key="r_mur")
    va = pd.DataFrame(res.get("validation", []))
    if len(va):
        rows = "".join(
            f'<tr><td>{_name("regions", v.region, lang)}</td><td class="mono">{v.r_chl_flh:.2f}</td>'
            f'<td class="mono">{v.r_modis_viirs:.2f}</td><td class="mono">{_fmt(v.flh, 1)} (p {_fmt_p(v.p_flh)})</td>'
            f'<td class="mono">{_fmt(v.viirs_1225, 1)} (p {_fmt_p(v.p_viirs_1225)})</td></tr>' for v in va.itertuples())
        with c2, st.container(border=True):
            _card(tx["flh_t"], "")
            st.markdown('<div class="mtx"><table><thead><tr><th></th><th>r chl–nFLH</th><th>r MODIS–VIIRS</th>'
                        f'<th>nFLH %/déc</th><th>VIIRS 2012–25</th></tr></thead><tbody>{rows}</tbody></table></div>',
                        unsafe_allow_html=True)
    c3, c4 = st.columns(2, gap="medium")
    rob = pd.DataFrame(res["robustness"])
    fig_r = go.Figure(go.Bar(y=[_name("regions", r, lang) for r in rob.region], x=rob.pct_sig, orientation="h",
                             marker={"color": ["#34d399" if v >= 80 else "#fbbf24" for v in rob.pct_sig]},
                             text=[f"{v:.0f} %" for v in rob.pct_sig], textposition="outside"))
    fig_r.add_vline(x=80, line={"dash": "dash", "color": "rgba(226,232,240,.5)"})
    fig_r.update_layout(**_base_layout(height=380, xaxis=_axis(range=[0, 110]), yaxis=_axis(),
                                       margin={"l": 10, "r": 10, "t": 10, "b": 30}))
    with c3, st.container(border=True):
        _card(tx["rob_t"], tx["rob_s"])
        st.plotly_chart(fig_r, config=CFG, width="stretch", key="r_rob")
    we = pd.DataFrame(res["weatherhead"])
    fig_w = go.Figure()
    for var, color in (("sst", WARM), ("chl", COOL)):
        d = we[we.variable == var]
        fig_w.add_trace(go.Bar(y=[_name("regions", r, lang) for r in d.region], x=d.years_needed.clip(upper=120),
                               orientation="h", name=tx["v_" + var], marker={"color": color},
                               text=[f"{v:.0f}" for v in d.years_needed], textposition="outside",
                               textfont={**FONT, "size": 10}, cliponaxis=False,
                               customdata=d.years_needed, hovertemplate="%{y}: %{customdata:.0f}<extra></extra>"))
    fig_w.add_vline(x=23, line={"color": "#f8fafc", "width": 2, "dash": "dot"})
    fig_w.add_annotation(x=23, y=1.02, yref="paper", text=f'23 {tx["years_have"]}', showarrow=False,
                         xanchor="left", yanchor="bottom", font={**FONT, "color": "#f8fafc"})
    fig_w.update_layout(**_base_layout(height=380, barmode="group",
                                       xaxis=_axis(title={"text": tx["years_needed"], "font": FONT}, range=[0, 135]),
                                       yaxis=_axis(), legend={"orientation": "h", "y": -0.22, "font": FONT},
                                       margin={"l": 10, "r": 30, "t": 30, "b": 40}))
    with c4, st.container(border=True):
        _card(tx["weath_t"], tx["weath_s"])
        st.plotly_chart(fig_w, config=CFG, width="stretch", key="r_weath")


# ============================================================ galería y método
def gallery(tx: dict, results_dir: Path, df: pd.DataFrame | None):
    items = "".join(f'<a class="gal-it" href="/app/static/evidence/{f}" target="_blank" rel="noopener">'
                    f'<img src="/app/static/evidence/{f}" loading="lazy" alt="{c}"><span>{c}</span></a>'
                    for f, c in tx["figs"])
    with st.container(border=True):
        _card(tx["gal_t"], tx["gal_s"])
        st.markdown(f'<div class="gal">{items}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="medium")
    with c1, st.container(border=True):
        _card(tx["method_t"], "")
        st.markdown("<ul class='ml'>" + "".join(f"<li>{m}</li>" for m in tx["method"]) + "</ul>", unsafe_allow_html=True)
    with c2, st.container(border=True):
        _card(tx["limits_t"], "")
        st.markdown("<ul class='ml'>" + "".join(f"<li>{m}</li>" for m in tx["limits"]) + "</ul>", unsafe_allow_html=True)
    with st.container(border=True):
        _card(tx["dl_t"], "")
        d1, d2 = st.columns(2)
        f = results_dir / "results.json"
        if f.exists():
            d1.download_button(tx["dl_json"], f.read_bytes(), "resultados_investigacion.json", "application/json",
                               width="stretch")
        if df is not None:
            d2.download_button(tx["dl_series"], df.to_csv(index=False).encode(), "series_regionales.csv", "text/csv",
                               width="stretch")


CSS = """
<style>
.mtx{overflow:auto;max-height:620px;border-radius:14px;border:1px solid rgba(148,163,184,.12)}
.mtx table{width:100%;border-collapse:collapse;font-size:13px}
.mtx th{position:sticky;top:0;background:#0b1224;color:#7dd3fc;font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;
  text-transform:uppercase;text-align:left;padding:10px 12px;border-bottom:1px solid rgba(56,189,248,.25)}
.mtx td{padding:9px 12px;border-bottom:1px solid rgba(148,163,184,.08);color:#e2e8f0}
.mtx tr:hover td{background:rgba(56,189,248,.07)}
.mtx .mono,.mono{font-family:var(--mono);font-size:12px}
.mtx td.mono{white-space:nowrap}
.evb{display:inline-block;padding:3px 10px;border-radius:999px;font-family:var(--mono);font-size:11px;color:var(--c);
  border:1px solid var(--c);background:color-mix(in srgb,var(--c) 14%,transparent)}
.gal{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;margin-top:8px}
.gal-it{display:block;border-radius:16px;overflow:hidden;border:1px solid rgba(148,163,184,.16);background:#f8fafc;
  text-decoration:none;transition:all .35s cubic-bezier(.2,.8,.2,1);position:relative}
.gal-it img{width:100%;height:170px;object-fit:cover;object-position:top;display:block;transition:transform .5s}
.gal-it span{display:block;padding:10px 12px;background:#0b1224;color:#cbd5e1;font-size:12.5px;line-height:1.4;min-height:58px}
.gal-it,.gal-it *{text-decoration:none!important}
.gal-it:hover{transform:translateY(-4px);box-shadow:0 20px 50px -20px rgba(56,189,248,.8);border-color:rgba(56,189,248,.6)}
.gal-it:hover img{transform:scale(1.05)}
ul.ml{margin:6px 0 0;padding-left:18px;color:#cbd5e1;font-size:14px;line-height:1.65}
ul.ml li{margin-bottom:6px}
[data-testid="stTabs"] [role="tablist"]{gap:6px;flex-wrap:wrap;border-bottom:1px solid rgba(148,163,184,.14);padding-bottom:0}
[data-testid="stTab"]{font-family:var(--mono)!important;border-radius:12px 12px 0 0;padding:10px 16px!important;
  transition:all .25s;position:relative;cursor:pointer}
[data-testid="stTab"] p{font-family:var(--mono)!important;font-size:12.5px!important;color:#94a3b8!important;letter-spacing:.02em}
[data-testid="stTab"]:hover{background:rgba(56,189,248,.1)}
[data-testid="stTab"]:hover p{color:#fff!important}
[data-testid="stTab"][aria-selected="true"]{background:linear-gradient(180deg,rgba(14,165,233,.28),rgba(99,102,241,.06))}
[data-testid="stTab"][aria-selected="true"] p{color:#fff!important}
[data-testid="stTab"][aria-selected="true"]::after{content:"";position:absolute;left:10px;right:10px;bottom:-1px;height:3px;
  border-radius:3px;background:linear-gradient(90deg,#22d3ee,#a855f7);box-shadow:0 0 12px rgba(34,211,238,.7)}
.evb{white-space:nowrap}
</style>
"""


def load_series(results_dir: Path) -> pd.DataFrame | None:
    f = results_dir / "series.parquet"
    return pd.read_parquet(f) if f.exists() else None


__all__ = ["CSS", "findings", "trends", "maps", "series", "rivers", "extremes", "validation", "gallery",
           "load_series", "json"]
