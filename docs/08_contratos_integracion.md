# 08 · Contratos del sistema base y guía de integración

> Esta es la **base donde se integra la investigación del equipo** (D14). La herramienta es **parametrizada, no un reporte**: todo se invoca con `(dataset_id, bbox, t0, t1, season)`. Cambiar de región = cambiar parámetros, **nunca** reescribir código.
>
> En producción: **https://nasa.cardenal-shekers.online**

## 1. Mapa de la especificación al repositorio

La especificación "Trend Detective" proponía `app.py` + `src/{catalog,data,analysis,viz}.py`. Se respetan **las firmas exactas**, pero dentro del paquete `mece`, para no duplicar el código del plan:

| Especificación | Repositorio | Contenido |
|---|---|---|
| `src/catalog.py` | `src/mece/catalog.py` | `DatasetSpec`, `CATALOG`, casos de estudio (`config/cases.yaml`) |
| `src/data.py` | `src/mece/acquisition/data.py` | `fetch_dataset` y backends `opendap`, `earthaccess` y `erddap` |
| `src/analysis.py` | `src/mece/statistics/analysis.py` | `compute_anomalies`, `regional_series`, `trend_test`, `trend_map` |
| `src/viz.py` | `src/mece/visualization/figures.py` | `fig_globe` (3D), `fig_trend_map`, `fig_series` |
| `app.py` | `dashboard/app.py` | Solo UI y orquestación |
| `data/raw`, `data/results` | `data/raw`, `data/processed`, `data/cache`, `data/results` | Fuera de Git |

## 2. Contratos

```python
from mece.acquisition.data import fetch_dataset
from mece.statistics.analysis import compute_anomalies, regional_series, trend_test, trend_map

da   = fetch_dataset("chl", (18.0, 20.5, -94.0, -90.5), "2003-01", "2025-12")  # (time, lat, lon)
anom = compute_anomalies(da)               # valor − climatología del mismo mes (log10 en clorofila)
s    = regional_series(anom, season="wet") # "all" | "wet" (jun–oct) | "dry" (nov–may)
res  = trend_test(s)                       # TrendResult: slope_per_decade, intercept, p, z, n, significant, ci_low, ci_high…
tmap = trend_map(anom, min_valid=120, cache_key="mi_clave")  # Dataset: slope, p, n, significant
```

| Función | Garantías |
|---|---|
| `fetch_dataset` | Latitud siempre ascendente, sin importar el orden del producto. Caché por `(dataset, bbox_hash, t0, t1)`: la segunda llamada no descarga nada. Si faltan meses se descargan, salvo con `download_missing=False`. Nunca cachea una consulta incompleta. |
| `compute_anomalies` | Misma forma que la entrada. Climatología 2003‑2022 (`config/analysis.yaml`). En clorofila trabaja en log10. |
| `regional_series` | Media ponderada por cos(lat). Los meses con < 30 % de píxeles válidos quedan como NaN. |
| `trend_test` | Año completo: Mann‑Kendall **estacional Hirsch‑Slack**, con covarianza entre meses. Temporada: Mann‑Kendall **Hamed‑Rao**. Pendiente Theil‑Sen sobre años decimales con IC 95 %. `robust=False` si ambas pruebas discrepan. |
| `trend_map` | MK + Sen vectorizado por píxel, con varianza corregida por AR(1). `significant` = pasa FDR Benjamini‑Hochberg (q = 0.10) **y** p < 0.05. |

### Verificación (`pytest`)

| Criterio de la especificación | Prueba |
|---|---|
| 1 · `fetch_dataset(...)` devuelve `(time, lat, lon)` | Verificado con datos reales en el servidor |
| 2 · Golfo de California sin editar código | `tests/test_catalog_data.py::test_gulf_of_california_is_parametric` |
| 3 · Pendiente inyectada recuperada ±10 % | `tests/test_analysis.py::test_trend_test_recovers_injected_slope_within_10pct` |
| 4 · Nunca colorear p ≥ 0.05 | `test_trend_map_never_colors_p_ge_005` y `test_trend_map_never_colors_nonsignificant` |
| 5 · Segunda ejecución sin descargas | Caché de `fetch_dataset` y de `trend_map` |
| Extra · Falsos positivos ≈ α | `test_false_positive_rate_without_trend` (40 réplicas con ruido AR(1)) |

## 3. Cómo integrar tu trabajo

### Agregar una región de estudio
1. Agrega un bloque en `config/cases.yaml` con `bbox`, `t0`, `t1`, `datasets`, nombres ES/EN y el marcador.
2. Si el bbox no cabe en ningún almacén (`stores`), agrega un almacén y ejecuta `mece pipeline fetch --dataset chl` y `--dataset sst`.
3. Ejecuta `mece pipeline precompute --case <id>`.

La región aparece sola en el globo y en el selector, sin tocar código.

### Agregar una variable (p. ej. precipitación IMERG)
1. Agrega el producto en `config/products.yaml`. IMERG ya está ahí.
2. Agrega una entrada en `CATALOG` (`src/mece/catalog.py`) con `backend`, `units`, etiquetas y la limitación declarada.
3. Implementa su función `ensure_<producto>` en `acquisition/data.py`. Debe escribir archivos mensuales en `monthly_path(...)`.
4. Listo: `fetch_dataset`, el análisis y la UI la usan sin más cambios.

### Agregar un análisis (correlaciones, desfases…)
- Va en `src/mece/statistics/` como función pura: recibe `xr.DataArray` o `pd.Series` y devuelve un dataclass o un `Dataset`.
- Su prueba con datos sintéticos va en `tests/`.
- La UI solo llama a la función. **Nada de lógica de análisis en `dashboard/`.**

## 4. Datos y pipeline

```bash
mece pipeline fetch --dataset chl     # MODIS-Aqua mensual → almacenes (solo lo que falta)
mece pipeline fetch --dataset sst     # MUR25 diario por OPeNDAP → mensual
mece pipeline globe                   # textura SST global + costas/tierra del globo
mece pipeline precompute [--case id]  # mapas de tendencia a resolución completa
```

| Almacén | bbox | Clorofila | SST |
|---|---|---|---|
| `gom` | 17–32 N, 99–79 W | 2002‑07 → 2026‑04 (286 meses) | 2002‑09 → último mes completo |
| `gulf_california` | 21–33 N, 116–104 W | ídem | ídem |

**Regla de oro:** la interfaz **nunca calcula con datos incompletos**. Si faltan meses, muestra el avance de la descarga.

## 5. Interfaz (D16): componentes interactivos

La interfaz combina Streamlit con **componentes propios** (`st.components.v2`, bidireccionales), definidos en `dashboard/components.py`. Son solo presentación: reciben datos ya calculados y devuelven eventos (`select`, `analyze`) a Python.

| Componente | Tecnología | Interacción |
|---|---|---|
| `globe` | globe.gl 2.46.2 (Three.js) | 4 capas en vivo (TSM MUR25, clorofila MODIS NRT, Tierra de noche, Blue Marble); clic en una región para seleccionarla; tooltip; lectura del valor bajo el cursor; rotación, centrar, zoom y pantalla completa; anillos pulsantes; arcos "aporte continental" cuenca→mar; vuelo de cámara al cambiar de región |
| `mission_bar` | HTML/CSS/JS | Emblema orbital animado y reloj UTC en vivo |
| `kpis` | HTML/CSS/JS | Conteo animado, inclinación 3D al pasar el cursor y medidor de z con zonas significativas (\|z\| > 1.96) |
| `region_cards` | HTML/CSS/JS | Tarjetas con brillo al pasar el cursor; clic para seleccionar la región |

Tema global: `dashboard/theme.py` (fondo espacial animado, paneles de vidrio, menú con degradado, cinta de telemetría).

### Texturas del globo
`mece pipeline globe` genera `data/spatial/globe/tex_{sst,chl}.jpg`:
- El océano es el dato real coloreado y la tierra es Blue Marble atenuada.
- Se acompaña de `grid_{sst,chl}.json`, una rejilla a 1° para leer el valor bajo el cursor.
- La app las publica en `/app/static/globe/` (`enableStaticServing = true`).

**Para agregar una capa al globo**, hay que generar su textura y su rejilla con `mece.visualization.textures` y añadir una entrada en `LAYERS` (JavaScript de `components.py`).

> Detalle técnico: three-globe usa d3-geo, que espera los polígonos en sentido **horario**. En sentido antihorario, una caja se interpreta como "todo el planeta excepto la caja".
