"""Descarga mensual de los productos de la investigación (portado de los PASOS 1.2–1.4,
5.2 y 12.1 del notebook del equipo), con el patrón del sistema: un archivo global a la
vez, recorte inmediato, borrado del global e idempotencia por mes.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from mece.acquisition import data as D
from mece.config import ROOT, get_settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def research_config() -> dict:
    with (ROOT / "config" / "research.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def research_dir() -> Path:
    return get_settings().data_dir / "research"


def month_path(key: str, ym: str) -> Path:
    return research_dir() / "raw" / key / f"{ym.replace('-', '')}.nc"


def _bbox_for(key: str) -> list[float]:
    cfg = research_config()
    return cfg["bbox_basins"] if key == "pp" else cfg["bbox_ocean"]


def _crop_month(path: Path, key: str, prod, ym: str) -> None:
    """Recorta un archivo global al bbox de la investigación y lo guarda (float32)."""
    lat0, lat1, lon0, lon1 = _bbox_for(key)
    per = pd.Period(ym, "M")
    with D.NC_LOCK:
        kw = {"group": prod.group} if prod.group else {}
        with xr.open_dataset(path, decode_times=False, **kw) as ds:
            da = ds[prod.file_variable]
            if "time" in da.dims:
                da = da.isel(time=0, drop=True)
            if prod.dims_order:  # IMERG: (lon, lat) → (lat, lon)
                da = da.transpose("lat", "lon")
            da = da.sortby("lat").sel(lat=slice(lat0, lat1), lon=slice(lon0, lon1)).load()
            units = str(da.attrs.get("units", ""))
            if prod.quality_variable and prod.quality_variable in ds:
                q = ds[prod.quality_variable]
                q = q.sortby("lat").sel(lat=slice(lat0, lat1), lon=slice(lon0, lon1)).load()
                da = da.where(q <= prod.max_quality_level)
    v = da.values.astype("float32")
    if prod.conversion == "mm_per_hour_to_mm_per_month":
        if "hr" not in units:
            raise RuntimeError(f"{key} {ym}: unidades inesperadas '{units}' (se esperaba mm/hr)")
        v = v * 24 * per.days_in_month
    lo, hi = prod.valid_range
    v = np.where((v >= lo) & (v <= hi), v, np.nan).astype("float32")
    out = xr.DataArray(
        v[np.newaxis],
        coords={"time": [per.start_time], "lat": da.lat.values, "lon": da.lon.values},
        dims=("time", "lat", "lon"),
        name=key,
        attrs={
            "units": prod.units_target,
            "product": f"{prod.short_name} {prod.version}",
            "granule": path.name,
        },
    )
    D._atomic_to_netcdf(out, month_path(key, ym))


def fetch_product(key: str, workers: int = 2) -> dict:
    """Descarga los meses que falten del producto de la investigación `key`."""
    import earthaccess

    from mece.acquisition.auth import login

    cfg = research_config()
    prod = get_settings().products[cfg["products"][key]]
    end = cfg["period"]["end"]
    months = D.month_range(cfg["period"]["start"], end)
    todo = [m for m in months if not month_path(key, m).exists()]
    D.update_status(
        "research",
        key,
        {
            "state": "downloading" if todo else "ready",
            "total_months": len(months),
            "done_months": len(months) - len(todo),
        },
    )
    if not todo:
        return {"key": key, "downloaded": 0}
    login()
    granules = earthaccess.search_data(
        concept_id=prod.concept_id,
        granule_name=prod.granule_pattern,
        temporal=(f"{todo[0]}-01", pd.Period(todo[-1], "M").end_time.strftime("%Y-%m-%d")),
    )
    by_month: dict[str, object] = {}
    for g in granules:
        ym = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:7]
        if ym in todo:
            by_month.setdefault(ym, g)  # un granulo por mes (el catálogo trae duplicados)
    tmp_root = get_settings().data_dir / "tmp" / f"research_{key}"
    done = len(months) - len(todo)

    def work(ym, g):
        d = tmp_root / ym
        d.mkdir(parents=True, exist_ok=True)
        try:
            files = earthaccess.download([g], str(d), show_progress=False)
            if not files:
                raise RuntimeError(f"descarga vacía {key} {ym}")
            _crop_month(Path(files[0]), key, prod, ym)
        finally:
            for f in d.glob("*"):
                f.unlink(missing_ok=True)
            d.rmdir()

    errors = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, ym, g): ym for ym, g in sorted(by_month.items())}
        for fut in as_completed(futs):
            try:
                fut.result()
                done += 1
            except Exception as exc:  # noqa: BLE001
                errors.append((futs[fut], str(exc)[:200]))
                log.error("%s %s: %s", key, futs[fut], exc)
            if done % 6 == 0:
                D.update_status("research", key, {"done_months": done})
    D.update_status(
        "research",
        key,
        {"state": "ready" if not errors else "partial", "done_months": done, "errors": len(errors)},
    )
    return {"key": key, "downloaded": len(by_month) - len(errors), "errors": errors[:5]}


def chl_from_store() -> int:
    """Clorofila MODIS: se recorta del almacén 'gom' existente (sin descargar nada)."""
    from mece.catalog import CATALOG, load_stores

    cfg = research_config()
    lat0, lat1, lon0, lon1 = cfg["bbox_ocean"]
    spec, store = CATALOG["chl"], load_stores()["gom"]
    n = 0
    for ym in D.month_range(cfg["period"]["start"], cfg["period"]["end"]):
        dest = month_path("chl", ym)
        src = D.monthly_path(spec, store, ym)
        if dest.exists() or not src.exists():
            continue
        with D.NC_LOCK, xr.open_dataset(src) as ds:
            da = ds["chlor_a"].sel(lat=slice(lat0, lat1), lon=slice(lon0, lon1)).load()
        D._atomic_to_netcdf(da.rename("chl").astype("float32"), dest)
        n += 1
    D.update_status("research", "chl", {"state": "ready", "done_months": n})
    return n


def fetch_ancillary() -> dict:
    """Polígono del Golfo (GCOOS), cuencas HUC2 del Mississippi (USGS) e índice ONI (NOAA)."""
    cfg = research_config()["ancillary"]
    out = research_dir() / "ancillary"
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    for name, url in (
        ("gom_polygon.geojson", cfg["gom_polygon"]),
        ("mississippi_huc2.geojson", cfg["mississippi_huc2"]),
        ("oni.data", cfg["oni"]),
    ):
        dest = out / name
        if dest.exists() and dest.stat().st_size > 0 and name != "oni.data":
            res[name] = "existe"
            continue
        with urllib.request.urlopen(url, timeout=180) as r:
            content = r.read()
        if name.endswith(".geojson"):
            json.loads(content)  # valida
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(content)
        tmp.replace(dest)
        res[name] = f"{len(content) / 1e6:.1f} MB"
    return res


def fetch_all() -> list[dict]:
    out = [{"ancillary": fetch_ancillary()}, {"chl_from_store": chl_from_store()}]
    for key in ("sst", "flh", "viirs", "pp"):
        out.append(fetch_product(key))
    return out
