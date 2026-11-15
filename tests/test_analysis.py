"""Criterios de aceptación de la especificación (D14) sobre datos sintéticos."""

import numpy as np
import pandas as pd
import pymannkendall as mk
import pytest
import xarray as xr

from mece.statistics.analysis import (
    _mk_sen_block,
    compute_anomalies,
    regional_series,
    trend_map,
    trend_test,
)

RNG = np.random.default_rng(42)
TIME = pd.date_range("2003-01-01", "2025-12-01", freq="MS")


def _cube(trend_per_year=0.03, ny=6, nx=7, noise=0.25, ar=0.3):
    """Cubo con ciclo estacional, tendencia conocida y ruido AR(1)."""
    t = np.arange(TIME.size) / 12.0
    seasonal = 2.0 * np.sin(2 * np.pi * TIME.month.to_numpy() / 12)
    e = np.zeros((TIME.size, ny, nx))
    eps = RNG.normal(0, noise, e.shape)
    for i in range(1, TIME.size):
        e[i] = ar * e[i - 1] + eps[i]
    data = 26 + seasonal[:, None, None] + trend_per_year * t[:, None, None] + e
    da = xr.DataArray(
        data,
        dims=("time", "lat", "lon"),
        coords={"time": TIME, "lat": np.linspace(18, 20, ny), "lon": np.linspace(-94, -91, nx)},
        attrs={"units": "°C", "log_transform": 0},
    )
    return da


def test_anomalies_keep_shape_and_remove_seasonality():
    da = _cube()
    an = compute_anomalies(da)
    assert an.shape == da.shape
    by_month = an.groupby("time.month").mean(("time", "lat", "lon"))
    assert float(abs(by_month).max()) < 0.4  # sin ciclo estacional residual


def test_trend_test_recovers_injected_slope_within_10pct():
    """Criterio 3: pendiente inyectada recuperada dentro de ±10 %."""
    da = _cube(trend_per_year=0.03)
    s = regional_series(compute_anomalies(da))
    r = trend_test(s)
    assert r.significant and r.p < 0.001
    assert r.slope_per_decade == pytest.approx(0.30, rel=0.10)
    assert r.ci_low < r.slope_per_decade < r.ci_high


def test_false_positive_rate_without_trend():
    """Sin tendencia, la tasa de falsos positivos debe rondar α = 0.05 (≤ 12 % en 40 réplicas)."""
    hits = 0
    for _ in range(40):
        da = _cube(trend_per_year=0.0, ny=2, nx=2, noise=0.3, ar=0.3)
        hits += trend_test(regional_series(compute_anomalies(da))).significant
    assert hits / 40 <= 0.12


def test_season_filter_keeps_only_requested_months():
    s = regional_series(compute_anomalies(_cube()), season="wet")
    assert set(s.index.month) == {6, 7, 8, 9, 10}
    assert trend_test(s).method.startswith("Mann-Kendall (Hamed-Rao)")


def test_vectorized_sen_matches_pymannkendall():
    y = RNG.normal(0, 1, (5, 60)).astype(np.float32) + np.arange(60) * 0.05
    t = np.arange(60, dtype=float)
    sen, _, _, _ = _mk_sen_block(y, t)
    for k in range(5):
        assert sen[k] == pytest.approx(mk.sens_slope(y[k]).slope, rel=1e-4, abs=1e-6)


def test_trend_map_never_colors_p_ge_005():
    """Criterio 4: ningún píxel 'significativo' tiene p ≥ 0.05."""
    da = _cube(trend_per_year=0.0, noise=0.3)
    da[:, :3, :] += (np.arange(TIME.size) / 12.0 * 0.05)[:, None, None]  # tendencia en la mitad
    tm = trend_map(compute_anomalies(da), min_valid=120)
    sig = tm["significant"].values
    assert sig.any()
    assert np.all(tm["p"].values[sig] < 0.05)
    assert set(tm.data_vars) >= {"slope", "p", "n"}


def test_log_transform_for_chlorophyll():
    da = np.exp(_cube(noise=0.05) / 10)
    da.attrs = {"units": "mg m-3", "log_transform": 1}
    an = compute_anomalies(da)
    assert an.attrs["anomaly_space"] == "log10"
