"""Adquisición de datos y caché en disco (contrato `fetch_dataset`, D14/D15).

Modelo de almacenamiento
------------------------
- **Almacenes regionales** (config/cases.yaml → stores): recortes locales de los
  productos globales. Se llenan una sola vez con el pipeline (`mece pipeline
  bootstrap`) y se actualizan de forma incremental.
- **Caché de consultas**: el resultado de cada `fetch_dataset` se guarda con la
  clave `(dataset_id, bbox_hash, t0, t1)`; la segunda llamada no descarga nada.

Backends
--------
- ``opendap``     SST MUR25: recorte en el servidor de NASA (Earthdata Cloud OPeNDAP),
                  un archivo diario de unos 40 KB; mensual = media de días.
- ``earthaccess`` Clorofila MODIS: descarga del archivo global mensual, recorte
                  para TODOS los almacenes y borrado del global.
- ``erddap``      Opcional (contrato original): griddap ya recortado por el servidor.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mece.catalog import CATALOG, BBox, DatasetSpec, Store, bbox_hash, store_for_bbox, validate_bbox
from mece.config import ROOT, get_settings

log = logging.getLogger(__name__)

ENCODING = {"zlib": True, "complevel": 4}

# netCDF4/HDF5 NO es seguro entre hilos: toda lectura/escritura NetCDF pasa por este
# candado. Las descargas HTTP sí corren en paralelo.
NC_LOCK = threading.RLock()


class RegionNotPrepared(RuntimeError):
    """El bbox pedido no cabe en ningún almacén regional."""


class DataUnavailable(RuntimeError):
    """No hay datos locales para el periodo pedido y no se permitió descargar."""


# ============================================================== utilidades
def month_range(t0: str, t1: str) -> list[str]:
    """Meses 'YYYY-MM' entre t0 y t1 inclusive (acepta 'YYYY-MM' o 'YYYY-MM-DD')."""
    p0, p1 = pd.Period(t0[:7], "M"), pd.Period(t1[:7], "M")
    if p0 > p1:
        raise ValueError(f"t0 ({t0}) es posterior a t1 ({t1})")
    return [str(p) for p in pd.period_range(p0, p1, freq="M")]


def data_root() -> Path:
    return get_settings().data_dir


def _resolve(p: Path) -> Path:
    return p if p.is_absolute() else (ROOT / p)


def _atomic_to_netcdf(ds: xr.Dataset | xr.DataArray, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    if isinstance(ds, xr.DataArray):
        ds = ds.to_dataset(name=ds.name or "value")
    enc = {v: ENCODING for v in ds.data_vars}
    with NC_LOCK:
        ds.to_netcdf(tmp, encoding=enc)
    tmp.replace(dest)


# ======================================================== estado (status.json)
_STATUS_LOCK = threading.Lock()


def status_path() -> Path:
    return data_root() / "status.json"


def read_status() -> dict:
    try:
        return json.loads(status_path().read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def update_status(section: str, key: str, info: dict) -> None:
    """Actualiza status.json de forma atómica (lo lee el dashboard).

    Varios procesos (descargas, precálculo, worker) escriben a la vez: se serializan
    con un candado de archivo (fcntl) y cada proceso usa su propio temporal.
    """
    import fcntl

    p = status_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with _STATUS_LOCK, open(p.with_suffix(".lock"), "w") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)
        st = read_status()
        st.setdefault(section, {}).setdefault(key, {}).update(
            info | {"updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        )
        tmp = p.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(st, indent=1, ensure_ascii=False))
        tmp.replace(p)


# ================================================================ rutas
def monthly_path(spec: DatasetSpec, store: Store, ym: str) -> Path:
    """Archivo mensual listo para análisis de un almacén."""
    yyyymm = ym.replace("-", "")
    if spec.backend == "opendap":  # mensual = agregado propio de los diarios
        return (
            data_root() / "processed" / spec.variable / spec.product_key / store.id / f"{yyyymm}.nc"
        )
    return data_root() / "raw" / spec.variable / spec.product_key / store.id / f"{yyyymm}.nc"


def daily_path(spec: DatasetSpec, store: Store, day: date) -> Path:
    return (
        data_root()
        / "raw"
        / spec.variable
        / spec.product_key
        / store.id
        / "daily"
        / f"{day:%Y}"
        / f"{day:%Y%m%d}.nc"
    )


# ====================================================== sesión Earthdata
_tls = threading.local()


def _session():
    """Sesión HTTP autenticada con Earthdata (una por hilo)."""
    if getattr(_tls, "session", None) is None:
        import earthaccess

        from mece.acquisition.auth import login

        login()
        _tls.session = earthaccess.get_requests_https_session()
    return _tls.session


def _get_with_retry(url: str, params: dict | None = None, tries: int = 5, timeout: int = 120):
    """GET con reintentos exponenciales ante 429/5xx/errores de red. 404 → None."""
    import requests

    for attempt in range(tries):
        try:
            r = _session().get(url, params=params, timeout=timeout)
        except requests.RequestException as exc:
            wait = 2**attempt
            log.warning("red: %s (reintento en %ss)", exc.__class__.__name__, wait)
            time.sleep(wait)
            continue
        if r.status_code == 200:
            return r
        if r.status_code == 404:
            return None
        if r.status_code in (429, 500, 502, 503, 504):
            wait = 2 ** (attempt + 1)
            log.warning("HTTP %s en %s (reintento en %ss)", r.status_code, url[-60:], wait)
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code} en {url}: {r.text[:200]}")
    raise RuntimeError(f"Sin respuesta tras {tries} intentos: {url}")


# ============================================ backend OPeNDAP · MUR25 diario
MUR25_CONCEPT = "C2036880657-POCLOUD"
MUR25_LAT0, MUR25_LON0, MUR25_RES = -89.875, -179.875, 0.25
MUR25_NLAT, MUR25_NLON = 720, 1440


def _mur25_indices(bbox: BBox) -> tuple[int, int, int, int]:
    lat0, lat1, lon0, lon1 = bbox
    i0 = max(0, int(np.floor((lat0 - MUR25_LAT0) / MUR25_RES)))
    i1 = min(MUR25_NLAT - 1, int(np.ceil((lat1 - MUR25_LAT0) / MUR25_RES)))
    j0 = max(0, int(np.floor((lon0 - MUR25_LON0) / MUR25_RES)))
    j1 = min(MUR25_NLON - 1, int(np.ceil((lon1 - MUR25_LON0) / MUR25_RES)))
    return i0, i1, j0, j1


def _mur25_fetch_day(store: Store, day: date, spec: DatasetSpec) -> bool:
    """Descarga el recorte diario de MUR25 para un almacén. True si hay dato."""
    dest = daily_path(spec, store, day)
    if dest.exists():
        return True
    gran = f"{day:%Y%m%d}090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2"
    url = f"https://opendap.earthdata.nasa.gov/collections/{MUR25_CONCEPT}/granules/{gran}.dap.nc4"
    i0, i1, j0, j1 = _mur25_indices(store.bbox)
    ce = f"/analysed_sst[0:1:0][{i0}:1:{i1}][{j0}:1:{j1}];/lat[{i0}:1:{i1}];/lon[{j0}:1:{j1}];/time"
    r = _get_with_retry(url, params={"dap4.ce": ce})
    if r is None:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.name}.{threading.get_ident()}.tmp")
    tmp.write_bytes(r.content)
    # validación mínima: se abre y tiene la variable esperada
    with NC_LOCK, xr.open_dataset(tmp) as ds:
        ok = "analysed_sst" in ds
    if not ok:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Respuesta OPeNDAP sin analysed_sst para {day}")
    tmp.replace(dest)
    return True


def _mur25_build_month(store: Store, ym: str, spec: DatasetSpec, min_days: int = 20) -> bool:
    """Media mensual (°C) a partir de los diarios del almacén."""
    per = pd.Period(ym, "M")
    days = [d.date() for d in pd.date_range(per.start_time, per.end_time, freq="D")]
    files = [daily_path(spec, store, d) for d in days if daily_path(spec, store, d).exists()]
    if len(files) < min_days:
        log.warning("MUR25 %s %s: solo %d días; mes incompleto", store.id, ym, len(files))
        return False
    arrs = []
    for f in files:
        with NC_LOCK, xr.open_dataset(f) as ds:
            arrs.append(ds["analysed_sst"].isel(time=0, drop=True).load())
    sst = xr.concat(arrs, dim="day").mean("day", skipna=True) - 273.15
    sst = sst.where((sst > -2) & (sst < 40))
    out = sst.expand_dims(time=[per.start_time]).rename("sst")
    out.attrs = {
        "units": "degC",
        "long_name": "Media mensual de SST de fundación (GHRSST MUR25 v4.2)",
        "n_days": len(files),
        "source": "NASA PO.DAAC · MUR25-JPL-L4-GLOB-v04.2 · OPeNDAP",
        "doi": "10.5067/GHM25-4FJ42",
    }
    _atomic_to_netcdf(out, monthly_path(spec, store, ym))
    return True


def ensure_mur25(stores: Iterable[Store], months: list[str], workers: int = 4) -> dict:
    """Garantiza los meses de MUR25 en los almacenes (descarga solo lo que falta)."""
    spec = CATALOG["sst"]
    stores = list(stores)
    today = date.today()
    todo_months = [m for m in months if any(not monthly_path(spec, s, m).exists() for s in stores)]
    days = []
    for m in todo_months:
        per = pd.Period(m, "M")
        for d in pd.date_range(per.start_time, per.end_time, freq="D"):
            if d.date() < today - timedelta(days=1):
                days.extend(
                    (s, d.date()) for s in stores if not daily_path(spec, s, d.date()).exists()
                )
    total, done, missing = len(days), 0, 0
    log.info(
        "MUR25: %d meses por construir, %d recortes diarios por descargar", len(todo_months), total
    )
    for s in stores:
        update_status("sst", s.id, {"state": "downloading", "total_days": total, "done_days": 0})
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_mur25_fetch_day, s, d, spec): (s, d) for s, d in days}
        for fut in as_completed(futs):
            done += 1
            try:
                if not fut.result():
                    missing += 1
            except Exception as exc:  # noqa: BLE001
                missing += 1
                log.error("MUR25 %s: %s", futs[fut], exc)
            if done % 200 == 0 or done == total:
                for s in stores:
                    update_status("sst", s.id, {"done_days": done, "missing_days": missing})
    built = 0
    for m in todo_months:
        for s in stores:
            if not monthly_path(spec, s, m).exists() and _mur25_build_month(s, m, spec):
                built += 1
    for s in stores:
        _record_store_status("sst", s)
    return {"days_downloaded": total - missing, "days_missing": missing, "months_built": built}


# ===================================== backend earthaccess · clorofila MODIS
def _crop_global_to_stores(path: Path, spec: DatasetSpec, stores: list[Store], ym: str) -> None:
    from mece.config import get_settings

    prod = get_settings().products[spec.product_key]
    lo, hi = prod.valid_range
    subs = {}
    with NC_LOCK, xr.open_dataset(path) as ds:
        da = ds[spec.var_name]
        for st in stores:
            lat0, lat1, lon0, lon1 = st.bbox
            lat_sl = slice(lat1, lat0) if spec.lat_descending else slice(lat0, lat1)
            subs[st.id] = da.sel(lat=lat_sl, lon=slice(lon0, lon1)).load()
    for st in stores:
        sub = subs[st.id]
        sub = sub.where((sub >= lo) & (sub <= hi)).sortby("lat")
        out = sub.expand_dims(time=[pd.Period(ym, "M").start_time]).rename("chlor_a")
        out.attrs = {
            "units": "mg m-3",
            "long_name": "Clorofila-a (OCI) · MODIS-Aqua L3m mensual 4 km",
            "source": f"NASA OB.DAAC · {prod.short_name} {prod.version}",
            "doi": prod.doi or "",
            "granule": path.name,
        }
        _atomic_to_netcdf(out, monthly_path(spec, st, ym))


def ensure_modis_chl(stores: Iterable[Store], months: list[str], workers: int = 2) -> dict:
    """Descarga los meses que falten, recorta para todos los almacenes y borra el global."""
    import earthaccess

    from mece.acquisition.auth import login

    spec = CATALOG["chl"]
    prod = get_settings().products[spec.product_key]
    stores = list(stores)
    todo = [m for m in months if any(not monthly_path(spec, s, m).exists() for s in stores)]
    if not todo:
        for s in stores:
            _record_store_status("chl", s)
        return {"months_downloaded": 0}
    login()
    granules = earthaccess.search_data(
        concept_id=prod.concept_id,
        granule_name=prod.granule_pattern,
        temporal=(f"{todo[0]}-01", pd.Period(todo[-1], "M").end_time.strftime("%Y-%m-%d")),
    )
    by_month = {}
    for g in granules:
        ym = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:7]
        if ym in todo:
            by_month[ym] = g
    tmp_root = data_root() / "tmp" / "chl_global"
    total, done = len(by_month), 0
    for s in stores:
        update_status(
            "chl", s.id, {"state": "downloading", "total_months": total, "done_months": 0}
        )

    def work(ym, g):
        d = tmp_root / ym
        d.mkdir(parents=True, exist_ok=True)
        try:
            files = earthaccess.download([g], str(d), show_progress=False)
            if not files:
                raise RuntimeError(f"descarga vacía para {ym}")
            _crop_global_to_stores(Path(files[0]), spec, stores, ym)
        finally:
            for f in d.glob("*"):
                f.unlink(missing_ok=True)
            d.rmdir()
        return ym

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, ym, g) for ym, g in sorted(by_month.items())]
        for fut in as_completed(futs):
            done += 1
            try:
                fut.result()
            except Exception as exc:  # noqa: BLE001
                log.error("clorofila: %s", exc)
            if done % 5 == 0 or done == total:
                for s in stores:
                    update_status("chl", s.id, {"done_months": done})
    for s in stores:
        _record_store_status("chl", s)
    return {"months_downloaded": done}


def _record_store_status(dataset_id: str, store: Store) -> None:
    spec = CATALOG[dataset_id]
    folder = monthly_path(spec, store, "2000-01").parent
    months = sorted(p.stem for p in folder.glob("*.nc")) if folder.exists() else []
    info = {"state": "ready" if months else "empty", "n_months": len(months)}
    if months:
        info |= {
            "first_month": f"{months[0][:4]}-{months[0][4:]}",
            "last_month": f"{months[-1][:4]}-{months[-1][4:]}",
        }
    update_status(dataset_id, store.id, info)


# ======================================================== backend ERDDAP
def build_griddap_url(spec: DatasetSpec, bbox: BBox, t0: str, t1: str) -> str:
    """URL griddap con el recorte hecho en el servidor (contrato original)."""
    if not (spec.erddap_id and spec.server_url):
        raise ValueError(f"{spec.var_name}: sin erddap_id/server_url")
    lat0, lat1, lon0, lon1 = bbox
    la, lb = (lat1, lat0) if spec.lat_descending else (lat0, lat1)
    t0s = f"{t0[:7]}-01T00:00:00Z" if len(t0) == 7 else f"{t0}T00:00:00Z"
    t1s = f"{t1[:7]}-28T00:00:00Z" if len(t1) == 7 else f"{t1}T00:00:00Z"
    var = "chlorophyll" if spec.erddap_id.startswith("erdMH1chla") else "sst"
    return (
        f"{spec.server_url}/griddap/{spec.erddap_id}.nc?"
        f"{var}[({t0s}):1:({t1s})][({la}):1:({lb})][({lon0}):1:({lon1})]"
    )


def _fetch_erddap(spec: DatasetSpec, bbox: BBox, t0: str, t1: str, dest: Path) -> Path:
    import requests

    url = build_griddap_url(spec, bbox, t0, t1)
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    return dest


# ============================================================ contrato
def fetch_dataset(
    dataset_id: str,
    bbox: tuple[float, float, float, float],
    t0: str,
    t1: str,
    cache_dir: Path = Path("data/raw"),
    download_missing: bool = True,
) -> xr.DataArray:
    """Devuelve la variable recortada a `bbox` entre t0 y t1, dims (time, lat, lon).

    bbox = (lat_min, lat_max, lon_min, lon_max). La latitud sale siempre ascendente,
    sin importar el orden del producto (DatasetSpec.lat_descending). Si la consulta ya
    está en caché, no descarga nada; si faltan meses en el almacén y
    `download_missing`, los descarga primero.
    """
    if dataset_id not in CATALOG:
        raise KeyError(f"dataset '{dataset_id}' no está en CATALOG ({list(CATALOG)})")
    spec = CATALOG[dataset_id]
    bbox = validate_bbox(bbox)
    months = month_range(t0, t1)
    _resolve(cache_dir)  # se respeta el parámetro del contrato; los almacenes viven en data/
    cache_file = (
        data_root()
        / "cache"
        / "fetch"
        / f"{dataset_id}_{bbox_hash(bbox)}_{months[0]}_{months[-1]}.nc"
    )
    if cache_file.exists():
        with NC_LOCK, xr.open_dataarray(cache_file) as da:
            return da.load()

    if spec.backend == "erddap":
        raw = _fetch_erddap(spec, bbox, t0, t1, cache_file.with_suffix(".erddap.nc"))
        with xr.open_dataset(raw) as ds:
            da = ds[list(ds.data_vars)[0]].load()
        da = da.rename({"latitude": "lat", "longitude": "lon"}).sortby("lat")
        _atomic_to_netcdf(da, cache_file)
        return da

    store = store_for_bbox(bbox)
    if store is None:
        raise RegionNotPrepared(
            f"El bbox {bbox} no cabe en ningún almacén de config/cases.yaml. "
            "Agrega un almacén que lo contenga y ejecuta `mece pipeline bootstrap`."
        )
    missing = [m for m in months if not monthly_path(spec, store, m).exists()]
    if missing and download_missing:
        if spec.backend == "opendap":
            ensure_mur25([store], missing)
        else:
            ensure_modis_chl([store], missing)
        missing = [m for m in months if not monthly_path(spec, store, m).exists()]
    files = [monthly_path(spec, store, m) for m in months if monthly_path(spec, store, m).exists()]
    if not files:
        raise DataUnavailable(
            f"Sin datos locales de '{dataset_id}' para {months[0]}…{months[-1]} en el almacén "
            f"'{store.id}'. El pipeline los está preparando o no se permitió descargar."
        )
    lat0, lat1, lon0, lon1 = bbox
    parts = []
    for f in files:
        with NC_LOCK, xr.open_dataset(f) as ds:
            v = ds[list(ds.data_vars)[0]]
            parts.append(v.sel(lat=slice(lat0, lat1), lon=slice(lon0, lon1)).load())
    da = xr.concat(parts, dim="time").sortby("time").sortby("lat")
    da.name = dataset_id
    da.attrs = {
        "units": spec.units,
        "dataset_id": dataset_id,
        "label": spec.label_es,
        "source": spec.source_es,
        "log_transform": int(spec.log_transform),
        "bbox": list(bbox),
        "months_missing": len(missing),
    }
    if not missing:  # solo se cachea una consulta completa
        _atomic_to_netcdf(da, cache_file)
    return da


__all__ = [
    "fetch_dataset",
    "ensure_mur25",
    "ensure_modis_chl",
    "build_griddap_url",
    "month_range",
    "read_status",
    "RegionNotPrepared",
    "DataUnavailable",
]
