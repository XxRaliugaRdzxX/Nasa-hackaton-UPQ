"""Construcción reproducible de los polígonos de regiones de estudio.

Cada región es un par marino/terrestre (ver config/regions.yaml):
  - marino  → donde se promedian clorofila y SST
  - terrestre → cuenca aportante donde se promedia la precipitación (y GLDAS)

Fuentes públicas (se descargan a data/raw/ancillary/, que no se versiona):
  - Marine Regions · IHO Sea Areas "Gulf of Mexico" (CC-BY 4.0, VLIZ)
  - Natural Earth 10 m · tierra y estados (dominio público)
  - HydroSHEDS · HydroBASINS v1c, Norteamérica, nivel 6 (ver hydrosheds.org/terms)

Salida: un GeoJSON por polígono en data/spatial/regions/ (EPSG:4326) con sus
metadatos, más una figura de control en docs/figuras/regiones_control.png.

Uso:  mece regions build            (descarga fuentes si faltan)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import Point, box
from shapely.ops import unary_union

from mece.config import Settings

log = logging.getLogger(__name__)

SOURCES: dict[str, dict[str, str]] = {
    "iho": {
        "url": (
            "https://geo.vliz.be/geoserver/MarineRegions/wfs?service=WFS&version=1.0.0"
            "&request=GetFeature&typeName=MarineRegions:iho&outputFormat=application/json"
            "&CQL_FILTER=name=%27Gulf%20of%20Mexico%27"
        ),
        "file": "marine_regions/iho_gulf_of_mexico.geojson",
        "citation": "Flanders Marine Institute (2018). IHO Sea Areas v3. marineregions.org",
        "license": "CC-BY 4.0",
    },
    "land": {
        "url": "https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip",
        "file": "natural_earth/ne_10m_land.zip",
        "citation": "Natural Earth 10m land",
        "license": "Public domain",
    },
    "admin1": {
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip",
        "file": "natural_earth/ne_10m_admin_1_states_provinces.zip",
        "citation": "Natural Earth 10m admin-1 states/provinces",
        "license": "Public domain",
    },
    "hybas6": {
        "url": "https://data.hydrosheds.org/file/HydroBASINS/standard/hybas_na_lev06_v1c.zip",
        "file": "hydrobasins/hybas_na_lev06_v1c.zip",
        "citation": "Lehner & Grill (2013), Hydrol. Process. 27(15). HydroBASINS v1c",
        "license": "HydroSHEDS license (hydrosheds.org/terms)",
    },
}

WGS84 = "EPSG:4326"


# ------------------------------------------------------------------ descargas
def download_sources(ancillary_dir: Path, force: bool = False) -> None:
    """Descarga las fuentes que falten. Escribe a .part y renombra al terminar."""
    for key, src in SOURCES.items():
        dest = ancillary_dir / src["file"]
        if dest.exists() and dest.stat().st_size > 0 and not force:
            log.info("fuente %s ya existe: %s", key, dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        log.info("descargando %s …", key)
        try:
            with requests.get(src["url"], stream=True, timeout=300) as r:
                r.raise_for_status()
                with tmp.open("wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
        except requests.RequestException as exc:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"No se pudo descargar la fuente '{key}' ({src['url']}): {exc}"
            ) from exc
        tmp.replace(dest)


def _read(
    ancillary_dir: Path,
    key: str,
    bbox: tuple[float, float, float, float] | None = None,
    where: str | None = None,
    columns: list[str] | None = None,
) -> gpd.GeoDataFrame:
    """Lee una fuente filtrando ya en disco (bbox/where/columns) para ahorrar memoria."""
    path = ancillary_dir / SOURCES[key]["file"]
    if not path.exists():
        raise FileNotFoundError(f"Falta la fuente '{key}' en {path}. Ejecuta: mece regions build")
    uri = f"zip://{path}" if path.suffix == ".zip" else str(path)
    gdf = gpd.read_file(uri, bbox=bbox, where=where, columns=columns)
    if gdf.crs is None:
        return gdf.set_crs(WGS84)
    return gdf if gdf.crs.to_epsg() == 4326 else gdf.to_crs(WGS84)


# ---------------------------------------------------------------- construcción
def _log_step(msg: str) -> None:
    """Registra el paso y la memoria máxima usada (útil en el servidor compartido)."""
    import resource

    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    log.info("%-45s RSS máx %6.0f MB", msg, rss_mb)


def _raster_grid(geom_m, pad_m: float, res_m: float):
    """Malla regular (transform, shape) que cubre `geom_m` con un margen `pad_m`."""
    import numpy as np
    from rasterio.transform import from_origin

    minx, miny, maxx, maxy = geom_m.bounds
    minx, miny, maxx, maxy = minx - pad_m, miny - pad_m, maxx + pad_m, maxy + pad_m
    shape_ = (int(np.ceil((maxy - miny) / res_m)), int(np.ceil((maxx - minx) / res_m)))
    return from_origin(minx, maxy, res_m, res_m), shape_


def _burn(geom_m, transform, shape_):
    from rasterio.features import rasterize

    return rasterize(
        [geom_m], out_shape=shape_, transform=transform, fill=0, default_value=1, dtype="uint8"
    ).astype(bool)


def _polygonize(mask, transform):
    from rasterio.features import shapes
    from shapely.geometry import shape

    polys = [
        shape(g) for g, v in shapes(mask.astype("uint8"), mask=mask, transform=transform) if v == 1
    ]
    return unary_union(polys)


def _clean(geom, min_part_m2: float = 1e4):
    """Geometría válida y solo poligonal; descarta piezas menores a `min_part_m2`."""
    import shapely

    geom = shapely.make_valid(geom)
    stack, polys = [geom], []
    while stack:
        g = stack.pop()
        if g.geom_type == "Polygon":
            if g.area >= min_part_m2:
                polys.append(g)
        elif hasattr(g, "geoms"):
            stack.extend(g.geoms)
    return unary_union(polys)


def _largest_part(geom):
    """Conserva solo el cuerpo de agua principal (descarta lagunas o trozos sueltos)."""
    if geom.geom_type == "MultiPolygon":
        return max(geom.geoms, key=lambda g: g.area)
    return geom


def _open_water(geom, width_m: float = 2_000.0):
    """Apertura morfológica: corta conexiones de agua más angostas que `2·width_m`
    (bocas de lagunas costeras) y conserva el cuerpo de agua principal."""
    return _largest_part(geom.buffer(-width_m).buffer(width_m).intersection(geom))


def _far_from_land(land_m, region_m, min_dist_m: float, res_m: float = 1_000.0):
    """Parte de `region_m` a más de `min_dist_m` de la tierra (CRS métrico).

    Se calcula con un raster de distancia y no con un búfer vectorial: el búfer
    de 100 km sobre la costa continental a escala 1:10 m exige más de 1 GB de
    RAM; el raster de 1 km usa ~50 MB y su error (≤ 1 km) es despreciable frente
    a los píxeles de datos (4-25 km).
    """
    from scipy.ndimage import distance_transform_edt

    transform, shape_ = _raster_grid(region_m, min_dist_m + 5 * res_m, res_m)
    land = _burn(land_m, transform, shape_)
    far = distance_transform_edt(~land) * res_m > min_dist_m
    return _polygonize(far, transform).intersection(region_m)


def _coastal_strip(land_m, own_m, sea_m, width_m: float, res_m: float = 1_000.0):
    """Mar a ≤ `width_m` de la costa de `own_m` y más cerca de ella que de otra costa.

    Cada píxel de mar se asigna a la costa más cercana (límites laterales por
    equidistancia), así la franja no invade aguas frente a estados vecinos.
    """
    from scipy.ndimage import distance_transform_edt

    transform, shape_ = _raster_grid(own_m, width_m + 20 * res_m, res_m)
    land = _burn(land_m, transform, shape_)
    own = land & _burn(own_m, transform, shape_)
    other = land & ~own
    d_own = distance_transform_edt(~own) * res_m
    d_other = distance_transform_edt(~other) * res_m
    strip = ~land & (d_own <= width_m) & (d_own <= d_other)
    return _largest_part(_polygonize(strip, transform).intersection(sea_m))


def _outlets_draining_to(
    basins: gpd.GeoDataFrame,
    crs: str,
    land_m,
    target_sea_m,
    min_frac: float,
    reference_sea_m=None,
    ring_m: float = 3_000.0,
) -> list[int]:
    """MAIN_BAS de las cuencas cuya desembocadura vierte en `target_sea_m`.

    Para cada sub-cuenca de salida se toma un anillo de `ring_m` a su alrededor; su
    parte no terrestre es el "contacto con el agua". Se acepta la cuenca si al menos
    `min_frac` de ese contacto cae en `target_sea_m`. Si se da `reference_sea_m`, la
    fracción se mide solo sobre el contacto con ese mar: así no cuenta el agua de
    estuarios anchos (p. ej. la boca del Grijalva), que Natural Earth no marca como tierra.
    """
    from shapely import clip_by_rect

    window = box(*land_m.bounds)
    outlets = basins[(basins["NEXT_DOWN"] == 0) & (basins["ENDO"] == 0)].to_crs(crs)
    outlets = outlets[outlets.intersects(window)]
    ids: list[int] = []
    for main_bas, geom in zip(outlets["MAIN_BAS"], outlets.geometry.simplify(200), strict=True):
        ring = geom.buffer(ring_m).difference(geom)
        sea = ring.difference(clip_by_rect(land_m, *ring.bounds))
        if reference_sea_m is not None:
            sea = sea.intersection(reference_sea_m)
        if sea.area < 1e6:  # < 1 km² de contacto: no vierte a este mar
            continue
        if sea.intersection(target_sea_m).area / sea.area >= min_frac:
            ids.append(int(main_bas))
    return sorted(set(ids))


def build_regions(settings: Settings) -> dict[str, gpd.GeoDataFrame]:
    """Construye todos los polígonos y devuelve {nombre_archivo: GeoDataFrame}."""
    b = settings.region_build
    crs = b.metric_crs
    anc = settings.ancillary_dir
    bbox = settings.region_bbox

    # --- fuentes, leídas solo en la ventana necesaria (memoria acotada)
    # Ventana marina: el Golfo con 3° de margen. Ventana de cuencas: todo lo que drena al Golfo.
    gulf_win = (bbox.lon_min - 3, bbox.lat_min - 3, bbox.lon_max + 3, bbox.lat_max + 3)
    basin_win = (-120.0, 13.0, -74.0, 56.0)
    hb_cols = ["HYBAS_ID", "NEXT_DOWN", "MAIN_BAS", "ENDO"]

    iho = _read(anc, "iho")
    land = _read(anc, "land", bbox=gulf_win)
    admin1 = _read(
        anc, "admin1", bbox=gulf_win, where="admin = 'Mexico'", columns=["name", "admin"]
    )
    # HydroBASINS trae índices .sbn de ArcGIS que GDAL no lee bien con filtro bbox:
    # se lee completo (archivo pequeño) y se recorta en memoria con .cx
    h6 = _read(anc, "hybas6", columns=hb_cols).cx[
        basin_win[0] : basin_win[2], basin_win[1] : basin_win[3]
    ]

    land_m = unary_union(land.to_crs(crs).geometry.values)
    iho_m = unary_union(iho.to_crs(crs).geometry.values)
    del land
    _log_step("fuentes leídas")

    # --- marinas
    gom_all_m = iho_m.difference(land_m)  # Golfo sin tierra (incluye lagunas conectadas)
    gom_m = _largest_part(gom_all_m)  # cuerpo de agua principal
    _log_step("Golfo marino")
    offshore_m = _largest_part(_far_from_land(land_m, gom_m, b.offshore_buffer_km * 1e3))
    _log_step("Golfo oceánico (> 100 km)")

    tab = admin1[admin1["name"] == "Tabasco"]
    if tab.empty:
        raise RuntimeError("No se encontró Tabasco en Natural Earth admin-1")
    tab_m = unary_union(tab.to_crs(crs).geometry.values)
    tabasco_marine_m = _coastal_strip(land_m, tab_m, gom_m, b.tabasco_strip_km * 1e3)

    center = gpd.GeoSeries([Point(b.plume_center["lon"], b.plume_center["lat"])], crs=WGS84).to_crs(
        crs
    )[0]
    plume_m = _open_water(center.buffer(b.plume_radius_km * 1e3).intersection(gom_m))
    _log_step("Tabasco y pluma")

    # --- terrestres: se les quita cualquier parte que caiga en el Golfo (sin solape tierra/mar)
    gu = h6[h6["MAIN_BAS"].astype(int) == b.gu_main_basin_id]
    if gu.empty:
        raise RuntimeError(f"MAIN_BAS {b.gu_main_basin_id} no existe en HydroBASINS nivel 6")
    gu_m = unary_union(gu.to_crs(crs).geometry.values).difference(gom_all_m)
    _log_step("cuenca Grijalva-Usumacinta")

    tab_ids = _outlets_draining_to(
        h6, crs, land_m, tabasco_marine_m, b.tabasco_outlet_min_frac, reference_sea_m=gom_all_m
    )
    if b.gu_main_basin_id not in tab_ids:
        raise RuntimeError("La cuenca Grijalva-Usumacinta debería desembocar frente a Tabasco")
    tab_basins_m = unary_union(
        h6[h6["MAIN_BAS"].astype(int).isin(tab_ids)].to_crs(crs).geometry.values
    ).difference(gom_all_m)
    _log_step("cuencas con desembocadura en Tabasco")

    gom_ids = _outlets_draining_to(h6, crs, land_m, gom_all_m, b.gom_outlet_min_frac)
    # Las cuencas continentales tienen mucho detalle; se simplifican a la resolución final
    # antes de unirlas (misma tolerancia que se aplica al guardar).
    gom_basins_m = unary_union(
        h6[h6["MAIN_BAS"].astype(int).isin(gom_ids)]
        .to_crs(crs)
        .geometry.simplify(b.simplify_m)
        .values
    ).difference(gom_all_m)
    _log_step("cuencas que drenan al Golfo")
    del h6, land_m

    # --- geometría final: primero se simplifica el mar; después la tierra se simplifica y
    # se recorta contra el mar ya simplificado, para no dejar franjas de solape en la costa
    def simp(g):
        return _clean(g.simplify(b.simplify_m, preserve_topology=True))

    gom_m, offshore_m, tabasco_marine_m, plume_m = (
        simp(g) for g in (gom_m, offshore_m, tabasco_marine_m, plume_m)
    )
    sea_final = unary_union([gom_m, offshore_m, tabasco_marine_m, plume_m])
    gu_m, tab_basins_m, gom_basins_m = (
        _clean(simp(g).difference(sea_final)) for g in (gu_m, tab_basins_m, gom_basins_m)
    )
    _log_step("geometrías finales limpias")

    # --- empaquetado con metadatos
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    src_cite = {k: f"{v['citation']} [{v['license']}]" for k, v in SOURCES.items()}

    def pack(
        region_id: str, part: str, geom_m, method: str, sources: list[str]
    ) -> gpd.GeoDataFrame:
        if geom_m.is_empty:
            raise RuntimeError(
                f"La geometría {region_id}/{part} quedó vacía; revisa los parámetros"
            )
        reg = settings.regions[region_id]
        gdf = gpd.GeoDataFrame(
            {
                "region_id": [region_id],
                "part": [part],
                "name_es": [reg.name_es],
                "name_en": [reg.name_en],
                "area_km2": [round(geom_m.area / 1e6, 1)],
                "method": [method],
                "sources": ["; ".join(src_cite[s] for s in sources)],
                "created": [now],
            },
            geometry=[geom_m],
            crs=crs,
        ).to_crs(WGS84)
        # Se redondea a 1e-5° (~1 m), la precisión con la que se escribe el GeoJSON, y se
        # vuelve a validar: así el archivo guardado es exactamente una geometría válida.
        gdf["geometry"] = gdf.geometry.set_precision(1e-5).apply(lambda g: _clean(g, 0.0))
        return gdf

    out = {
        "gom_marine.geojson": pack(
            "gom",
            "marine",
            gom_m,
            "Polígono IHO 'Gulf of Mexico' menos tierra (NE 10m)",
            ["iho", "land"],
        ),
        "gom_basins_land.geojson": pack(
            "gom",
            "land",
            gom_basins_m,
            f"HydroBASINS lev06: {len(gom_ids)} cuencas con >= {b.gom_outlet_min_frac:.0%} "
            "del contacto de su desembocadura en el Golfo; sin solape con el Golfo",
            ["hybas6", "iho", "land"],
        ),
        "gom_offshore_marine.geojson": pack(
            "gom_offshore",
            "marine",
            offshore_m,
            f"Golfo IHO a más de {b.offshore_buffer_km:g} km de la costa",
            ["iho", "land"],
        ),
        "tabasco_coast_marine.geojson": pack(
            "tabasco_coast",
            "marine",
            tabasco_marine_m,
            f"Mar a <= {b.tabasco_strip_km:g} km de la costa de Tabasco y más cerca de ella que "
            "de otra costa (raster de distancia 1 km), dentro del Golfo IHO",
            ["admin1", "land", "iho"],
        ),
        "tabasco_basins_land.geojson": pack(
            "tabasco_coast",
            "land",
            tab_basins_m,
            f"HydroBASINS lev06: {len(tab_ids)} cuencas con >= {b.tabasco_outlet_min_frac:.0%} "
            "del contacto marino de su desembocadura frente a Tabasco "
            f"(MAIN_BAS {tab_ids}); sin solape con el Golfo",
            ["hybas6", "admin1", "land"],
        ),
        "gu_plume_marine.geojson": pack(
            "grijalva_usumacinta",
            "marine",
            plume_m,
            f"Radio de {b.plume_radius_km:g} km alrededor de ({b.plume_center['lat']}, "
            f"{b.plume_center['lon']}), dentro del Golfo IHO. Definición operativa a validar",
            ["iho", "land"],
        ),
        "gu_basin_land.geojson": pack(
            "grijalva_usumacinta",
            "land",
            gu_m,
            f"HydroBASINS lev06 MAIN_BAS {b.gu_main_basin_id} (México + Guatemala); "
            "sin solape con el Golfo",
            ["hybas6", "land"],
        ),
    }
    return out


def write_regions(regions: dict[str, gpd.GeoDataFrame], out_dir: Path) -> list[Path]:
    """Escribe cada GeoJSON de forma atómica (tmp + rename)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, gdf in regions.items():
        dest = out_dir / name
        tmp = dest.with_suffix(".tmp.geojson")
        gdf.to_file(tmp, driver="GeoJSON", COORDINATE_PRECISION=5)
        tmp.replace(dest)
        paths.append(dest)
    return paths


def summary_table(regions: dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    rows = [
        gdf.drop(columns="geometry").iloc[0].to_dict() | {"file": n} for n, gdf in regions.items()
    ]
    return pd.DataFrame(rows)[["file", "region_id", "part", "area_km2", "method"]]


def plot_control(regions: dict[str, gpd.GeoDataFrame], settings: Settings, dest: Path) -> Path:
    """Figura de control para que el equipo revise visualmente los polígonos."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    land = _read(settings.ancillary_dir, "land", bbox=(-115.0, 12.0, -70.0, 52.0))
    fig, axes = plt.subplots(1, 2, figsize=(15, 7.5), dpi=130)

    # Panel 1: Golfo completo
    ax = axes[0]
    land.plot(ax=ax, color="#e8e4da", edgecolor="#9a9486", linewidth=0.3)
    regions["gom_basins_land.geojson"].plot(
        ax=ax, color="#c9b88a", alpha=0.55, label="Cuencas al Golfo"
    )
    regions["gom_marine.geojson"].plot(ax=ax, color="#9cc9e6", edgecolor="#0b2545", linewidth=0.6)
    regions["gom_offshore_marine.geojson"].plot(ax=ax, color="#3d7fb5", alpha=0.6)
    regions["tabasco_coast_marine.geojson"].plot(ax=ax, color="#13a89e")
    ax.set_xlim(-112, -76)
    ax.set_ylim(14, 50)
    ax.set_title(
        "Golfo de México: marino (azul), oceánico >100 km (azul oscuro),\ncuencas aportantes (ocre)"
    )

    # Panel 2: Tabasco y Grijalva-Usumacinta
    ax = axes[1]
    land.plot(ax=ax, color="#e8e4da", edgecolor="#9a9486", linewidth=0.4)
    regions["tabasco_basins_land.geojson"].plot(ax=ax, color="#d9c27e", alpha=0.6)
    regions["gu_basin_land.geojson"].plot(
        ax=ax, facecolor="none", edgecolor="#8a5a00", linewidth=1.2, hatch="//"
    )
    regions["tabasco_coast_marine.geojson"].plot(ax=ax, color="#13a89e", alpha=0.75)
    regions["gu_plume_marine.geojson"].plot(
        ax=ax, facecolor="none", edgecolor="#c0392b", linewidth=1.6
    )
    b = settings.region_build
    ax.plot(b.plume_center["lon"], b.plume_center["lat"], "o", color="#c0392b", ms=4)
    ax.set_xlim(-95.5, -88.5)
    ax.set_ylim(14.5, 21.0)
    ax.set_title(
        "Tabasco: franja marina 0-50 km (turquesa), pluma 60 km (rojo),\n"
        "cuencas con desembocadura en Tabasco (ocre), cuenca G-U (rayado)"
    )
    for ax in axes:
        ax.set_xlabel("Longitud")
        ax.set_ylabel("Latitud")
        ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.suptitle(
        "Marine Ecosystem Change Explorer · control de regiones", fontsize=13, color="#0b2545"
    )
    fig.tight_layout()
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest)
    plt.close(fig)
    return dest
