"""Catálogo, casos de estudio y utilidades de adquisición (sin red)."""

import pytest

from mece.acquisition.data import build_griddap_url, month_range
from mece.catalog import CATALOG, bbox_hash, load_regions, store_for_bbox, validate_bbox


def test_every_case_fits_a_store_and_uses_known_datasets():
    for cid, reg in load_regions().items():
        assert store_for_bbox(reg.bbox) is not None, f"{cid} no cabe en ningún almacén"
        assert set(reg.datasets) <= set(CATALOG)


def test_gulf_of_california_is_parametric():
    """Criterio 2: otra región solo cambia parámetros."""
    reg = load_regions()["gulf_california"]
    assert store_for_bbox(reg.bbox).id == "gulf_california"


def test_bbox_validation_and_hash():
    assert validate_bbox((18, 20.5, -94, -90.5)) == (18.0, 20.5, -94.0, -90.5)
    with pytest.raises(ValueError):
        validate_bbox((20.5, 18, -94, -90.5))
    assert bbox_hash((18, 20.5, -94, -90.5)) == bbox_hash((18.0, 20.50, -94.0, -90.5))


def test_month_range():
    assert month_range("2003-01-16", "2003-03") == ["2003-01", "2003-02", "2003-03"]


def test_griddap_url_respects_lat_descending():
    url = build_griddap_url(CATALOG["chl"], (18.0, 20.5, -94.0, -90.5), "2003-01", "2025-01")
    assert "erdMH1chlamday_R2022SQ.nc?chlorophyll" in url
    assert "[(20.5):1:(18.0)]" in url  # latitud descendente
    url2 = build_griddap_url(CATALOG["sst"], (18.0, 20.5, -94.0, -90.5), "2003-01", "2025-01")
    assert "[(18.0):1:(20.5)]" in url2
