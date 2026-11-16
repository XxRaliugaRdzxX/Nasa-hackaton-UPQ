"""Catálogo de datasets y casos de estudio (contrato D14).

`CATALOG` es la única fuente de verdad sobre qué variables puede analizar la
herramienta. Agregar una variable = agregar una entrada aquí (y su producto en
config/products.yaml); el resto del sistema la descubre solo.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from mece.config import ROOT

BBox = tuple[float, float, float, float]  # (lat_min, lat_max, lon_min, lon_max)


@dataclass(frozen=True)
class DatasetSpec:
    """Descripción de un dataset analizable.

    Los cinco primeros campos son los del contrato original (ERDDAP). Los
    siguientes añaden el backend NASA directo (D15).
    """

    erddap_id: str | None
    var_name: str
    units: str
    server_url: str | None
    lat_descending: bool
    # --- extensiones
    backend: str = "earthaccess"  # earthaccess | opendap | erddap
    product_key: str = ""  # clave en config/products.yaml
    variable: str = ""  # nombre interno común (chlorophyll, sst…)
    label_es: str = ""
    label_en: str = ""
    source_es: str = ""
    source_en: str = ""
    log_transform: bool = False  # analizar en log10 (clorofila)
    trend_units_es: str = ""
    trend_units_en: str = ""
    limitation_es: str = ""
    limitation_en: str = ""
    available: bool = True
    label_pt: str = ""
    source_pt: str = ""
    trend_units_pt: str = ""
    limitation_pt: str = ""

    def loc(self, field: str, lang: str) -> str:
        """Texto del campo en el idioma pedido (es/en/pt), con respaldo en español."""
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_es", "")


CATALOG: dict[str, DatasetSpec] = {
    "chl": DatasetSpec(
        erddap_id="erdMH1chlamday_R2022SQ",
        var_name="chlor_a",
        units="mg m-3",
        server_url="https://coastwatch.pfeg.noaa.gov/erddap",
        lat_descending=True,
        backend="earthaccess",
        product_key="modis_chl_monthly",
        variable="chlorophyll",
        label_es="Clorofila-a",
        label_en="Chlorophyll-a",
        source_es="MODIS-Aqua L3m R2022.0 · mensual 4 km · NASA OB.DAAC",
        source_en="MODIS-Aqua L3m R2022.0 · monthly 4 km · NASA OB.DAAC",
        label_pt="Clorofila-a",
        source_pt="MODIS-Aqua L3m R2022.0 · mensal 4 km · NASA OB.DAAC",
        trend_units_pt="% / década",
        limitation_pt=(
            "<strong>Limitação declarada · águas Caso 2:</strong> na faixa costeira, os "
            "sedimentos e a matéria orgânica dissolvida do aporte fluvial superestimam a "
            "clorofila por satélite. A clorofila indica biomassa fitoplanctônica superficial, "
            "não produtividade. Com 23 anos de registro, uma tendência não pode, por si só, "
            "ser atribuída à mudança climática."
        ),
        log_transform=True,
        trend_units_es="% / década",
        trend_units_en="% / decade",
        limitation_es=(
            "<strong>Limitación declarada · aguas Caso 2:</strong> en la franja costera, "
            "los sedimentos y la materia orgánica disuelta del aporte fluvial sesgan al "
            "alza la clorofila satelital. La clorofila es un indicador de biomasa "
            "fitoplanctónica superficial, no de productividad. Con 23 años de registro, "
            "una tendencia no puede atribuirse por sí sola al cambio climático."
        ),
        limitation_en=(
            "<strong>Declared limitation · Case 2 waters:</strong> along the coast, river "
            "sediments and dissolved organic matter bias satellite chlorophyll upward. "
            "Chlorophyll indicates surface phytoplankton biomass, not productivity. A "
            "23-year record cannot by itself attribute a trend to climate change."
        ),
    ),
    "sst": DatasetSpec(
        erddap_id="jplMURSST41mday",
        var_name="analysed_sst",
        units="°C",
        server_url="https://coastwatch.pfeg.noaa.gov/erddap",
        lat_descending=False,
        backend="opendap",
        product_key="mur25_sst_daily",
        variable="sst",
        label_es="Temperatura superficial del mar",
        label_en="Sea surface temperature",
        source_es="GHRSST MUR25 v4.2 · diario→mensual 0.25° · NASA PO.DAAC",
        source_en="GHRSST MUR25 v4.2 · daily→monthly 0.25° · NASA PO.DAAC",
        label_pt="Temperatura da superfície do mar",
        source_pt="GHRSST MUR25 v4.2 · diário→mensal 0,25° · NASA PO.DAAC",
        trend_units_pt="°C / década",
        limitation_pt=(
            "<strong>Limitação declarada · produto L4:</strong> MUR é uma análise multissensor "
            "interpolada (TSM de fundação). Não é uma observação direta por pixel e suaviza a "
            "variabilidade costeira fina."
        ),
        log_transform=False,
        trend_units_es="°C / década",
        trend_units_en="°C / decade",
        limitation_es=(
            "<strong>Limitación declarada · producto L4:</strong> MUR es un análisis "
            "multisensor interpolado (SST de fundación). No es una observación directa por "
            "píxel y suaviza la variabilidad costera fina."
        ),
        limitation_en=(
            "<strong>Declared limitation · L4 product:</strong> MUR is an interpolated "
            "multi-sensor analysis (foundation SST). It is not a direct per-pixel "
            "observation and smooths fine coastal variability."
        ),
    ),
    # "pr": precipitación IMERG (fase siguiente; la arquitectura ya la admite)
}


@dataclass(frozen=True)
class Region:
    """Caso de estudio: un juego de parámetros con nombre."""

    id: str
    name_es: str
    name_en: str
    region_es: str
    region_en: str
    bbox: BBox
    t0: str
    t1: str
    datasets: tuple[str, ...]
    marker: dict = field(default_factory=dict)
    summary_es: str = ""
    summary_en: str = ""
    name_pt: str = ""
    region_pt: str = ""
    summary_pt: str = ""

    def loc(self, field: str, lang: str) -> str:
        """Texto del campo en el idioma pedido (es/en/pt), con respaldo en español."""
        return getattr(self, f"{field}_{lang}", "") or getattr(self, f"{field}_es", "")

    def name(self, lang: str) -> str:
        return self.loc("name", lang)


@dataclass(frozen=True)
class Store:
    id: str
    name: str
    bbox: BBox


@lru_cache(maxsize=1)
def _cases_yaml(path: Path | None = None) -> dict:
    path = path or ROOT / "config" / "cases.yaml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_regions() -> dict[str, Region]:
    raw = _cases_yaml()["cases"]
    out = {}
    for cid, c in raw.items():
        out[cid] = Region(
            id=cid,
            name_es=c["name_es"],
            name_en=c["name_en"],
            region_es=c.get("region_es", ""),
            region_en=c.get("region_en", ""),
            bbox=tuple(float(v) for v in c["bbox"]),
            t0=str(c["t0"]),
            t1=str(c["t1"]),
            datasets=tuple(c.get("datasets", list(CATALOG))),
            marker=c.get("marker", {}),
            summary_es=c.get("summary_es", "").strip(),
            summary_en=c.get("summary_en", "").strip(),
            name_pt=c.get("name_pt", ""),
            region_pt=c.get("region_pt", ""),
            summary_pt=c.get("summary_pt", "").strip(),
        )
    return out


def default_region_id() -> str:
    return _cases_yaml()["default_case"]


def load_stores() -> dict[str, Store]:
    return {
        sid: Store(id=sid, name=s["name"], bbox=tuple(float(v) for v in s["bbox"]))
        for sid, s in _cases_yaml()["stores"].items()
    }


def store_for_bbox(bbox: BBox) -> Store | None:
    """Primer almacén que contiene por completo el bbox pedido."""
    lat0, lat1, lon0, lon1 = bbox
    for st in load_stores().values():
        s0, s1, w0, w1 = st.bbox
        if s0 <= lat0 and lat1 <= s1 and w0 <= lon0 and lon1 <= w1:
            return st
    return None


def bbox_hash(bbox: BBox) -> str:
    """Hash estable del bbox para claves de caché."""
    txt = ",".join(f"{v:.4f}" for v in bbox)
    return hashlib.sha1(txt.encode()).hexdigest()[:10]


def validate_bbox(bbox: BBox) -> BBox:
    lat0, lat1, lon0, lon1 = (float(v) for v in bbox)
    if not (-90 <= lat0 < lat1 <= 90 and -180 <= lon0 < lon1 <= 180):
        raise ValueError(f"bbox inválido {bbox}: se espera (lat_min, lat_max, lon_min, lon_max)")
    return lat0, lat1, lon0, lon1
