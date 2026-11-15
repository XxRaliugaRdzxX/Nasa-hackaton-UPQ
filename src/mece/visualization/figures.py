"""Constructores de figuras Plotly (contrato D14). Ninguna figura de la app usa matplotlib.

Tokens visuales de la prueba de diseño (tema oscuro único).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import xarray as xr

from mece.catalog import BBox, Region

# ------------------------------------------------------------------ tokens
TOK = {
    "page": "#020617",
    "surface": "#0f172a",
    "surface2": "#111c33",
    "ink": "#f1f5f9",
    "ink2": "#cbd5e1",
    "muted": "#94a3b8",
    "grid": "rgba(148,163,184,0.10)",
    "base": "rgba(148,163,184,0.28)",
    "accent": "#22d3ee",
    "accent2": "#fbbf24",
    "warm": "#fb7185",
    "cool": "#38bdf8",
    "nonsig": "#2f4566",
    "land": "#0b1324",
    "ocean_deep": "#0b1a2e",
    "coast": "#7dd3fc",
}
DIVERGING = [
    [0.00, "#1e40af"],
    [0.22, "#38bdf8"],
    [0.50, "#1e293b"],
    [0.78, "#fb7185"],
    [1.00, "#e11d48"],
]
FONT = {
    "family": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    "color": TOK["ink2"],
    "size": 12,
}
MONO = '"IBM Plex Mono", ui-monospace, monospace'


def _thermal_scale() -> list:
    """cmocean.thermal como escala de Plotly (SST)."""
    import cmocean

    cm = cmocean.cm.thermal
    return [
        [i / 10, "rgb({},{},{})".format(*(int(255 * c) for c in cm(i / 10)[:3]))] for i in range(11)
    ]


def _base_layout(**kw) -> dict:
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": FONT,
        "margin": {"l": 54, "r": 10, "t": 8, "b": 42},
        "hoverlabel": {"bgcolor": "rgba(2,6,23,0.92)", "bordercolor": TOK["accent"], "font": FONT},
    } | kw


# ================================================================== globo 3D
def _xyz(lon, lat, r=1.0):
    lon_r, lat_r = np.radians(lon), np.radians(lat)
    return r * np.cos(lat_r) * np.cos(lon_r), r * np.cos(lat_r) * np.sin(lon_r), r * np.sin(lat_r)


def _lines3d(segments: list[tuple[np.ndarray, np.ndarray]], r: float):
    """Segmentos separados por NaN, en float32 (Plotly los envía como binario)."""
    lon = np.concatenate([np.r_[np.asarray(a, float), np.nan] for a, _ in segments])
    lat = np.concatenate([np.r_[np.asarray(b, float), np.nan] for _, b in segments])
    x, y, z = _xyz(lon, lat, r)
    return x.astype(np.float32), y.astype(np.float32), z.astype(np.float32)


@lru_cache(maxsize=2)
def _coast_segments_110m(path: str) -> list:
    data = json.loads(Path(path).read_text())
    segs = []
    for f in data["features"]:
        g = f["geometry"]
        parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for p in parts:
            arr = np.asarray(p)
            segs.append((arr[:, 0], arr[:, 1]))
    return segs


@lru_cache(maxsize=2)
def land_mesh(path: str, step: float = 3.0, r: float = 1.003):
    """Tierra como malla 3D: puntos de rejilla dentro de la tierra + contorno densificado,
    triangulados (Delaunay) y filtrados por pertenencia al polígono. Triángulos de ~3°
    para que la malla se ciña a la esfera."""
    import shapely
    from scipy.spatial import Delaunay
    from shapely.geometry import shape

    data = json.loads(Path(path).read_text())
    polys = [shape(f["geometry"]) for f in data["features"]]
    land = shapely.union_all(polys)
    shapely.prepare(land)
    gx, gy = np.meshgrid(np.arange(-180, 180.01, step), np.arange(-90, 90.01, step))
    grid = np.c_[gx.ravel(), gy.ravel()]
    grid = grid[shapely.contains_xy(land, grid[:, 0], grid[:, 1])]
    edge = shapely.get_coordinates(shapely.segmentize(land.boundary, step / 3))
    pts = np.unique(np.round(np.r_[grid, edge], 3), axis=0)
    tri = Delaunay(pts).simplices
    cen = pts[tri].mean(axis=1)
    keep = shapely.contains_xy(land, cen[:, 0], cen[:, 1])
    tri = tri[keep]
    x, y, z = _xyz(pts[:, 0], pts[:, 1], r)
    return (
        x.astype(np.float32),
        y.astype(np.float32),
        z.astype(np.float32),
        tri[:, 0].astype(np.int32),
        tri[:, 1].astype(np.int32),
        tri[:, 2].astype(np.int32),
    )


def _fill_nearest(vals: np.ndarray) -> np.ndarray:
    """Rellena NaN con el valor válido más cercano (la tierra queda cubierta por la malla)."""
    from scipy.ndimage import distance_transform_edt

    mask = ~np.isfinite(vals)
    if not mask.any():
        return vals
    idx = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return vals[tuple(idx)]


def _bbox_ring(b: BBox, n: int = 24):
    lat0, lat1, lon0, lon1 = b
    lons = np.r_[
        np.linspace(lon0, lon1, n), np.full(n, lon1), np.linspace(lon1, lon0, n), np.full(n, lon0)
    ]
    lats = np.r_[
        np.full(n, lat0), np.linspace(lat0, lat1, n), np.full(n, lat1), np.linspace(lat1, lat0, n)
    ]
    return lons, lats


def fig_globe(
    regions: list[Region],
    active: str,
    field: xr.DataArray | None = None,
    coast_path: str | Path | None = None,
    lang: str = "es",
    height: int = 560,
    texture_step: int = 2,
    land_path: str | Path | None = None,
) -> go.Figure:
    """Globo 3D WebGL: SST real como textura, costas, retícula y regiones del catálogo.

    La cámara apunta a la región activa. `field` es una malla global (lat, lon) en °C.
    """
    fig = go.Figure()
    act = next((r for r in regions if r.id == active), regions[0])

    # esfera base (tierra) — un poco más pequeña que la capa de datos
    lo, la = np.meshgrid(np.linspace(-180, 180, 73), np.linspace(-90, 90, 37))
    bx, by, bz = (a.astype(np.float32) for a in _xyz(lo, la, 0.995))
    fig.add_trace(
        go.Surface(
            x=bx,
            y=by,
            z=bz,
            surfacecolor=np.zeros_like(bx),
            colorscale=[[0, TOK["land"]], [1, TOK["land"]]],
            showscale=False,
            hoverinfo="skip",
            lighting={"ambient": 0.9, "diffuse": 0.3, "specular": 0.05},
        )
    )
    # capa de SST (huecos en tierra)
    if field is not None:
        f = field.sortby("lat")
        if texture_step > 1:  # textura más ligera para la web (~0.4 MB en lugar de 2.4 MB)
            f = f.coarsen(lat=texture_step, lon=texture_step, boundary="trim").mean()
        lon2, lat2 = np.meshgrid(f["lon"].values, f["lat"].values)
        vals = f.values.astype(float)
        x, y, z = _xyz(lon2, lat2, 1.0)
        # La SST cubre todo el globo (tierra rellenada con el océano más cercano) y la
        # tierra se dibuja encima como malla: costas nítidas sin halos de color falsos.
        vals = _fill_nearest(vals)
        label = "SST" if lang == "en" else "TSM"
        fig.add_trace(
            go.Surface(
                x=x.astype(np.float32),
                y=y.astype(np.float32),
                z=z.astype(np.float32),
                surfacecolor=vals.astype(np.float32),
                colorscale=_thermal_scale(),
                cmin=-2,
                cmax=32,
                colorbar={
                    "title": {"text": f"{label} °C", "font": {**FONT, "family": MONO, "size": 11}},
                    "thickness": 10,
                    "len": 0.55,
                    "x": 0.98,
                    "outlinewidth": 0,
                    "tickfont": {**FONT, "size": 10},
                },
                hoverinfo="skip",
                lighting={"ambient": 0.85, "diffuse": 0.45, "specular": 0.08, "roughness": 0.9},
                lightposition={"x": 1000, "y": -1000, "z": 2000},
            )
        )
    if land_path and Path(land_path).exists():
        lx, ly, lz, i, j, k = land_mesh(str(land_path))
        fig.add_trace(
            go.Mesh3d(
                x=lx,
                y=ly,
                z=lz,
                i=i,
                j=j,
                k=k,
                color=TOK["land"],
                flatshading=False,
                hoverinfo="skip",
                showscale=False,
                lighting={"ambient": 0.9, "diffuse": 0.25, "specular": 0.02},
            )
        )
    # retícula
    grid = [(np.linspace(-180, 180, 120), np.full(120, lat)) for lat in range(-60, 90, 30)]
    grid += [(np.full(90, lon), np.linspace(-90, 90, 90)) for lon in range(-180, 180, 30)]
    gx, gy, gz = _lines3d(grid, 1.002)
    fig.add_trace(
        go.Scatter3d(
            x=gx,
            y=gy,
            z=gz,
            mode="lines",
            hoverinfo="skip",
            line={"color": "rgba(240,239,236,0.13)", "width": 1},
        )
    )
    # costas
    if coast_path and Path(coast_path).exists():
        cx, cy, cz = _lines3d(_coast_segments_110m(str(coast_path)), 1.004)
        fig.add_trace(
            go.Scatter3d(
                x=cx,
                y=cy,
                z=cz,
                mode="lines",
                hoverinfo="skip",
                line={"color": "rgba(240,239,236,0.55)", "width": 1.6},
            )
        )
    # regiones: contorno del bbox + marcador con etiqueta
    for reg in regions:
        is_act = reg.id == act.id
        rx, ry, rz = _lines3d([_bbox_ring(reg.bbox)], 1.008)
        fig.add_trace(
            go.Scatter3d(
                x=rx,
                y=ry,
                z=rz,
                mode="lines",
                hoverinfo="skip",
                line={
                    "color": TOK["accent"] if is_act else "rgba(195,194,183,0.55)",
                    "width": 5 if is_act else 2,
                },
            )
        )
    # marcadores: etiqueta visible solo en la región activa; el resto al pasar el cursor
    mk = [r.marker or {"lat": np.mean(r.bbox[:2]), "lon": np.mean(r.bbox[2:])} for r in regions]
    mx, my, mz = _xyz(np.array([m["lon"] for m in mk]), np.array([m["lat"] for m in mk]), 1.02)
    names = [r.name(lang) for r in regions]
    is_act = [r.id == act.id for r in regions]
    fig.add_trace(
        go.Scatter3d(
            x=mx,
            y=my,
            z=mz,
            mode="markers+text",
            text=[f"<b>{n}</b>" if a else "" for n, a in zip(names, is_act, strict=True)],
            customdata=names,
            textposition="top center",
            textfont={"color": TOK["ink"], "size": 14, "family": "Archivo, system-ui"},
            marker={
                "size": [8 if a else 5 for a in is_act],
                "color": [TOK["accent"] if a else TOK["ink2"] for a in is_act],
                "symbol": "diamond",
                "line": {"color": TOK["page"], "width": 1},
            },
            hovertemplate="%{customdata}<extra></extra>",
        )
    )
    # cámara hacia la región activa
    clon = float(np.mean(act.bbox[2:]))
    clat = float(np.mean(act.bbox[:2]))
    ex, ey, ez = _xyz(clon, clat, 1.32)
    fig.update_layout(
        height=height,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene={
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "zaxis": {"visible": False},
            "aspectmode": "data",
            "bgcolor": "rgba(0,0,0,0)",
            "camera": {"eye": {"x": ex, "y": ey, "z": ez}, "up": {"x": 0, "y": 0, "z": 1}},
            "dragmode": "orbit",
        },
        hoverlabel={"bgcolor": TOK["surface"], "bordercolor": TOK["base"], "font": FONT},
        uirevision=active,
    )
    return fig


# ============================================================ mapa de tendencia
@lru_cache(maxsize=16)
def coast_lines(bbox: BBox, land_zip: str) -> tuple[list, list]:
    """Línea de costa (Natural Earth 10 m) recortada al bbox, lista para Plotly."""
    import geopandas as gpd
    from shapely import clip_by_rect

    lat0, lat1, lon0, lon1 = bbox
    if not Path(land_zip).exists():
        return [], []
    land = gpd.read_file(f"zip://{land_zip}", bbox=(lon0 - 1, lat0 - 1, lon1 + 1, lat1 + 1))
    xs, ys = [], []
    for geom in land.geometry:
        b = clip_by_rect(geom.boundary, lon0, lat0, lon1, lat1)
        lines = getattr(b, "geoms", [b])
        for ln in lines:
            if ln.is_empty or ln.geom_type != "LineString":
                continue
            x, y = ln.xy
            xs += [*x, None]
            ys += [*y, None]
    return xs, ys


def fig_trend_map(
    result: xr.Dataset,
    units: str,
    coast: tuple[list, list] | None = None,
    marker: dict | None = None,
    height: int = 400,
) -> go.Figure:
    """Pendiente de Sen solo donde es significativa; el resto del mar en gris.

    Escala divergente azul↔gris↔rojo centrada en 0. Un píxel con p ≥ 0.05 nunca lleva
    color divergente (además se exige FDR, ver trend_map).
    """
    lats, lons = result["lat"].values, result["lon"].values
    slope = result["slope"].values.astype(float)
    tested = np.isfinite(result["p"].values)
    sig = (
        result["significant"].values.astype(bool)
        if "significant" in result
        else result["p"].values < 0.05
    )
    sig &= tested
    z_all = np.where(tested, 0.0, np.nan)
    z_sig = np.where(sig, slope, np.nan)
    finite = np.abs(z_sig[np.isfinite(z_sig)])
    zcap = float(np.nanpercentile(finite, 98)) if finite.size else 1.0
    zcap = max(zcap, 1e-6)
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            x=lons,
            y=lats,
            z=z_all,
            showscale=False,
            hoverinfo="skip",
            colorscale=[[0, TOK["nonsig"]], [1, TOK["nonsig"]]],
        )
    )
    fig.add_trace(
        go.Heatmap(
            x=lons,
            y=lats,
            z=z_sig,
            colorscale=DIVERGING,
            zmin=-zcap,
            zmax=zcap,
            zmid=0,
            colorbar={
                "title": {"text": units, "side": "right", "font": FONT},
                "tickfont": FONT,
                "outlinewidth": 0,
                "thickness": 12,
                "len": 0.85,
            },
            hovertemplate="lon %{x:.2f} · lat %{y:.2f}<br>Sen %{z:.3f} "
            + units
            + "<extra></extra>",
        )
    )
    if coast and coast[0]:
        fig.add_trace(
            go.Scatter(
                x=coast[0],
                y=coast[1],
                mode="lines",
                hoverinfo="skip",
                line={"color": TOK["muted"], "width": 1.2},
                showlegend=False,
            )
        )
    if marker:
        fig.add_trace(
            go.Scatter(
                x=[marker["lon"]],
                y=[marker["lat"]],
                mode="markers+text",
                text=[marker.get("label", "")],
                textposition="bottom center",
                textfont={"color": TOK["ink2"], "size": 11},
                marker={
                    "color": TOK["accent2"],
                    "size": 11,
                    "symbol": "triangle-up",
                    "line": {"color": "#020617", "width": 1},
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )
    ratio = 1 / max(np.cos(np.radians(float(np.mean(lats)))), 0.2)
    axis = {"gridcolor": TOK["grid"], "linecolor": TOK["base"], "tickfont": FONT, "zeroline": False}
    fig.update_layout(
        **_base_layout(
            height=height,
            xaxis=axis
            | {
                "title": {"text": "longitud", "font": FONT},
                "range": [lons.min(), lons.max()],
                "constrain": "domain",
            },
            yaxis=axis
            | {
                "title": {"text": "latitud", "font": FONT},
                "range": [lats.min(), lats.max()],
                "scaleanchor": "x",
                "scaleratio": ratio,
            },
            showlegend=False,
        )
    )
    return fig


# ================================================================ serie
def fig_series(
    series: pd.Series,
    trend,
    units: str,
    height: int = 400,
    labels: tuple[str, str] = ("anomalía mensual", "tendencia (Sen)"),
    transform=None,
) -> go.Figure:
    """Anomalías con relleno cálido/frío + recta de Sen luminosa y selector de rango.

    `transform` permite mostrar en otra escala (p. ej. log10 → %) sin cambiar el cálculo.
    """
    s = series.dropna()
    tr = transform or (lambda v: v)
    t = np.asarray(s.index.year + (s.index.month - 0.5) / 12.0)
    y = np.asarray(tr(s.to_numpy()), float)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=np.where(y > 0, y, 0),
            mode="lines",
            line={"width": 0},
            fill="tozeroy",
            fillcolor="rgba(251,113,133,0.30)",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=np.where(y < 0, y, 0),
            mode="lines",
            line={"width": 0},
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.30)",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=s.index,
            y=y,
            name=labels[0],
            mode="lines",
            line={"color": TOK["accent"], "width": 1.6},
            hovertemplate="%{y:.3f} " + units + "<extra></extra>",
        )
    )
    if trend is not None and np.isfinite(trend.slope_per_decade):
        yline = np.asarray(tr(trend.intercept + trend.slope_per_decade / 10 * (t - t[0])), float)
        fig.add_trace(
            go.Scatter(
                x=s.index,
                y=yline,
                mode="lines",
                hoverinfo="skip",
                showlegend=False,
                line={"color": "rgba(251,191,36,0.25)", "width": 9},
            )
        )
        fig.add_trace(
            go.Scatter(
                x=s.index,
                y=yline,
                name=labels[1],
                mode="lines",
                line={"color": TOK["accent2"], "width": 2.4, "dash": "dash"},
                hoverinfo="skip",
            )
        )
    axis = {"gridcolor": TOK["grid"], "linecolor": TOK["base"], "tickfont": FONT}
    btn = {
        "bgcolor": "rgba(15,23,42,0.85)",
        "activecolor": "#0ea5e9",
        "bordercolor": TOK["base"],
        "borderwidth": 1,
        "font": {**FONT, "color": TOK["ink"]},
    }
    fig.update_layout(
        **_base_layout(
            height=height,
            xaxis=axis
            | {
                "zeroline": False,
                "showspikes": True,
                "spikecolor": TOK["accent"],
                "spikethickness": 1,
                "spikedash": "dot",
                "spikemode": "across",
                "rangeselector": btn
                | {
                    "buttons": [
                        {"count": 5, "label": "5A", "step": "year", "stepmode": "backward"},
                        {"count": 10, "label": "10A", "step": "year", "stepmode": "backward"},
                        {"step": "all", "label": "∞"},
                    ],
                    "x": 0,
                    "y": 1.02,
                },
                "rangeslider": {
                    "visible": True,
                    "thickness": 0.07,
                    "bgcolor": "rgba(15,23,42,0.6)",
                    "bordercolor": TOK["base"],
                },
            },
            yaxis=axis
            | {"title": {"text": units, "font": FONT}, "zerolinecolor": "rgba(226,232,240,0.35)"},
            legend={"orientation": "h", "y": 1.13, "x": 1, "xanchor": "right", "font": FONT},
            hovermode="x unified",
            margin={"l": 54, "r": 10, "t": 30, "b": 20},
        )
    )
    return fig


def fig_stripes(series: pd.Series, units: str, transform=None, height: int = 130) -> go.Figure:
    """Franjas de anomalía anual (estilo 'warming stripes'): un vistazo a 23 años."""
    s = series.dropna()
    tr = transform or (lambda v: v)
    annual = s.groupby(s.index.year).mean()
    vals = np.asarray(tr(annual.to_numpy()), float)
    lim = float(np.nanmax(np.abs(vals))) or 1.0
    stripes = [
        [0.0, "#0c2a6b"],
        [0.2, "#1d4ed8"],
        [0.4, "#7dd3fc"],
        [0.5, "#e2e8f0"],
        [0.6, "#fda4af"],
        [0.8, "#e11d48"],
        [1.0, "#7f1d1d"],
    ]
    fig = go.Figure(
        go.Bar(
            x=annual.index.astype(str),
            y=np.ones_like(vals),
            marker={
                "color": vals,
                "colorscale": stripes,
                "cmin": -lim,
                "cmax": lim,
                "line": {"width": 0},
            },
            customdata=vals,
            hovertemplate="%{x} · %{customdata:+.3f} " + units + "<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            height=height,
            bargap=0,
            margin={"l": 0, "r": 0, "t": 0, "b": 22},
            xaxis={"showgrid": False, "tickfont": FONT, "linecolor": "rgba(0,0,0,0)", "dtick": 2},
            yaxis={"visible": False, "range": [0, 1]},
            showlegend=False,
        )
    )
    return fig
