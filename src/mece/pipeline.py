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
    # Fin None = hasta el último mes completo: el worker busca en CMR y descarga solo lo que
    # NASA haya publicado (la clorofila estándar llega con meses de retraso; MUR25 en ~1 día).
    "chl": ("2002-07", None),  # MODISA_L3m_CHL R2022.0 estándar
    "sst": ("2002-09", None),  # MUR25
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


def globe_chl() -> Path:
    """Clorofila global del último mes NRT (MODIS-Aqua 9 km) para el globo."""
    import earthaccess

    from mece.acquisition.auth import login

    login()
    res = earthaccess.search_data(
        concept_id="C3380709124-OB_CLOUD",
        granule_name="*.L3m.MO.CHL.chlor_a.9km.NRT.nc",
        temporal=((date.today() - timedelta(days=120)).isoformat(), date.today().isoformat()),
    )
    if not res:
        raise RuntimeError("Sin clorofila mensual NRT reciente")
    g = sorted(res, key=lambda x: x["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"])[
        -1
    ]
    month = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:7]
    tmp = D.data_root() / "tmp" / "chl_globe"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        f = Path(earthaccess.download([g], str(tmp), show_progress=False)[0])
        with D.NC_LOCK, xr.open_dataset(f) as ds:
            chl = ds["chlor_a"].load()
    finally:
        for x in tmp.glob("*"):
            x.unlink(missing_ok=True)
    chl = chl.where((chl > 0.001) & (chl < 100)).rename("chlor_a")
    chl.attrs = {"units": "mg m-3", "month": month, "source": "MODIS-Aqua L3m 9km NRT"}
    out = D.data_root() / "spatial" / "globe" / "chl_global_latest.nc"
    D._atomic_to_netcdf(chl, out)
    D.update_status("globe", "chl", {"state": "ready", "date": month})
    return out


def globe_textures() -> dict:
    """Texturas JPEG + rejillas JSON para el globo (SST y clorofila)."""
    from mece.visualization import textures as TX

    g = D.data_root() / "spatial" / "globe"
    land = g / "ne_110m_land.geojson"
    out = {"sst": TX.build_sst_texture(g / "sst_global_latest.nc", land, g)}
    chl_nc = g / "chl_global_latest.nc"
    if chl_nc.exists():
        with xr.open_dataarray(chl_nc) as da:
            chl = da.load()
        out["chl"] = TX.build_chl_texture(chl, land, g, chl.attrs.get("month", ""))
    return out


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
