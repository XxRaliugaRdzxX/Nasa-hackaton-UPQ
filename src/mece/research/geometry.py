"""Geometrías de la investigación (PASOS 1.1, 1.5 y 5.1 del notebook del equipo)."""

from __future__ import annotations

from functools import lru_cache

import geopandas as gpd
import numpy as np
import shapely
import xarray as xr

from mece.research.fetch import research_config, research_dir


@lru_cache(maxsize=1)
def gulf_polygon():
    """Límite del Golfo (GCOOS GoM_Region_GSHHS), reparado como en la celda 39 del notebook."""
    gdf = gpd.read_file(research_dir() / "ancillary" / "gom_polygon.geojson")
    return shapely.make_valid(shapely.union_all(gdf.geometry.make_valid().array))


@lru_cache(maxsize=1)
def basin_geometries() -> dict:
    cfg = research_config()["basins"]
    out = {}
    for key, b in cfg.items():
        if b["shape"] == "huc2":
            gdf = gpd.read_file(research_dir() / "ancillary" / "mississippi_huc2.geojson")
            out[key] = shapely.make_valid(shapely.union_all(gdf.geometry.make_valid().array))
        else:
            out[key] = shapely.box(*b["shape"])
    return out


def region_masks(da: xr.DataArray) -> dict[str, xr.DataArray]:
    """Máscara océano (polígono del Golfo) ∩ caja de cada región (mascaras_regiones)."""
    lon2d, lat2d = np.meshgrid(da.lon.values, da.lat.values)
    ocean = shapely.contains_xy(gulf_polygon(), lon2d, lat2d)
    out = {}
    for key, r in research_config()["regions"].items():
        m = ocean.copy()
        if r["box"] is not None:
            x0, x1, y0, y1 = r["box"]
            m &= (lon2d >= x0) & (lon2d <= x1) & (lat2d >= y0) & (lat2d <= y1)
        out[key] = xr.DataArray(m, coords={"lat": da.lat, "lon": da.lon}, dims=("lat", "lon"))
    return out


def land_mask(da: xr.DataArray) -> np.ndarray:
    """Tierra (Natural Earth 10 m) en la rejilla de `da` (equivale a regionmask land_10)."""
    import regionmask

    from mece.config import get_settings

    land = gpd.read_file(
        f"zip://{get_settings().ancillary_dir / 'natural_earth' / 'ne_10m_land.zip'}",
        bbox=(
            float(da.lon.min()) - 1,
            float(da.lat.min()) - 1,
            float(da.lon.max()) + 1,
            float(da.lat.max()) + 1,
        ),
    )
    return regionmask.mask_geopandas(land, da.lon, da.lat).notnull().values


def basin_masks(da: xr.DataArray) -> dict[str, xr.DataArray]:
    lon2d, lat2d = np.meshgrid(da.lon.values, da.lat.values)
    land = land_mask(da)
    return {
        key: xr.DataArray(
            shapely.contains_xy(geom, lon2d, lat2d) & land,
            coords={"lat": da.lat, "lon": da.lon},
            dims=("lat", "lon"),
        )
        for key, geom in basin_geometries().items()
    }


def regions_geojson() -> dict:
    """Regiones (caja ∩ Golfo) y cuencas como GeoJSON simplificado para la web."""
    cfg = research_config()
    gulf = gulf_polygon()
    feats = []
    for key, r in cfg["regions"].items():
        geom = (
            gulf
            if r["box"] is None
            else gulf.intersection(shapely.box(r["box"][0], r["box"][2], r["box"][1], r["box"][3]))
        )
        feats.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": "marine",
                    "id": key,
                    **{k: r[k] for k in ("name_es", "name_en", "name_pt")},
                },
                "geometry": shapely.geometry.mapping(geom.simplify(0.03)),
            }
        )
    for key, geom in basin_geometries().items():
        b = cfg["basins"][key]
        feats.append(
            {
                "type": "Feature",
                "properties": {
                    "kind": "basin",
                    "id": key,
                    **{k: b[k] for k in ("name_es", "name_en", "name_pt")},
                },
                "geometry": shapely.geometry.mapping(geom.simplify(0.05)),
            }
        )
    return {"type": "FeatureCollection", "features": feats}
