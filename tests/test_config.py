"""La configuración del repositorio debe cargar y ser coherente."""

import pytest

from mece.config import ConfigError, get_settings


@pytest.fixture(scope="module")
def settings():
    return get_settings()


def test_config_loads(settings):
    assert len(settings.products) >= 8
    assert set(settings.regions) == {"gom", "gom_offshore", "tabasco_coast", "grijalva_usumacinta"}


def test_trend_windows_use_historical_final_products(settings):
    """Las tendencias solo pueden usar productos refinados (nunca NRT)."""
    for var, win in settings.analysis.trend_windows.items():
        p = settings.products[win.product]
        assert p.variable == var
        assert p.level == "final" and p.role == "historical", f"{var} usa un producto no refinado"


def test_climatology_inside_trend_windows(settings):
    clim = settings.analysis.climatology
    for win in settings.analysis.trend_windows.values():
        assert win.start <= clim.start and clim.end <= win.end


def test_imerg_final_window_does_not_exceed_v07_record(settings):
    """IMERG Final V07 termina en 2025-09 (D03); la ventana no puede pasar de ahí."""
    assert settings.analysis.trend_windows["precipitation"].end <= "2025-09"


def test_bad_yaml_raises_clear_error(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "products.yaml").write_text("region_bbox: {lat_min: 40, lat_max: 10}\n")
    get_settings.cache_clear()
    with pytest.raises(ConfigError):
        get_settings(tmp_path)
    get_settings.cache_clear()
