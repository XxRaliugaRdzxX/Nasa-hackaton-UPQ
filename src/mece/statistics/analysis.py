"""Análisis de tendencias (contratos D14 · metodología docs/04).

- compute_anomalies : valor − climatología del mismo mes (log10 para clorofila).
- regional_series   : media espacial ponderada por área, filtro de temporada.
- trend_test        : Mann-Kendall (estacional / Hamed-Rao) + pendiente de Sen.
- trend_map         : MK + Sen píxel a píxel, vectorizado, con FDR (Benjamini-Hochberg).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats

from mece.catalog import BBox, bbox_hash

log = logging.getLogger(__name__)

SEASONS = {
    "all": tuple(range(1, 13)),
    "wet": (6, 7, 8, 9, 10),  # lluvias jun–oct
    "dry": (11, 12, 1, 2, 3, 4, 5),  # secas nov–may
}
ALPHA = 0.05
FDR_Q = 0.10  # Wilks (2016) para campos espacialmente correlacionados
MIN_REGION_COVERAGE = 0.30


# ================================================================ anomalías
def _climatology_window(da: xr.DataArray) -> xr.DataArray:
    """Periodo de referencia: config/analysis.yaml ∩ datos; si no alcanza, todo el registro."""
    try:
        from mece.config import get_settings

        clim = get_settings().analysis.climatology
        sub = da.sel(time=slice(f"{clim.start}-01", f"{clim.end}-28"))
        if sub.sizes.get("time", 0) >= 10 * 12:
            sub.attrs["clim_period"] = f"{clim.start}…{clim.end}"
            return sub
    except Exception:  # noqa: BLE001 — sin config se usa el registro completo
        pass
    out = da
    out.attrs["clim_period"] = "registro completo"
    return out


def compute_anomalies(da: xr.DataArray) -> xr.DataArray:
    """anomalía = valor − climatología mensual (groupby time.month). Misma forma que da.

    Si el dataset se analiza en escala logarítmica (clorofila, attrs['log_transform']),
    la anomalía se calcula sobre log10(valor): un +0.1 equivale a ×1.26 (26 % sobre lo
    normal).
    """
    log_t = bool(int(da.attrs.get("log_transform", 0)))
    x = np.log10(da.where(da > 0)) if log_t else da
    x.attrs = dict(da.attrs)
    base = _climatology_window(x)
    clim = base.groupby("time.month").mean("time")
    anom = x.groupby("time.month") - clim
    anom = anom.drop_vars("month", errors="ignore")
    anom.attrs = dict(da.attrs) | {
        "anomaly_space": "log10" if log_t else "linear",
        "clim_period": base.attrs.get("clim_period", ""),
    }
    # climatología regional (para expresar el cambio relativo)
    w = np.cos(np.deg2rad(da["lat"]))
    clim_mean = da.weighted(w.fillna(0)).mean(("lat", "lon")).mean().item()
    anom.attrs["clim_mean"] = float(clim_mean)
    anom.name = da.name
    return anom


# ============================================================ serie regional
def regional_series(anom: xr.DataArray, season: str = "all") -> pd.Series:
    """Promedio espacial ponderado por área (cos lat). season ∈ {"all", "wet", "dry"}.

    Los meses con menos del 30 % de píxeles válidos (nubes) quedan como NaN.
    """
    if season not in SEASONS:
        raise ValueError(f"season debe ser una de {list(SEASONS)}")
    w = np.cos(np.deg2rad(anom["lat"])).broadcast_like(anom.isel(time=0, drop=True))
    valid = anom.notnull()
    ocean = anom.notnull().any("time")
    coverage = valid.where(ocean).sum(("lat", "lon")) / max(int(ocean.sum()), 1)
    mean = anom.weighted(w.fillna(0)).mean(("lat", "lon"), skipna=True)
    mean = mean.where(coverage >= MIN_REGION_COVERAGE)
    s = mean.to_series()
    s.index = pd.DatetimeIndex(s.index).to_period("M").to_timestamp()
    s = s[s.index.month.isin(SEASONS[season])]
    s.name = "anomaly"
    s.attrs = {k: anom.attrs.get(k) for k in ("units", "anomaly_space", "clim_mean", "dataset_id")}
    s.attrs["season"] = season
    s.attrs["coverage_mean"] = float(coverage.mean())
    return s


# ============================================================ prueba de tendencia
@dataclass
class TrendResult:
    slope_per_decade: float  # en unidades de la serie (log10 para clorofila)
    intercept: float  # valor de la recta de Sen en el primer instante de la serie
    p: float
    z: float
    n: int
    significant: bool
    # --- extensiones
    method: str = ""
    ci_low: float = float("nan")  # IC 95 % de la pendiente (por década)
    ci_high: float = float("nan")
    p_hamed_rao: float = float("nan")
    robust: bool = True  # ambas pruebas coinciden
    t_start: float = float("nan")  # año decimal inicial

    def as_dict(self) -> dict:
        return asdict(self)


def _decimal_year(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray(idx.year + (idx.month - 0.5) / 12.0, dtype=np.float64)


def trend_test(series: pd.Series) -> TrendResult:
    """Mann-Kendall + pendiente de Sen.

    - Serie con los 12 meses: Mann-Kendall **estacional con covarianza entre
      estaciones** (Hirsch & Slack, 1984).
    - Serie filtrada por temporada: Mann-Kendall con corrección **Hamed-Rao**.
    La pendiente es Theil-Sen sobre años decimales, con IC 95 %.
    """
    import pymannkendall as mk

    s = series.dropna().sort_index()
    n = int(s.size)
    if n < 24:
        return TrendResult(np.nan, np.nan, np.nan, np.nan, n, False, method="datos insuficientes")
    t = _decimal_year(pd.DatetimeIndex(s.index))
    y = s.to_numpy(float)
    res = stats.theilslopes(y, t, alpha=0.95)
    slope, intercept_0, lo, hi = res.slope, res.intercept, res.low_slope, res.high_slope

    hr = mk.hamed_rao_modification_test(y)
    full_year = s.attrs.get("season", "all") == "all" and len(set(s.index.month)) == 12
    if full_year:
        regular = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="MS"))
        # Hirsch-Slack: incluye la covarianza entre meses (los meses vecinos están
        # correlacionados; la versión simple infla los falsos positivos)
        sea = mk.correlated_seasonal_test(regular.to_numpy(float), period=12)
        p, z, method = float(sea.p), float(sea.z), "Mann-Kendall estacional (Hirsch-Slack) + Sen"
    else:
        p, z, method = float(hr.p), float(hr.z), "Mann-Kendall (Hamed-Rao) + Sen"
    robust = (p < ALPHA) == (hr.p < ALPHA)
    return TrendResult(
        slope_per_decade=float(slope * 10),
        intercept=float(intercept_0 + slope * t[0]),
        p=p,
        z=z,
        n=n,
        significant=bool(p < ALPHA),
        method=method,
        ci_low=float(lo * 10),
        ci_high=float(hi * 10),
        p_hamed_rao=float(hr.p),
        robust=bool(robust),
        t_start=float(t[0]),
    )


# ============================================================ mapa de tendencia
def result_cache_key(dataset_id: str, bbox: BBox, t0: str, t1: str, season: str = "all") -> str:
    return f"trend_{dataset_id}_{bbox_hash(bbox)}_{t0[:7]}_{t1[:7]}_{season}"


def _results_dir() -> Path:
    from mece.config import get_settings

    return get_settings().data_dir / "results"


def _bh_fdr(p: np.ndarray, q: float) -> np.ndarray:
    """Benjamini-Hochberg: máscara de rechazos (NaN → False)."""
    out = np.zeros(p.shape, bool)
    ok = np.isfinite(p)
    pv = p[ok]
    if pv.size == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * pv.size / (np.arange(pv.size) + 1)
    passed = ranked <= q
    if passed.any():
        kmax = np.max(np.nonzero(passed)[0])
        rej = np.zeros(pv.size, bool)
        rej[order[: kmax + 1]] = True
        out[ok] = rej
    return out


def _mk_sen_block(y: np.ndarray, t: np.ndarray) -> tuple[np.ndarray, ...]:
    """MK + Sen vectorizado para un bloque (n_pix, n_time) con NaN."""
    n_t = y.shape[1]
    iu, ju = np.triu_indices(n_t, k=1)
    dy = y[:, ju] - y[:, iu]  # (pix, pares)
    dt = (t[ju] - t[iu]).astype(np.float32)
    slopes = dy / dt
    sen = np.nanmedian(slopes, axis=1)
    sgn = np.sign(dy)
    s_stat = np.nansum(sgn, axis=1)
    n = np.sum(np.isfinite(y), axis=1).astype(np.float64)
    var = n * (n - 1) * (2 * n + 5) / 18.0
    # corrección AR(1) de la varianza (Matalas/Bayley-Hammersley) sobre residuos de Sen
    med_t = np.nanmedian(np.where(np.isfinite(y), t[None, :], np.nan), axis=1)
    med_y = np.nanmedian(y, axis=1)
    resid = y - (med_y[:, None] + sen[:, None] * (t[None, :] - med_t[:, None]))
    r0 = resid[:, :-1]
    r1_ = resid[:, 1:]
    m = np.isfinite(r0) & np.isfinite(r1_)
    mu = np.nanmean(resid, 1)[:, None]
    num = np.nansum(np.where(m, (r0 - mu) * (r1_ - mu), 0), 1)
    den = np.nansum((resid - mu) ** 2, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = np.clip(num / den, -0.99, 0.99)
        factor = np.where(r1 > 0, (1 + r1) / (1 - r1), 1.0)
        z = np.where(s_stat > 0, s_stat - 1, np.where(s_stat < 0, s_stat + 1, 0.0)) / np.sqrt(
            var * factor
        )
    p = 2 * stats.norm.sf(np.abs(z))
    return sen, p, n, z


def trend_map(anom: xr.DataArray, min_valid: int = 120, cache_key: str | None = None) -> xr.Dataset:
    """MK + Sen píxel a píxel sobre anomalías (ya sin estacionalidad).

    Devuelve un Dataset con slope (unidades/década), p, n y significant (FDR
    Benjamini-Hochberg q = 0.10 sobre los píxeles válidos). Si `cache_key` existe en
    data/results/, se carga en lugar de calcular.
    """
    if cache_key:
        path = _results_dir() / f"{cache_key}.nc"
        if path.exists():
            with xr.open_dataset(path) as ds:
                return ds.load()
    t_idx = pd.DatetimeIndex(anom["time"].values)
    t = _decimal_year(t_idx).astype(np.float64)
    arr = anom.transpose("lat", "lon", "time").to_numpy().astype(np.float32)
    ny, nx, nt = arr.shape
    flat = arr.reshape(-1, nt)
    n_valid = np.isfinite(flat).sum(1)
    todo = np.nonzero(n_valid >= min_valid)[0]
    slope = np.full(flat.shape[0], np.nan, np.float32)
    pval = np.full(flat.shape[0], np.nan, np.float64)
    # bloque acotado: ~40 MB de pares por bloque
    pairs = nt * (nt - 1) // 2
    block = max(16, int(10_000_000 / max(pairs, 1)))
    for b0 in range(0, todo.size, block):
        idx = todo[b0 : b0 + block]
        sen, p, _, _ = _mk_sen_block(flat[idx], t)
        slope[idx] = sen * 10
        pval[idx] = p
    # significativo = pasa FDR y además p < 0.05 (el mapa nunca colorea p ≥ 0.05)
    sig = _bh_fdr(pval, FDR_Q) & (pval < ALPHA)
    ds = xr.Dataset(
        {
            "slope": (("lat", "lon"), slope.reshape(ny, nx)),
            "p": (("lat", "lon"), pval.reshape(ny, nx)),
            "n": (("lat", "lon"), n_valid.reshape(ny, nx).astype(np.int16)),
            "significant": (("lat", "lon"), sig.reshape(ny, nx)),
        },
        coords={"lat": anom["lat"].values, "lon": anom["lon"].values},
        attrs={
            "method": "Mann-Kendall (var. corregida AR1) + Sen por píxel; FDR Benjamini-Hochberg",
            "fdr_q": FDR_Q,
            "min_valid": min_valid,
            "anomaly_space": anom.attrs.get("anomaly_space", "linear"),
            "units": str(anom.attrs.get("units", "")),
            "period": f"{t_idx.min():%Y-%m}…{t_idx.max():%Y-%m}",
            "n_pixels_tested": int(todo.size),
            "n_pixels_significant": int(sig.sum()),
        },
    )
    if cache_key:
        path = _results_dir() / f"{cache_key}.nc"
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        ds.to_netcdf(tmp)
        tmp.replace(path)
    return ds


def percent_per_decade(slope_log10_per_decade: float) -> float:
    """Convierte una pendiente en log10/década a %/década."""
    return (10**slope_log10_per_decade - 1) * 100
