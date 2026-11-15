"""Pipeline de preparación de datos (lo ejecuta el worker, nunca la interfaz).

mece pipeline fetch --dataset chl --start 2002-07 --end 2026-04
mece pipeline globe          # textura de SST global para el globo 3D
mece pipeline precompute     # series, tendencias y mapas de cada caso
mece pipeline bootstrap      # todo lo anterior
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import xarray as xr

from mece.acquisition import data as D
from mece.catalog import CATALOG, load_regions, load_stores

log = logging.getLogger(__name__)

# Periodos completos disponibles (verificados en CMR, 2026-11-15)
DEFAULT_RANGES = {
    "chl": ("2002-07", "2026-04"),  # MODISA_L3m_CHL R2022.0 estándar
    "sst": ("2002-09", None),  # MUR25 hasta el último mes completo
}


def _last_complete_month() -> str:
    first_this = date.today().replace(day=1)
    return (first_this - timedelta(days=1)).strftime("%Y-%m")


def fetch(dataset_id: str, start: str | None = None, end: str | None = None) -> dict:
    """Llena todos los almacenes con el dataset entre start y end."""
    d0, d1 = DEFAULT_RANGES[dataset_id]
    start = start or d0
    end = end or d1 or _last_complete_month()
    months = D.month_range(start, end)
    stores = list(load_stores().values())
    log.info("fetch %s %s→%s en %s", dataset_id, start, end, [s.id for s in stores])
    if CATALOG[dataset_id].backend == "opendap":
        return D.ensure_mur25(stores, months)
    return D.ensure_modis_chl(stores, months)


# ------------------------------------------------------------- globo 3D
def globe_texture(step: int = 4) -> Path:
    """SST global del último día disponible de MUR25, submuestreada (1° con step=4)."""
    out = D.data_root() / "spatial" / "globe" / "sst_global_latest.nc"
    for back in range(1, 8):
        day = date.today() - timedelta(days=back)
        gran = f"{day:%Y%m%d}090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2"
        url = (
            f"https://opendap.earthdata.nasa.gov/collections/{D.MUR25_CONCEPT}"
            f"/granules/{gran}.dap.nc4"
        )
        ce = (
            f"/analysed_sst[0:1:0][0:{step}:719][0:{step}:1439];"
            f"/lat[0:{step}:719];/lon[0:{step}:1439]"
        )
        r = D._get_with_retry(url, params={"dap4.ce": ce})
        if r is None:
            continue
        tmp = out.with_suffix(".raw.nc4")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(r.content)
        with xr.open_dataset(tmp) as ds:
            sst = (ds["analysed_sst"].isel(time=0, drop=True) - 273.15).load()
        tmp.unlink(missing_ok=True)
        sst = sst.rename("sst")
        sst.attrs = {"units": "degC", "date": day.isoformat(), "source": "GHRSST MUR25 v4.2"}
        D._atomic_to_netcdf(sst, out)
        D.update_status("globe", "sst", {"state": "ready", "date": day.isoformat()})
        log.info("textura del globo: %s", day)
        return out
    raise RuntimeError("No se encontró un día reciente de MUR25 para el globo")


def coastline_110m() -> Path:
    """Costas y tierra Natural Earth 1:110m (GeoJSON ligeros) para el globo."""
    import requests

    base = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson"
    folder = D.data_root() / "spatial" / "globe"
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("ne_110m_coastline.geojson", "ne_110m_land.geojson"):
        out = folder / name
        if out.exists():
            continue
        r = requests.get(f"{base}/{name}", timeout=120)
        r.raise_for_status()
        json.loads(r.text)  # valida
        out.write_text(r.text)
    return folder / "ne_110m_coastline.geojson"


# ------------------------------------------------------------ precálculo
def precompute(cases: list[str] | None = None) -> dict:
    """Series, tendencia y mapa de tendencia para cada caso y dataset (periodo completo)."""
    from mece.statistics import analysis as A

    regions = load_regions()
    done = {}
    for cid, reg in regions.items():
        if cases and cid not in cases:
            continue
        for ds_id in reg.datasets:
            key = f"{cid}:{ds_id}"
            try:
                da = D.fetch_dataset(ds_id, reg.bbox, reg.t0, reg.t1, download_missing=False)
                if int(da.attrs.get("months_missing", 0)) > 0:
                    log.warning(
                        "%s incompleto (%s meses faltan); se omite", key, da.attrs["months_missing"]
                    )
                    continue
                anom = A.compute_anomalies(da)
                ck = A.result_cache_key(ds_id, reg.bbox, reg.t0, reg.t1)
                A.trend_map(anom, cache_key=ck)
                done[key] = "ok"
            except Exception as exc:  # noqa: BLE001
                log.error("precompute %s: %s", key, exc)
                done[key] = f"error: {exc}"
    D.update_status(
        "precompute",
        "all",
        {"state": "ready", "items": done, "at": datetime.now(UTC).isoformat(timespec="seconds")},
    )
    return done


def coverage_summary() -> dict[str, dict]:
    """Resumen de lo que hay en cada almacén (para la barra de estado)."""
    st = D.read_status()
    return {k: v for k, v in st.items() if k in CATALOG}


__all__ = ["fetch", "globe_texture", "coastline_110m", "precompute", "coverage_summary", "np"]
