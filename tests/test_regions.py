"""Los polígonos versionados deben ser válidos y respetar la separación tierra/mar."""

import geopandas as gpd
import pytest

from mece.config import get_settings

S = get_settings()
LAEA = S.region_build.metric_crs


def _load(name):
    path = S.regions_dir / name
    if not path.exists():
        pytest.skip(f"{name} no construido (ejecuta: mece regions build)")
    return gpd.read_file(path).to_crs(LAEA)


@pytest.mark.parametrize("region_id,region", list(S.regions.items()))
def test_geometries_valid_and_nonempty(region_id, region):
    for name in filter(None, [region.marine, region.land]):
        gdf = _load(name)
        assert len(gdf) == 1 and gdf.geometry.is_valid.all() and not gdf.geometry.is_empty.any()
        assert gdf.iloc[0]["region_id"] == region_id


@pytest.mark.parametrize(
    "region_id,region", [(k, r) for k, r in S.regions.items() if r.marine and r.land]
)
def test_marine_and_land_do_not_overlap(region_id, region):
    """Clorofila/SST (mar) y precipitación (tierra) no deben compartir área (< 1 km²)."""
    marine, land = _load(region.marine), _load(region.land)
    overlap_km2 = marine.geometry.iloc[0].intersection(land.geometry.iloc[0]).area / 1e6
    assert overlap_km2 < 1.0, f"{region_id}: {overlap_km2:.1f} km² de solape tierra/mar"


def test_nested_marine_regions_inside_gulf():
    gom = _load("gom_marine.geojson").geometry.iloc[0].buffer(1_000)  # 1 km de tolerancia
    for name in [
        "gom_offshore_marine.geojson",
        "tabasco_coast_marine.geojson",
        "gu_plume_marine.geojson",
    ]:
        assert gom.contains(_load(name).geometry.iloc[0]), f"{name} sale del Golfo"


def test_grijalva_usumacinta_basin_area_matches_literature():
    """La cuenca G-U mide ~128 000 km² (México + Guatemala)."""
    area = _load("gu_basin_land.geojson").geometry.iloc[0].area / 1e6
    assert 115_000 < area < 135_000, f"área {area:,.0f} km²"


def test_gu_basin_reaches_guatemala():
    lat_min = _load("gu_basin_land.geojson").to_crs("EPSG:4326").total_bounds[1]
    assert lat_min < 16.0, "la cuenca debe incluir la parte alta en Guatemala"
