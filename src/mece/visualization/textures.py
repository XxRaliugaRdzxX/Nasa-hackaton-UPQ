"""Texturas equirectangulares para el globo 3D (globe.gl) y rejillas para el hover.

Océano = dato real de NASA coloreado; tierra = Blue Marble (NASA) atenuada, para
que el dato del océano destaque. Salida: JPEG 2048×1024 + JSON con la rejilla a 1°
para leer el valor bajo el cursor.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr

W, H = 2048, 1024
BLUE_MARBLE_URL = "https://unpkg.com/three-globe@2.45.6/example/img/earth-blue-marble.jpg"


def _fill_nearest(a: np.ndarray) -> np.ndarray:
    from scipy.ndimage import distance_transform_edt

    mask = ~np.isfinite(a)
    if not mask.any():
        return a
    idx = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def _to_image_grid(da: xr.DataArray, fill: bool = True) -> np.ndarray:
    """(lat, lon) → matriz H×W con fila 0 = 90 N y columna 0 = 180 W."""
    from scipy.ndimage import zoom

    a = da.sortby("lat", ascending=False).sortby("lon").values.astype(float)
    if fill:
        a = _fill_nearest(a)
    return zoom(a, (H / a.shape[0], W / a.shape[1]), order=1)


def _land_mask(land_geojson: Path) -> np.ndarray:
    from rasterio.features import rasterize
    from rasterio.transform import from_origin
    from shapely.geometry import shape

    data = json.loads(Path(land_geojson).read_text())
    geoms = [shape(f["geometry"]) for f in data["features"]]
    tr = from_origin(-180, 90, 360 / W, 180 / H)
    return rasterize(geoms, out_shape=(H, W), transform=tr, fill=0, default_value=1).astype(bool)


def _blue_marble(cache: Path) -> np.ndarray:
    import requests
    from PIL import Image

    if not cache.exists():
        r = requests.get(BLUE_MARBLE_URL, timeout=120)
        r.raise_for_status()
        cache.write_bytes(r.content)
    img = Image.open(cache).convert("RGB").resize((W, H), Image.LANCZOS)
    return np.asarray(img).astype(np.float32) / 255.0


def _compose(
    ocean_rgb: np.ndarray, land: np.ndarray, bm: np.ndarray, ocean_nodata=None
) -> np.ndarray:
    out = ocean_rgb.copy()
    land_rgb = bm * 0.62 + np.array([0.02, 0.03, 0.06]) * 0.38  # tierra real, atenuada y fría
    out[land] = land_rgb[land]
    if ocean_nodata is not None:
        nd = ocean_nodata & ~land
        out[nd] = np.array([0.04, 0.07, 0.14])  # océano sin dato (nubes/hielo): azul noche
    # borde costero luminoso muy sutil (realza continentes sobre el océano)
    from scipy.ndimage import binary_dilation

    edge = binary_dilation(land, iterations=1) & ~land
    out[edge] = out[edge] * 0.55 + np.array([0.75, 0.9, 1.0]) * 0.45
    return np.clip(out, 0, 1)


def _save_jpeg(rgb: np.ndarray, dest: Path) -> Path:
    from PIL import Image

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.jpg")
    Image.fromarray((rgb * 255).astype(np.uint8)).save(
        tmp, quality=90, optimize=True, progressive=True
    )
    tmp.replace(dest)
    return dest


def _save_grid(da: xr.DataArray, dest: Path, decimals: int, step: float = 1.0) -> Path:
    """Rejilla para el hover: valores redondeados, null en tierra/sin dato."""
    g = da.sortby("lat", ascending=False).sortby("lon")
    res = float(abs(g["lat"].diff("lat").mean()))
    f = max(1, int(round(step / res)))
    if f > 1:
        g = g.coarsen(lat=f, lon=f, boundary="trim").mean()
    vals = np.where(np.isfinite(g.values), np.round(g.values, decimals), np.nan)
    payload = {
        "lat0": float(g["lat"].values[0]),
        "lon0": float(g["lon"].values[0]),
        "dlat": float(g["lat"].values[1] - g["lat"].values[0]),
        "dlon": float(g["lon"].values[1] - g["lon"].values[0]),
        "nlat": int(g.sizes["lat"]),
        "nlon": int(g.sizes["lon"]),
        "v": [None if not np.isfinite(x) else float(x) for x in vals.ravel()],
    }
    dest.write_text(json.dumps(payload, separators=(",", ":")))
    return dest


def build_sst_texture(sst_nc: Path, land_geojson: Path, out_dir: Path) -> dict:
    import cmocean

    with xr.open_dataarray(sst_nc) as da:
        sst = da.load()
    grid = _to_image_grid(sst)
    norm = np.clip((grid + 2) / 34.0, 0, 1)
    rgb = cmocean.cm.thermal(norm)[..., :3]
    land = _land_mask(land_geojson)
    bm = _blue_marble(out_dir / "earth-blue-marble.jpg")
    img = _save_jpeg(_compose(rgb, land, bm), out_dir / "tex_sst.jpg")
    grd = _save_grid(sst, out_dir / "grid_sst.json", 1)
    return {"texture": img, "grid": grd, "date": sst.attrs.get("date", "")}


def build_chl_texture(chl: xr.DataArray, land_geojson: Path, out_dir: Path, date: str) -> dict:
    """Clorofila (log) con paleta tipo 'ocean color' de NASA; sin dato = azul noche."""
    import matplotlib

    lc = np.log10(chl.where(chl > 0))
    nodata_src = ~np.isfinite(lc)
    grid = _to_image_grid(lc, fill=False)
    nodata = ~np.isfinite(grid)
    from scipy.ndimage import zoom

    nd = (
        zoom(
            nodata_src.sortby("lat", ascending=False).values.astype(float),
            (H / lc.sizes["lat"], W / lc.sizes["lon"]),
            order=0,
        )
        > 0.5
    )
    grid = np.where(np.isfinite(grid), grid, -2)
    norm = np.clip((grid + 2) / (np.log10(30) + 2), 0, 1)  # 0.01 – 30 mg m-3
    rgb = matplotlib.colormaps["turbo"](norm)[..., :3]
    land = _land_mask(land_geojson)
    bm = _blue_marble(out_dir / "earth-blue-marble.jpg")
    img = _save_jpeg(_compose(rgb, land, bm, ocean_nodata=nd | nodata), out_dir / "tex_chl.jpg")
    chl_coarse = (
        chl.coarsen(lat=12, lon=12, boundary="trim").mean() if chl.sizes["lat"] > 1000 else chl
    )
    grd = _save_grid(chl_coarse, out_dir / "grid_chl.json", 3)
    (out_dir / "tex_chl.meta.json").write_text(json.dumps({"date": date}))
    return {"texture": img, "grid": grd, "date": date}
