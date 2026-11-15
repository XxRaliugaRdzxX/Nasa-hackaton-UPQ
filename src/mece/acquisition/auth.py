"""Autenticación con NASA Earthdata y verificación de acceso a cada DAAC.

Credenciales (en .env, nunca en el código):
    EARTHDATA_TOKEN                          (recomendado; caduca a los 60 días)
    o EARTHDATA_USERNAME + EARTHDATA_PASSWORD

Uso:  mece check-access
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urlparse

import earthaccess

from mece.config import Product, Settings

log = logging.getLogger(__name__)

_SIGNATURES = {b"\x89HDF": "HDF5/NetCDF4", b"CDF\x01": "NetCDF3", b"CDF\x02": "NetCDF3-64"}


class EarthdataAuthError(RuntimeError):
    """Fallo de autenticación con instrucciones para resolverlo."""


def login() -> earthaccess.Auth:
    """Inicia sesión con las credenciales del entorno. No imprime ningún secreto."""
    has_token = bool(os.environ.get("EARTHDATA_TOKEN"))
    has_user = bool(os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD"))
    if not (has_token or has_user):
        raise EarthdataAuthError(
            "No hay credenciales de Earthdata. Copia .env.example a .env y define "
            "EARTHDATA_TOKEN (o EARTHDATA_USERNAME y EARTHDATA_PASSWORD)."
        )
    auth = earthaccess.login(strategy="environment")
    if not (auth and auth.authenticated):
        raise EarthdataAuthError(
            "Earthdata rechazó las credenciales. Si usas token, puede haber caducado "
            "(duran 60 días): genera uno nuevo en https://urs.earthdata.nasa.gov/profile"
        )
    return auth


@dataclass
class AccessResult:
    product_key: str
    daac: str
    ok: bool
    detail: str


def _probe_window(product: Product) -> tuple[str, str]:
    """Ventana temporal donde el producto debería tener granulos."""
    if product.level == "nrt":  # los NRT antiguos se retiran del catálogo
        end = date.today()
        return (end - timedelta(days=10)).isoformat(), end.isoformat()
    return "2025-08-01", "2025-08-31"


def check_access(settings: Settings) -> list[AccessResult]:
    """Descarga los primeros bytes de un granulo real de cada producto configurado."""
    login()
    session = earthaccess.get_requests_https_session()
    results: list[AccessResult] = []
    for key, p in settings.products.items():
        try:
            granules = earthaccess.search_data(
                concept_id=p.concept_id,
                granule_name=p.granule_pattern,
                temporal=_probe_window(p),
                count=1,
            )
            if not granules:
                results.append(
                    AccessResult(key, p.daac, False, "sin granulos en la ventana de prueba")
                )
                continue
            links = [
                u
                for u in granules[0].data_links(access="external")
                if not u.endswith((".md5", ".xml"))
            ]
            r = session.get(links[0], headers={"Range": "bytes=0-7"}, stream=True, timeout=60)
            if r.status_code == 416:  # algunos servidores (oceandata) no aceptan rangos
                r.close()
                r = session.get(links[0], stream=True, timeout=60)
            head = r.raw.read(8)
            r.close()
            kind = next((v for sig, v in _SIGNATURES.items() if head.startswith(sig)), None)
            if r.status_code in (200, 206) and kind:
                results.append(AccessResult(key, p.daac, True, f"HTTP {r.status_code} · {kind}"))
            elif r.status_code == 403:
                results.append(
                    AccessResult(
                        key,
                        p.daac,
                        False,
                        "HTTP 403: falta aprobar la aplicación/EULA del DAAC en "
                        "https://urs.earthdata.nasa.gov (Applications → Authorized Apps)",
                    )
                )
            else:
                host = urlparse(r.url).hostname
                results.append(
                    AccessResult(key, p.daac, False, f"HTTP {r.status_code} desde {host}")
                )
        except Exception as exc:  # noqa: BLE001 — se reporta cualquier fallo por producto
            results.append(
                AccessResult(key, p.daac, False, f"{type(exc).__name__}: {str(exc)[:150]}")
            )
    return results
