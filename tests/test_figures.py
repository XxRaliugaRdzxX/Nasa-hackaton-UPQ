"""Las figuras se construyen sin errores y respetan las reglas de la especificación."""

import numpy as np
import pandas as pd
import xarray as xr

from mece.catalog import load_regions
from mece.statistics.analysis import TrendResult
from mece.visualization.figures import fig_globe, fig_series, fig_trend_map


def test_globe_points_camera_to_active_region():
    regs = list(load_regions().values())
    field = xr.DataArray(
        np.full((10, 20), 25.0),
        dims=("lat", "lon"),
        coords={"lat": np.linspace(-80, 80, 10), "lon": np.linspace(-170, 170, 20)},
    )
    fig = fig_globe(regs, "gulf_california", field=field)
    eye = fig.layout.scene.camera.eye
    lon = np.degrees(np.arctan2(eye.y, eye.x))
    assert -116 < lon < -104  # la cámara mira al Golfo de California


def test_trend_map_never_colors_nonsignificant():
    ds = xr.Dataset(
        {
            "slope": (("lat", "lon"), np.array([[1.0, -1.0], [0.5, np.nan]])),
            "p": (("lat", "lon"), np.array([[0.01, 0.20], [0.04, np.nan]])),
            "n": (("lat", "lon"), np.array([[200, 200], [200, 0]])),
            "significant": (("lat", "lon"), np.array([[True, False], [False, False]])),
        },
        coords={"lat": [18.0, 19.0], "lon": [-94.0, -93.0]},
    )
    fig = fig_trend_map(ds, "°C / década")
    z_sig = np.asarray(fig.data[1].z, float)
    assert np.isfinite(z_sig[0, 0]) and np.isnan(z_sig[0, 1]) and np.isnan(z_sig[1, 0])


def test_series_has_anomaly_and_sen_lines():
    idx = pd.date_range("2003-01-01", periods=48, freq="MS")
    s = pd.Series(np.linspace(0, 1, 48), index=idx)
    tr = TrendResult(0.25, 0.0, 0.01, 2.5, 48, True)
    fig = fig_series(s, tr, "°C")
    assert [d.name for d in fig.data] == ["anomalía mensual", "tendencia (Sen)"]
    assert fig.data[1].line.dash == "dash"
