"""Carga y validación de la configuración del proyecto.

Fuentes:
  - config/products.yaml  → catálogo de productos NASA
  - config/analysis.yaml  → parámetros estadísticos
  - config/regions.yaml   → regiones de estudio (pares marino/terrestre)
  - .env                  → credenciales y rutas (nunca versionado)

Uso:
    from mece.config import get_settings
    s = get_settings()
    s.products["mur25_sst_daily"].short_name
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

# Raíz del repositorio: src/mece/config.py → parents[2]. En Docker se fija con MECE_ROOT.
ROOT = Path(os.environ.get("MECE_ROOT", Path(__file__).resolve().parents[2]))

Variable = Literal["chlorophyll", "sst", "precipitation", "runoff", "flh"]
Conversion = Literal[
    "none",
    "kelvin_to_celsius",
    "mm_per_hour_to_mm_per_month",
    "gldas_3h_acc_to_mm_per_month",
]


class ConfigError(RuntimeError):
    """Error de configuración con mensaje explícito para el usuario."""


# --------------------------------------------------------------------- productos
class BBox(BaseModel):
    lat_min: float = Field(ge=-90, le=90)
    lat_max: float = Field(ge=-90, le=90)
    lon_min: float = Field(ge=-180, le=180)
    lon_max: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def _ordered(self) -> BBox:
        if self.lat_min >= self.lat_max or self.lon_min >= self.lon_max:
            raise ValueError("region_bbox: los mínimos deben ser menores que los máximos")
        return self


class Product(BaseModel):
    variable: Variable
    role: Literal["historical", "nrt", "validation", "ancillary", "research"]
    level: Literal["final", "nrt"]
    daac: str
    short_name: str
    version: str
    concept_id: str
    doi: str | None = None
    granule_pattern: str
    temporal_resolution: Literal["daily", "monthly"]
    spatial_resolution: str
    file_variable: str
    extra_variables: list[str] = []
    group: str | None = None
    units_native: str
    units_target: str
    conversion: Conversion
    valid_range: tuple[float, float]
    lat_order: Literal["ascending", "descending"]
    dims_order: list[str] | None = None
    quality_variable: str | None = None
    max_quality_level: int | None = None
    notes: str = ""

    @field_validator("valid_range")
    @classmethod
    def _range_ordered(cls, v: tuple[float, float]) -> tuple[float, float]:
        if v[0] >= v[1]:
            raise ValueError("valid_range debe ser [mínimo, máximo]")
        return v


class ProductsConfig(BaseModel):
    region_bbox: BBox
    products: dict[str, Product]


# ---------------------------------------------------------------------- análisis
class Window(BaseModel):
    start: str = Field(pattern=r"^\d{4}-\d{2}$")
    end: str = Field(pattern=r"^\d{4}-\d{2}$")
    product: str | None = None

    @model_validator(mode="after")
    def _ordered(self) -> Window:
        if self.start >= self.end:
            raise ValueError(f"ventana {self.start}→{self.end}: el inicio debe ser anterior al fin")
        return self


class AnalysisConfig(BaseModel):
    model_config = {"extra": "allow"}  # el resto de bloques se valida donde se usa
    climatology: Window
    trend_windows: dict[str, Window]
    correlation_window: Window


# ---------------------------------------------------------------------- regiones
class Region(BaseModel):
    name_es: str
    name_en: str
    marine: str | None = None  # ruta GeoJSON relativa a data/spatial/regions/
    land: str | None = None
    description_es: str = ""
    description_en: str = ""


class RegionBuild(BaseModel):
    metric_crs: str
    simplify_m: float = Field(ge=0)
    offshore_buffer_km: float = Field(gt=0)
    tabasco_strip_km: float = Field(gt=0)
    plume_center: dict[Literal["lat", "lon"], float]
    plume_radius_km: float = Field(gt=0)
    gu_main_basin_id: int
    tabasco_outlet_min_frac: float = Field(gt=0, le=1)
    gom_outlet_min_frac: float = Field(gt=0, le=1)


class RegionsConfig(BaseModel):
    regions: dict[str, Region]
    build: RegionBuild


# ---------------------------------------------------------------------- settings
class Settings(BaseModel):
    root: Path
    data_dir: Path
    products: dict[str, Product]
    region_bbox: BBox
    analysis: AnalysisConfig
    regions: dict[str, Region]
    region_build: RegionBuild

    @property
    def regions_dir(self) -> Path:
        return self.data_dir / "spatial" / "regions"

    @property
    def ancillary_dir(self) -> Path:
        return self.data_dir / "raw" / "ancillary"


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"No existe el archivo de configuración: {path}")
    try:
        with path.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML inválido en {path}: {exc}") from exc


@lru_cache(maxsize=1)
def get_settings(root: Path | None = None) -> Settings:
    """Lee y valida toda la configuración. Falla con un mensaje claro si algo no cuadra."""
    root = Path(root) if root else ROOT
    load_dotenv(root / ".env", override=False)
    data_dir = Path(os.environ.get("MECE_DATA_DIR", root / "data"))
    if not data_dir.is_absolute():
        data_dir = (root / data_dir).resolve()

    try:
        prod = ProductsConfig.model_validate(_read_yaml(root / "config" / "products.yaml"))
        analysis = AnalysisConfig.model_validate(_read_yaml(root / "config" / "analysis.yaml"))
        regions = RegionsConfig.model_validate(_read_yaml(root / "config" / "regions.yaml"))
    except ValueError as exc:  # pydantic.ValidationError hereda de ValueError
        raise ConfigError(f"Configuración inválida:\n{exc}") from exc

    # Coherencia entre archivos: las ventanas de tendencia apuntan a productos existentes
    for var, win in analysis.trend_windows.items():
        if win.product and win.product not in prod.products:
            raise ConfigError(
                f"analysis.yaml: trend_windows.{var}.product='{win.product}' "
                "no existe en products.yaml"
            )

    return Settings(
        root=root,
        data_dir=data_dir,
        products=prod.products,
        region_bbox=prod.region_bbox,
        analysis=analysis,
        regions=regions.regions,
        region_build=regions.build,
    )
