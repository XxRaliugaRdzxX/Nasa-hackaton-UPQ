"""Pipeline de la investigación del equipo Cardinals Hyperyon (D19).

Portado del notebook `Colab/NASA_Datos (1).ipynb` (PASOS 1.5–12b) con los MISMOS métodos
y parámetros, más dos validaciones añadidas por el sistema:
  - SST independiente MUR25 (multisensor) contra la SST diurna de MODIS-Aqua.
  - ANOVA de anomalías por periodos (sección 4 del reporte técnico del equipo).

Entrada : data/research/raw/<var>/<YYYYMM>.nc  (mece research fetch)
Salida  : data/research/results/  (results.json, series.parquet, mapas *.nc, regiones.geojson)
"""

from __future__ import annotations

import json
import logging
import warnings
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pymannkendall as mk
import statsmodels.api as sm
import xarray as xr
from scipy import stats
from scipy.signal import detrend
from statsmodels.stats.multitest import multipletests

from mece.acquisition import data as D
from mece.research.fetch import month_path, research_config, research_dir
from mece.research.geometry import basin_masks, region_masks, regions_geojson

log = logging.getLogger(__name__)
warnings.filterwarnings("ignore", category=RuntimeWarning)

pct = lambda b: (10**b - 1) * 100  # noqa: E731  log10 → %


def results_dir() -> Path:
    d = research_dir() / "results"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ================================================================ cubos
def load_cube(key: str, ref: xr.DataArray | None = None) -> xr.DataArray:
    """Une los meses descargados en un solo arreglo float32 preasignado (memoria acotada).

    Si se da `ref`, cada mes se reubica en su rejilla (PASO 1.6 del notebook).
    """
    cfg = research_config()
    files = [
        (ym, month_path(key, ym))
        for ym in D.month_range(cfg["period"]["start"], cfg["period"]["end"])
    ]
    files = [(ym, f) for ym, f in files if f.exists()]
    if not files:
        raise FileNotFoundError(f"Sin datos de '{key}'. Ejecuta: mece research fetch")
    with D.NC_LOCK, xr.open_dataarray(files[0][1]) as a0:
        grid = (ref if ref is not None else a0.isel(time=0, drop=True)).load()
    arr = np.full((len(files), grid.sizes["lat"], grid.sizes["lon"]), np.nan, dtype="float32")
    times = []
    for k, (ym, f) in enumerate(files):
        with D.NC_LOCK, xr.open_dataarray(f) as a:
            a = a.isel(time=0, drop=True).load()
        if ref is not None:
            a = a.reindex(lat=grid.lat, lon=grid.lon, method="nearest", tolerance=0.02)
        arr[k] = a.values
        times.append(pd.Period(ym, "M").start_time)
    return xr.DataArray(
        arr,
        dims=("time", "lat", "lon"),
        name=key,
        coords={"time": times, "lat": grid.lat.values, "lon": grid.lon.values},
    )


# ================================================================ PASO 1.5 — series regionales
def regional_series(cube: xr.DataArray, var: str, masks: dict, cov_min: float) -> pd.DataFrame:
    w = np.cos(np.deg2rad(cube.lat)).astype("float32")  # float32: evita duplicar memoria
    rows = []
    for key, m in masks.items():
        datos = cube.where(m)
        log10 = var in ("chl", "viirs")
        transf = np.log10(datos) if log10 else datos
        media = transf.weighted(w).mean(("lat", "lon"))
        n_val = datos.notnull().sum(("lat", "lon"))
        df = pd.DataFrame(
            {
                "fecha": pd.to_datetime(cube.time.values),
                "variable": var,
                "region": key,
                "media": 10**media.values if log10 else media.values,
                "cobertura_pct": 100 * n_val.values / max(int(m.sum()), 1),
            }
        )
        df.loc[df.cobertura_pct < cov_min, "media"] = np.nan
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


def add_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """PASO 2.1: climatología del mismo mes en todo el periodo; clorofila en log10."""
    df = df.copy()
    is_log = df.variable.isin(["chl", "viirs"])
    df["y"] = np.where(is_log, np.log10(df.media), df.media)
    df["mes"] = df.fecha.dt.month
    clim = df.groupby(["variable", "region", "mes"])["y"].transform("mean")
    df["clim"] = clim
    df["anomalia"] = df.y - clim
    df["anomalia_pct"] = np.where(is_log, pct(df.anomalia), np.nan)
    return df.sort_values(["variable", "region", "fecha"])


# ================================================================ PASO 3.1 — tendencia
def sen_con_ic(t, y, var_s, alfa=0.05):
    """Pendiente de Sen + IC (Gilbert 1987) con la varianza de S corregida (Hamed-Rao).

    Con series muy cortas la corrección de Hamed-Rao puede dar una varianza no positiva;
    en ese caso se devuelve la pendiente sin intervalo (NaN).
    """
    i, j = np.triu_indices(len(y), k=1)
    p = np.sort((y[j] - y[i]) / (t[j] - t[i]))
    n = len(p)
    if not np.isfinite(var_s) or var_s <= 0:
        return float(np.median(p)), float("nan"), float("nan")
    c = stats.norm.ppf(1 - alfa / 2) * np.sqrt(var_s)
    lo = int(np.clip(np.floor((n - c) / 2), 0, n - 1))
    hi = int(np.clip(np.ceil((n + c) / 2), 0, n - 1))
    return float(np.median(p)), float(p[lo]), float(p[hi])


def years_from(fechas: pd.Series | pd.DatetimeIndex) -> np.ndarray:
    f = pd.DatetimeIndex(fechas)
    return ((f - f[0]).days / 365.25).values


def trend_row(d: pd.DataFrame, var: str) -> dict:
    d = d.sort_values("fecha").dropna(subset=["anomalia"])
    t, y = years_from(d.fecha), d.anomalia.values
    mk_cl, mk_hr = mk.original_test(y), mk.hamed_rao_modification_test(y)
    mk_se = mk.seasonal_test(d.y.values, period=12)
    sen, lo, hi = sen_con_ic(t, y, mk_hr.var_s)
    ols = sm.OLS(y, sm.add_constant(t)).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
    b, (b_lo, b_hi) = ols.params[1], ols.conf_int()[1]
    out = {
        "p_mk": mk_cl.p,
        "p_hr": mk_hr.p,
        "p_ols": ols.pvalues[1],
        "p_seasonal": mk_se.p,
        "tau": mk_hr.Tau,
        "years": float(t[-1]),
    }
    if var in ("chl", "viirs"):
        nivel = 10 ** d.y.mean()
        out |= {
            "sen": pct(sen * 10),
            "lo": pct(lo * 10),
            "hi": pct(hi * 10),
            "sen_abs": nivel * (10 ** (sen * 10) - 1),
            "total": pct(sen * t[-1]),
            "ols": pct(b * 10),
            "ols_lo": pct(b_lo * 10),
            "ols_hi": pct(b_hi * 10),
            "unit": "%/década",
        }
    else:
        out |= {
            "sen": sen * 10,
            "lo": lo * 10,
            "hi": hi * 10,
            "total": sen * t[-1],
            "ols": b * 10,
            "ols_lo": b_lo * 10,
            "ols_hi": b_hi * 10,
            "unit": "°C/década",
        }
    return out


def classify(slope: float, p: float) -> str:
    if p < 0.05:
        return "increase_sig" if slope > 0 else "decrease_sig"
    if p < 0.10:
        return "increase_marginal" if slope > 0 else "decrease_marginal"
    return "none"


# ================================================================ PASO 4 — tendencias por celda
def cell_trends(
    cube: xr.DataArray,
    var: str,
    ocean: xr.DataArray,
    factor: int,
    min_frac: float,
    fdr_alpha: float,
) -> xr.Dataset:
    c = cube.where(ocean)
    if var == "chl":
        c = np.log10(c)
    n = c.notnull().coarsen(lat=factor, lon=factor, boundary="trim").sum()
    g = c.coarsen(lat=factor, lon=factor, boundary="trim").mean()
    g = g.where(n >= factor * factor / 2)
    anom = (g.groupby("time.month") - g.groupby("time.month").mean("time")).drop_vars("month")
    y_all = anom.values
    nt, ny, nx = y_all.shape
    slope = np.full((ny, nx), np.nan)
    pval = np.full((ny, nx), np.nan)
    for i in range(ny):
        for j in range(nx):
            y = y_all[:, i, j]
            ok = np.isfinite(y)
            if ok.sum() < min_frac * nt:
                continue
            r = mk.hamed_rao_modification_test(y[ok])
            slope[i, j] = r.slope * 120
            pval[i, j] = r.p
    if var == "chl":
        slope = pct(slope)
    sig = np.zeros_like(pval, dtype=bool)
    f = np.isfinite(pval)
    sig[f] = multipletests(pval[f], method="fdr_bh", alpha=fdr_alpha)[0]
    return xr.Dataset(
        {
            "slope": (("lat", "lon"), slope),
            "p": (("lat", "lon"), pval),
            "sig_fdr": (("lat", "lon"), sig),
        },
        coords={"lat": anom.lat, "lon": anom.lon},
    )


# ================================================================ PASO 5.4 — correlación
def corr_adjusted(x, y):
    """Spearman con n efectivo de Bretherton (autocorrelación de ambas series)."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    r = stats.spearmanr(x, y)[0]
    rx, ry = pd.Series(x).autocorr(1), pd.Series(y).autocorr(1)
    n = len(x)
    neff = float(np.clip(n * (1 - rx * ry) / (1 + rx * ry), 3, n))
    tt = r * np.sqrt((neff - 2) / (1 - r**2))
    return float(r), float(2 * stats.t.sf(abs(tt), neff - 2)), n, neff


# ================================================================ PASO 9 — régimen
def pettitt(x):
    x = np.asarray(x)
    n = len(x)
    s = np.sign(x[None, :] - x[:, None])
    u = np.array([s[: k + 1, k + 1 :].sum() for k in range(n - 1)])
    k = int(np.argmax(np.abs(u)))
    return k, min(1.0, 2 * np.exp(-6 * abs(u[k]) ** 2 / (n**3 + n**2)))


def bic(rss, n, k):
    return n * np.log(rss / n) + k * np.log(n)


# ================================================================ PASO 11 — bootstrap
def sen_fast(t, y):
    i, j = np.triu_indices(len(y), k=1)
    return np.median((y[j] - y[i]) / (t[j] - t[i]))


def bootstrap_blocks(t, y, rng, b=1000, block=12):
    b0 = sen_fast(t, y)
    a0 = np.median(y - b0 * t)
    res = y - (a0 + b0 * t)
    n = len(y)
    nb = int(np.ceil(n / block))
    out = np.empty(b)
    for k in range(b):
        starts = rng.integers(0, n - block + 1, nb)
        r = np.concatenate([res[s : s + block] for s in starts])[:n]
        out[k] = sen_fast(t, a0 + b0 * t + r)
    return b0, out


def read_oni() -> pd.Series:
    rows = {}
    for line in (research_dir() / "ancillary" / "oni.data").read_text().splitlines():
        p = line.split()
        if len(p) == 13 and p[0].isdigit():
            for m, v in enumerate(p[1:], 1):
                if float(v) > -90:
                    rows[pd.Timestamp(int(p[0]), m, 1)] = float(v)
    return pd.Series(rows).sort_index()


# ================================================================ orquestación
def run() -> dict:  # noqa: C901 — un paso por bloque, como en el notebook
    cfg = research_config()
    regions = list(cfg["regions"])
    cov = cfg["coverage_min_pct"]
    rng = np.random.default_rng(42)
    res: dict = {
        "meta": {
            "generated": datetime.now(UTC).isoformat(timespec="seconds"),
            "period": cfg["period"],
            "source": "Colab/NASA_Datos (1).ipynb (portado)",
        }
    }

    # ---- PASO 1.5/1.6: cubos y series regionales (uno a la vez para acotar memoria)
    chl = load_cube("chl")
    masks = region_masks(chl)
    res["meta"]["pixels"] = {k: int(m.sum()) for k, m in masks.items()}
    series = [regional_series(chl, "chl", masks, cov)]
    ocean = masks["gulf"]
    maps = {
        "chl": cell_trends(
            chl, "chl", ocean, cfg["grid_factor"], cfg["grid_min_valid"], cfg["fdr_alpha"]
        )
    }
    ref = chl.isel(time=0, drop=True).copy()
    del chl
    sst = load_cube("sst", ref=ref)
    series.append(regional_series(sst, "sst", masks, cov))
    maps["sst"] = cell_trends(
        sst, "sst", ocean, cfg["grid_factor"], cfg["grid_min_valid"], cfg["fdr_alpha"]
    )
    del sst
    for key in ("flh", "viirs"):
        try:
            cube = load_cube(key, ref=ref)
            series.append(regional_series(cube, key, masks, cov))
            del cube
        except FileNotFoundError:
            log.warning("sin %s; se omite la validación", key)
    df = add_anomalies(pd.concat(series, ignore_index=True))
    for v, ds in maps.items():
        ds.to_netcdf(results_dir() / f"map_trend_{v}.nc")
    log.info("series y mapas listos")

    # ---- PASO 2.2 ciclo estacional (climatología) y 2.4 diagnósticos
    clim = (
        df[df.variable.isin(["chl", "sst"])]
        .groupby(["variable", "region", "mes"])
        .y.mean()
        .reset_index()
    )
    clim["valor"] = np.where(clim.variable == "chl", 10**clim.y, clim.y)
    res["climatology"] = clim[["variable", "region", "mes", "valor"]].to_dict("records")
    diag = []
    for (var, reg), d in df[df.variable.isin(["chl", "sst"])].groupby(["variable", "region"]):
        a = d.anomalia.dropna()
        r1 = a.autocorr(1)
        diag.append(
            {
                "variable": var,
                "region": reg,
                "skew_raw": float(stats.skew(d.media.dropna())),
                "skew": float(stats.skew(d.y.dropna())),
                "r1": float(r1),
                "n": len(a),
                "neff": float(len(a) * (1 - r1) / (1 + r1)),
            }
        )
    res["diagnostics"] = diag

    # ---- PASO 3.2 tabla de tendencias + FDR
    tend = []
    for var in ("chl", "sst"):
        for reg in regions:
            row = trend_row(df[(df.variable == var) & (df.region == reg)], var)
            tend.append({"variable": var, "region": reg, **row})
    tend = pd.DataFrame(tend)
    tend["q"] = multipletests(tend.p_hr, method="fdr_bh")[1]
    tend["result"] = [classify(s, p) for s, p in zip(tend.sen, tend.p_hr, strict=True)]

    # ---- PASO 4.4 resumen espacial
    spatial = []
    for var, ds in maps.items():
        lon2, lat2 = np.meshgrid(ds.lon, ds.lat)
        sl, sg = ds.slope.values, ds.sig_fdr.values
        for reg in regions:
            m = np.isfinite(sl)
            box = cfg["regions"][reg]["box"]
            if box:
                x0, x1, y0, y1 = box
                m &= (lon2 >= x0) & (lon2 <= x1) & (lat2 >= y0) & (lat2 <= y1)
            n = int(m.sum())
            spatial.append(
                {
                    "variable": var,
                    "region": reg,
                    "cells": n,
                    "median": float(np.nanmedian(sl[m])),
                    "pct_up": 100 * float((sg & (sl > 0) & m).sum()) / max(n, 1),
                    "pct_down": 100 * float((sg & (sl < 0) & m).sum()) / max(n, 1),
                }
            )
    spatial = pd.DataFrame(spatial)

    # ---- PASO 5.2/5.3 precipitación por cuenca
    pp_cube = load_cube("pp")
    bm = basin_masks(pp_cube.isel(time=0))
    w = np.cos(np.deg2rad(pp_cube.lat)).astype("float32")
    pp = []
    for key, m in bm.items():
        s = pp_cube.where(m).weighted(w).mean(("lat", "lon"))
        pp.append(
            pd.DataFrame(
                {
                    "fecha": pd.to_datetime(pp_cube.time.values),
                    "cuenca": key,
                    "pp": s.values,
                    "celdas": int(m.sum()),
                }
            )
        )
    del pp_cube
    pp = pd.concat(pp, ignore_index=True)
    pp["mes"] = pp.fecha.dt.month
    pp["anomalia"] = pp.pp - pp.groupby(["cuenca", "mes"]).pp.transform("mean")
    tend_pp = []
    for key, d in pp.groupby("cuenca"):
        d = d.sort_values("fecha").dropna(subset=["anomalia"])
        t, y = years_from(d.fecha), d.anomalia.values
        hr = mk.hamed_rao_modification_test(y)
        sen, lo, hi = sen_con_ic(t, y, hr.var_s)
        ols = sm.OLS(y, sm.add_constant(t)).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
        anual = d.pp.mean() * 12
        tend_pp.append(
            {
                "basin": key,
                "cells": int(d.celdas.iloc[0]),
                "annual_mm": anual,
                "sen": sen * 120,
                "lo": lo * 120,
                "hi": hi * 120,
                "sen_pct": 100 * sen * 120 / anual,
                "p_hr": hr.p,
                "p_ols": ols.pvalues[1],
                "result": classify(sen, hr.p),
                "last": str(d.fecha.max().date()),
            }
        )
    tend_pp = pd.DataFrame(tend_pp)

    # ---- PASO 5.4/6.1 correlaciones
    def an_series(var, reg):
        return (
            df[(df.variable == var) & (df.region == reg)].set_index("fecha").anomalia.sort_index()
        )

    corr_pp = []
    for basin, reg in cfg["pairs"]:
        x = pp[pp.cuenca == basin].set_index("fecha").anomalia
        y = an_series("chl", reg)
        d = pd.concat({"x": x, "y": y}, axis=1).dropna()
        d["x"], d["y"] = detrend(d.x.values), detrend(d.y.values)
        for lag in range(5):
            r, p, n, neff = corr_adjusted(d.x.shift(lag).values, d.y.values)
            corr_pp.append(
                {
                    "basin": basin,
                    "region": reg,
                    "lag": lag,
                    "r": r,
                    "p": p,
                    "n": n,
                    "neff": neff,
                    "control": [basin, reg] == cfg["pairs"][-1],
                }
            )
    corr_pp = pd.DataFrame(corr_pp)
    corr_pp["q"] = multipletests(corr_pp.p, method="fdr_bh")[1]
    corr_sst = []
    for reg in regions:
        d = pd.concat({"x": an_series("sst", reg), "y": an_series("chl", reg)}, axis=1).dropna()
        r, p, n, neff = corr_adjusted(detrend(d.x.values), detrend(d.y.values))
        corr_sst.append({"region": reg, "r": r, "p": p, "neff": neff})
    corr_sst = pd.DataFrame(corr_sst)
    corr_sst["q"] = multipletests(corr_sst.p, method="fdr_bh")[1]

    # ---- PASO 6.2 robustez (quitar un año)
    rob = []
    for reg in ("banco", "mississippi", "tamaulipas", "deep", "florida"):
        d = df[(df.variable == "chl") & (df.region == reg)].sort_values("fecha")
        rows = []
        for anio in sorted(d.fecha.dt.year.unique()):
            dd = d[d.fecha.dt.year != anio].dropna(subset=["anomalia"])
            t, y = years_from(dd.fecha), dd.anomalia.values
            hr = mk.hamed_rao_modification_test(y)
            rows.append(
                {"year": int(anio), "sen": pct(sen_con_ic(t, y, hr.var_s)[0] * 10), "p": hr.p}
            )
        r = pd.DataFrame(rows)
        rob.append(
            {
                "region": reg,
                "sen_min": r.sen.min(),
                "sen_max": r.sen.max(),
                "p_max": r.p.max(),
                "weakest_year": int(r.loc[r.p.idxmax(), "year"]),
                "pct_sig": 100 * (r.p < 0.05).mean(),
                "by_year": rows,
            }
        )

    # ---- PASO 6.3/6.4 matriz y nivel de evidencia
    rob_pct = {r["region"]: r["pct_sig"] for r in rob}
    tend["evidence"] = [
        "none"
        if r.p_hr >= 0.10
        else (
            "solid"
            if (
                r.p_hr < 0.05
                and r.q < 0.05
                and (r.variable != "chl" or rob_pct.get(r.region, 100) >= 80)
            )
            else "weak"
        )
        for r in tend.itertuples()
    ]
    tend_pp["evidence"] = [
        "none" if p >= 0.10 else ("solid" if p < 0.05 else "weak") for p in tend_pp.p_hr
    ]

    # ---- PASO 7 Weatherhead
    weath = []
    for var in ("chl", "sst"):
        for reg in regions:
            d = (
                df[(df.variable == var) & (df.region == reg)]
                .sort_values("fecha")
                .dropna(subset=["anomalia"])
            )
            t, y = years_from(d.fecha), d.anomalia.values
            hr = mk.hamed_rao_modification_test(y)
            w0 = sen_con_ic(t, y, hr.var_s)[0]
            ruido = y - (np.median(y - w0 * t) + w0 * t)
            sigma, phi = ruido.std(ddof=1), pd.Series(ruido).autocorr(1)
            n_req = ((3.3 * sigma / abs(w0)) * np.sqrt((1 + phi) / (1 - phi))) ** (2 / 3)
            weath.append(
                {
                    "variable": var,
                    "region": reg,
                    "years_needed": float(n_req),
                    "years_available": float(t[-1]),
                    "detectable_by": int(np.ceil(2003 + n_req)),
                }
            )

    # ---- PASO 8 tendencias por estación
    season_of = {
        12: "DEF",
        1: "DEF",
        2: "DEF",
        3: "MAM",
        4: "MAM",
        5: "MAM",
        6: "JJA",
        7: "JJA",
        8: "JJA",
        9: "SON",
        10: "SON",
        11: "SON",
    }
    an2 = df[df.variable.isin(["chl", "sst"])].copy()
    an2["temporada"] = an2.fecha.dt.month.map(season_of)
    an2["anio_temp"] = an2.fecha.dt.year + (an2.fecha.dt.month == 12)
    est = (
        an2.groupby(["variable", "region", "temporada", "anio_temp"])
        .anomalia.agg(["mean", "count"])
        .reset_index()
    )
    est = est[est["count"] == 3]
    seas = []
    for (var, reg, tem), d in est.groupby(["variable", "region", "temporada"]):
        r = mk.original_test(d.sort_values("anio_temp")["mean"].values)
        pend = r.slope * 10
        seas.append(
            {
                "variable": var,
                "region": reg,
                "season": tem,
                "trend": pct(pend) if var == "chl" else pend,
                "p": r.p,
            }
        )
    seas = pd.DataFrame(seas)
    seas["q"] = multipletests(seas.p, method="fdr_bh")[1]

    # ---- PASO 9 cambio gradual o salto
    anual = (
        an2[an2.fecha.dt.year.between(2003, 2025)]
        .groupby(["variable", "region", an2.fecha.dt.year.rename("anio")])
        .anomalia.mean()
        .reset_index()
    )
    regime = []
    for (var, reg), d in anual.groupby(["variable", "region"]):
        d = d.sort_values("anio")
        x, years = d.anomalia.values, d.anio.values
        n = len(x)
        k, p = pettitt(x)
        antes, despues = x[: k + 1].mean(), x[k + 1 :].mean()
        rss_step = ((x[: k + 1] - antes) ** 2).sum() + ((x[k + 1 :] - despues) ** 2).sum()
        b = np.polyfit(years, x, 1)
        rss_lin = ((x - np.polyval(b, years)) ** 2).sum()
        dbic = bic(rss_lin, n, 2) - bic(rss_step, n, 3)
        regime.append(
            {
                "variable": var,
                "region": reg,
                "year": int(years[k + 1]),
                "p": float(p),
                "jump": pct(despues - antes) if var == "chl" else float(despues - antes),
                "dbic": float(dbic),
                "model": "step" if dbic > 2 else ("linear" if dbic < -2 else "either"),
            }
        )
    res["annual_anomalies"] = anual.to_dict("records")

    # ---- PASO 10 regresión múltiple (+ ONI) y 10b atribución
    from statsmodels.stats.outliers_influence import variance_inflation_factor

    oni = read_oni()
    res["oni"] = [{"fecha": str(k.date()), "oni": v} for k, v in oni["2003":].items()]
    coefs, summary, attrib = [], [], []
    for reg, (basin, lag) in cfg["models"].items():
        d = pd.DataFrame({"chl": an_series("chl", reg), "SST": an_series("sst", reg)})
        if basin:
            d["Lluvia"] = pp[pp.cuenca == basin].set_index("fecha").anomalia.sort_index().shift(lag)
        d["ONI"] = oni
        d = d.dropna()
        d["Tiempo"] = (d.index - d.index[0]).days / 365.25
        z = (d - d.mean()) / d.std()
        x_mat = sm.add_constant(z.drop(columns="chl"))
        fit = sm.OLS(z.chl, x_mat).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
        ic = fit.conf_int()
        for i, c in enumerate(x_mat.columns):
            if c != "const":
                coefs.append(
                    {
                        "region": reg,
                        "predictor": c,
                        "beta": fit.params[c],
                        "lo": ic.loc[c, 0],
                        "hi": ic.loc[c, 1],
                        "p": fit.pvalues[c],
                        "vif": variance_inflation_factor(x_mat.values, i),
                    }
                )
        b_t = fit.params["Tiempo"] * d.chl.std() / d.Tiempo.std()
        summary.append(
            {
                "region": reg,
                "r2": fit.rsquared,
                "n": int(fit.nobs),
                "residual_trend": pct(b_t * 10),
                "p_residual": fit.pvalues["Tiempo"],
            }
        )
        fit2 = sm.OLS(d.chl, sm.add_constant(d.drop(columns="chl"))).fit()
        row = {"region": reg, "total": pct(np.polyfit(d.Tiempo, d.chl, 1)[0] * 10)}
        for c in ("SST", "Lluvia", "ONI"):
            row[c] = pct(fit2.params[c] * np.polyfit(d.Tiempo, d[c], 1)[0] * 10) if c in d else None
        row["residual"] = pct(fit2.params["Tiempo"] * 10)
        attrib.append(row)
    coefs = pd.DataFrame(coefs)
    coefs["q"] = multipletests(coefs.p, method="fdr_bh")[1]

    # ---- PASO 11 bootstrap de dirección y probabilidad de meses extremos
    boot, extremes, curves = [], [], []
    for var in ("chl", "sst"):
        conv = (lambda b: pct(b * 10)) if var == "chl" else (lambda b: b * 10)
        for reg in regions:
            s = an_series(var, reg).dropna()
            t = years_from(s.index)
            b0, bs = bootstrap_blocks(t, s.values, rng)
            boot.append(
                {
                    "variable": var,
                    "region": reg,
                    "slope": conv(b0),
                    "lo": conv(np.percentile(bs, 2.5)),
                    "hi": conv(np.percentile(bs, 97.5)),
                    "p_pos": float((bs > 0).mean()),
                    "p_neg": float((bs < 0).mean()),
                }
            )
    for var in ("sst", "chl"):
        for reg in regions:
            s = an_series(var, reg).dropna()
            base = s[s.index.year <= 2012]
            ev = (s > base.quantile(0.9)) if var == "sst" else (s < base.quantile(0.1))
            ev = ev.astype(int)
            t = (s.index.year + (s.index.month - 0.5) / 12 - 2003).values
            x_mat = sm.add_constant(pd.Series(t, index=s.index, name="t"))
            m = sm.GLM(ev, x_mat, family=sm.families.Binomial()).fit(
                cov_type="HAC", cov_kwds={"maxlags": 12}
            )
            tt = np.linspace(0, 23, 47)
            prob = m.predict(np.column_stack([np.ones_like(tt), tt]))
            curves.append(
                {
                    "variable": var,
                    "region": reg,
                    "year": (2003 + tt).round(2).tolist(),
                    "prob": (100 * prob).round(2).tolist(),
                }
            )
            extremes.append(
                {
                    "variable": var,
                    "region": reg,
                    "freq_early": 100 * ev[s.index.year <= 2012].mean(),
                    "freq_late": 100 * ev[s.index.year >= 2016].mean(),
                    "prob_2003": 100 * float(prob[0]),
                    "prob_2025": 100 * float(m.predict(np.array([[1.0, t.max()]]))[0]),
                    "odds_decade": float(np.exp(10 * m.params["t"])),
                    "p": float(m.pvalues["t"]),
                }
            )
    extremes = pd.DataFrame(extremes)
    extremes["q"] = multipletests(extremes.p, method="fdr_bh")[1]

    # ---- PASO 12 validación (nFLH, VIIRS) y 12b deriva + serie combinada (D18: titular)
    def reg_series(var, reg):
        return df[(df.variable == var) & (df.region == reg)].set_index("fecha").y.sort_index()

    def anomaly(s):
        return s - s.groupby(s.index.month).transform("mean")

    def sen_ic_p(s):
        s = s.dropna()
        t = years_from(s.index)
        hr = mk.hamed_rao_modification_test(s.values)
        b, lo, hi = sen_con_ic(t, s.values, hr.var_s)
        return b * 10, lo * 10, hi * 10, hr.p

    valid, drift, combined_series, drift_series = [], [], [], []
    have_val = {"flh", "viirs"} <= set(df.variable.unique())
    for reg in regions if have_val else []:
        chl_s, flh_s, vii_s = (
            reg_series("chl", reg),
            reg_series("flh", reg),
            reg_series("viirs", reg),
        )
        b_c, _, _, p_c = sen_ic_p(anomaly(chl_s))
        b_f, _, _, p_f = sen_ic_p(anomaly(flh_s))
        a_c, a_f = anomaly(chl_s), anomaly(flh_s)
        ok = a_c.notna() & a_f.notna()
        c12, v12 = chl_s["2012":"2025"], vii_s["2012":"2025"]
        b_m, _, _, p_m = sen_ic_p(anomaly(c12))
        b_v, _, _, p_v = sen_ic_p(anomaly(v12))
        a_m, a_v = anomaly(c12), anomaly(v12)
        ok2 = a_m.notna() & a_v.notna()
        valid.append(
            {
                "region": reg,
                "chl": pct(b_c),
                "p_chl": p_c,
                "flh": 100 * b_f / flh_s.mean(),
                "p_flh": p_f,
                "r_chl_flh": float(stats.spearmanr(a_c[ok], a_f[ok])[0]),
                "chl_1225": pct(b_m),
                "p_chl_1225": p_m,
                "viirs_1225": pct(b_v),
                "p_viirs_1225": p_v,
                "r_modis_viirs": float(stats.spearmanr(a_m[ok2], a_v[ok2])[0]),
            }
        )
        dif = (chl_s - vii_s)["2012":"2025"].dropna()
        d_b, d_lo, d_hi, d_p = sen_ic_p(dif)
        offset = (chl_s - vii_s)["2012":"2014"].mean()
        comb = pd.concat([chl_s[:"2011-12"], (vii_s + offset)["2012":]]).sort_index()
        c_b, c_lo, c_hi, c_p = sen_ic_p(anomaly(comb))
        drift.append(
            {
                "region": reg,
                "drift": pct(d_b),
                "drift_lo": pct(d_lo),
                "drift_hi": pct(d_hi),
                "p_drift": d_p,
                "modis": pct(b_c),
                "p_modis": p_c,
                "combined": pct(c_b),
                "comb_lo": pct(c_lo),
                "comb_hi": pct(c_hi),
                "p_combined": c_p,
            }
        )
        roll = pct(dif.rolling(12, center=True).mean())
        drift_series += [
            {"region": reg, "fecha": str(k.date()), "pct": float(v)}
            for k, v in roll.dropna().items()
        ]
        ac = anomaly(comb)
        combined_series += [
            {"region": reg, "fecha": str(k.date()), "anomalia_pct": float(pct(v))}
            for k, v in ac.dropna().items()
        ]
    drift = pd.DataFrame(drift)
    if len(drift):
        drift["q_combined"] = multipletests(drift.p_combined, method="fdr_bh")[1]
        drift["result"] = [
            classify(s, p) for s, p in zip(drift.combined, drift.p_combined, strict=True)
        ]

    # ---- AÑADIDO: validación de SST con MUR25 (independiente de Aqua)
    mur = []
    try:
        from mece.catalog import CATALOG, load_stores

        spec, store = CATALOG["sst"], load_stores()["gom"]
        files = [
            D.monthly_path(spec, store, m)
            for m in D.month_range(cfg["period"]["start"], cfg["period"]["end"])
        ]
        parts = []
        for f in files:
            with D.NC_LOCK, xr.open_dataset(f) as ds:
                parts.append(ds["sst"].load())
        mcube = xr.concat(parts, dim="time")
        mmask = region_masks(mcube.isel(time=0))
        wm = np.cos(np.deg2rad(mcube.lat)).astype("float32")
        sst_tend = tend[tend.variable == "sst"].set_index("region")
        for reg, m in mmask.items():
            s = mcube.where(m).weighted(wm).mean(("lat", "lon")).to_series()
            a = s - s.groupby(s.index.month).transform("mean")
            t = years_from(a.index)
            hr = mk.hamed_rao_modification_test(a.values)
            b, lo, hi = sen_con_ic(t, a.values, hr.var_s)
            mur.append(
                {
                    "region": reg,
                    "mur": b * 10,
                    "mur_lo": lo * 10,
                    "mur_hi": hi * 10,
                    "p": hr.p,
                    "modis": float(sst_tend.loc[reg, "sen"]),
                }
            )
    except Exception as exc:  # noqa: BLE001
        log.warning("validación MUR25 omitida: %s", exc)

    # ---- AÑADIDO: ANOVA por periodos (reporte técnico, sección 4)
    periods = [(2003, 2010), (2011, 2017), (2018, 2025)]
    anova = []
    for var in ("sst", "chl"):
        a = anual[(anual.variable == var) & (anual.region == "gulf")]
        groups = [a[a.anio.between(p0, p1)].anomalia.values for p0, p1 in periods]
        f, p = stats.f_oneway(*groups)
        anova.append(
            {
                "variable": var,
                "periods": [f"{p0}–{p1}" for p0, p1 in periods],
                "means": [
                    float(g.mean()) if var == "sst" else float(pct(g.mean())) for g in groups
                ],
                "F": float(f),
                "p": float(p),
                "kruskal_p": float(stats.kruskal(*groups).pvalue),
            }
        )

    # ---- guardar
    res |= {
        "trends": tend.to_dict("records"),
        "spatial": spatial.to_dict("records"),
        "precip_trends": tend_pp.to_dict("records"),
        "corr_rain_chl": corr_pp.to_dict("records"),
        "corr_sst_chl": corr_sst.to_dict("records"),
        "robustness": rob,
        "weatherhead": weath,
        "seasonal": seas.to_dict("records"),
        "regime": regime,
        "regression": coefs.to_dict("records"),
        "regression_summary": summary,
        "attribution": attrib,
        "bootstrap": boot,
        "extremes": extremes.to_dict("records"),
        "extreme_curves": curves,
        "validation": valid,
        "drift": drift.to_dict("records"),
        "drift_series": drift_series,
        "combined_series": combined_series,
        "mur_validation": mur,
        "anova": anova,
    }
    out = results_dir()
    (out / "results.json").write_text(json.dumps(res, ensure_ascii=False, default=float))
    df.to_parquet(out / "series.parquet", index=False)
    pp.to_parquet(out / "precip.parquet", index=False)
    (out / "regions.geojson").write_text(json.dumps(regions_geojson()))
    D.update_status(
        "research", "results", {"state": "ready", "generated": res["meta"]["generated"]}
    )
    log.info("resultados guardados en %s", out)
    return res
