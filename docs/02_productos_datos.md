# 02 · Productos satelitales, regiones y estrategia de adquisición

> Cobertura **verificada en NASA CMR el 2026‑11‑15**. El pipeline vuelve a consultar CMR antes de cada descarga, así que estas fechas no se fijan en el código.

## 1. Selección final de productos

### 1.1 Productos para análisis histórico (refinados)

| Variable | Producto (short_name) | Versión | Concept ID | Variable en archivo | Unidad nativa | Resolución | Cobertura verificada | Ventana de tendencia propuesta |
|---|---|---|---|---|---|---|---|---|
| Clorofila‑a | `MODISA_L3m_CHL` (mensual `MO`, 4 km) | R2022.0 | `C3380709133-OB_CLOUD` | `chlor_a` | mg m⁻³ | 4.64 km (1/24°) | 2002‑07 → 2026‑04 | **2003‑01 → 2025‑12** |
| SST (principal) | `MUR25-JPL-L4-GLOB-v04.2` (diario → mensual propio) | 4.2 | `C2036880657-POCLOUD` | `analysed_sst` | K → **°C** | 0.25° | 2002‑08‑31 → 2026‑11‑13 | **2003‑01 → 2025‑12** |
| SST (contraste) | `MODISA_L3m_NSST` (nocturna 11 µm, mensual 4 km) | R2019.0 | `C1615929573-OB_DAAC` | `sst` | °C | 4.64 km | 2002‑07 → hoy | Solo validación y cruces con clorofila |
| Precipitación | `GPM_3IMERGM` (Final Run mensual) | V07 (V07B) | `C2723754851-GES_DISC` | `precipitation` (grupo `Grid`) | **mm h⁻¹** → mm mes⁻¹ | 0.1° | 1998‑01 → **2025‑09 (serie cerrada)** | **2001‑01 → 2025‑09** (común: 2003‑01 → 2025‑09) |
| Escorrentía / humedad (Fase 4) | `GLDAS_NOAH025_M` | 2.1 | `C1342986036-GES_DISC` | `Qs_acc`, `Qsb_acc`, `SoilMoi0_10cm_inst` | kg m⁻² por 3 h (media mensual) → mm mes⁻¹ | 0.25° | 2000‑01 → 2026‑07 | A definir tras verificación |

### 1.2 Productos para monitoreo casi en tiempo real (NRT)

| Variable | Producto | Concept ID | Latencia típica | Uso |
|---|---|---|---|---|
| Clorofila‑a | `MODISA_L3m_CHL_NRT` (diario 4 km) | `C3380709124-OB_CLOUD` | ~1–2 días | Monitoreo y anomalía contra la climatología MODIS, mientras Aqua funcione |
| Clorofila‑a (continuidad) | `PACE_OCI_L3M_BGC_NRT` (diario 4 km, incluye `chlor_a`) | `C4184125829-OB_CLOUD` | ~1–2 días | Valores absolutos; reemplaza a MODIS NRT cuando Aqua se apague |
| SST | `MUR25-JPL-L4-GLOB-v04.2` | `C2036880657-POCLOUD` | ~1 día | El mismo producto que el histórico, así que la anomalía es coherente |
| Precipitación | `GPM_3IMERGDL` (Late Run diario) | `C2723754859-GES_DISC` | ~14 h | Acumulados de 1, 7 y 30 días y mes en curso **provisional** |

**Por qué Late y no Early:** Late (unas 14 h) incorpora más datos de microondas que Early (unas 4 h) y es más precisa. Para un monitor ambiental, 10 horas más de latencia valen más que la mejora en precisión.

### 1.3 DOI para citación (obtenidos de CMR)

| Producto | DOI |
|---|---|
| MODIS‑Aqua L3m CHL R2022.0 | `10.5067/AQUA/MODIS/L3M/CHL/2022.0` |
| GHRSST MUR25 v4.2 | `10.5067/GHM25-4FJ42` |
| GPM IMERG Final mensual V07 | `10.5067/GPM/IMERG/3B-MONTH/07` |
| GPM IMERG Late diario V07 | `10.5067/GPM/IMERGDL/DAY/07` |
| GLDAS Noah 0.25° mensual 2.1 | `10.5067/SXAVCZFAQLNO` |

Los productos sin DOI en CMR (SST de MODIS y productos NRT) se citan por su nombre corto, versión y URL de OB.DAAC.

## 2. Reglas de calidad y conversión por producto

| Producto | Controles de calidad | Conversión |
|---|---|---|
| `chlor_a` L3m | El binning L3 ya excluyó los píxeles con banderas L2 (tierra, nubes, brillo solar, falla atmosférica, etc.). Además: (1) descartar valores ≤ 0 o > 100 mg m⁻³; (2) marcar píxeles a < 20 km de la costa como "ópticamente complejos"; (3) guardar cuántos días válidos tiene cada mes cuando se construyan compuestos propios. | Promedios en **log10** (media geométrica). Se reporta en mg m⁻³ y como %/década. |
| MUR25 `analysed_sst` | Usar `analysis_error` como incertidumbre y `mask` para excluir tierra y hielo. MUR es interpolado: en el reporte se dice que **no es una observación directa por píxel**. | K → °C (−273.15). Mensual = media de días. |
| MODIS `sst` nocturna | Leer la capa de calidad del archivo (`qual_sst`) y quedarse con las mejores clases. Las clases exactas se confirman en la Fase 1 leyendo el archivo. | Ya viene en °C. |
| IMERG `precipitation` | Usar `precipitationQualityIndex` como información. Excluir el relleno (`_FillValue`). | mm h⁻¹ × 24 × días del mes. Promedio areal ponderado por cos(lat). Opcional: volumen en km³ = mm × área. |
| GLDAS `Qs_acc` | Archivo modelado, sin banderas. Advertencia fija: **escorrentía modelada ≠ caudal medido**. | Media mensual de acumulados de 3 h → × 8 × días = mm mes⁻¹. |

Regla general: **las unidades, el `_FillValue`, `scale_factor` y el orden de coordenadas se leen del archivo y se validan contra `config/products.yaml`.** Si no coinciden, el pipeline se detiene con un error explícito.

Diferencias de convenciones conocidas que el código debe manejar:
- **MODIS L3m:** latitud descendente (90 → −90) y longitud −180 → 180.
- **IMERG:** HDF5 con grupo `Grid` y dimensiones (`time`, `lon`, `lat`), es decir, lon antes que lat. Hay que transponer.
- **MUR25:** latitud ascendente. El `time` va a las 09:00 UTC.
- **GLDAS:** latitud ascendente, y la tierra va enmascarada con `_FillValue`.

## 3. Regiones de estudio

### 3.1 Principio
Cada **región de análisis** es un par: una zona marina receptora más su cuenca terrestre aportante.

| ID | Región | Polígono marino (chl, SST) | Polígono terrestre (precipitación, GLDAS) |
|---|---|---|---|
| `gom` | Golfo de México completo | Límite IHO "Gulf of Mexico" (Marine Regions, CC‑BY) | Cuencas que drenan al Golfo, de HydroBASINS (nivel 3–4). **Fase 2**, por el gran tamaño del Mississippi. |
| `tabasco_coast` | Costa de Tabasco | Franja marina de 0 a 50 km desde la costa, entre los límites estatales de Tabasco (INEGI) | Cuencas costeras de Tabasco (HydroBASINS nivel 6–7) |
| `grijalva_usumacinta` | Desembocadura Grijalva‑Usumacinta | Zona de pluma: semicírculo marino alrededor de la boca (Frontera, ~18.6 N, 92.65 W). Radio de trabajo de 60 km, **a validar con imágenes de pluma** | Cuenca completa Grijalva‑Usumacinta, México + Guatemala (HydroBASINS) |
| `gom_offshore` | Golfo oceánico (referencia) | Zona IHO menos la franja de 100 km desde la costa | — |

`gom_offshore` se agrega para contestar la pregunta "¿costa vs. océano?" con un contraste limpio.

### 3.2 Construcción y versionado
- Los polígonos se generan con un script reproducible (`src/mece/geospatial/build_regions.py`) a partir de fuentes públicas. Se guardan como **GeoJSON en EPSG:4326** en `data/spatial/regions/` y **se versionan en Git**.
- Cada GeoJSON lleva sus metadatos: fuente, licencia, fecha, buffer aplicado y propósito (`marine` / `land`).
- **Máscara tierra‑mar:** los productos oceánicos ya traen la tierra enmascarada. Además, el polígono marino se recorta con la línea de costa (GSHHG o Natural Earth 10 m), para que no se cuelen píxeles mixtos en el promedio.
- **Asignación de píxeles:** `regionmask` (por centro de píxel) con ponderación por área (cos lat). Para regiones pequeñas en la malla de 0.25° (MUR25, GLDAS) se usa ponderación por fracción de solape, porque con pocos píxeles el criterio de centro sesga el resultado.

## 4. Estrategia de adquisición

### 4.1 Herramienta
**`earthaccess`** (biblioteca oficial de NASA) para autenticación, búsqueda en CMR y descarga desde OB.DAAC, GES DISC y PO.DAAC. Una sola herramienta cubre los cuatro centros de datos.

**Requisitos de cuenta (una vez por cuenta del equipo):**
1. Una cuenta Earthdata Login.
2. Autorizar en el perfil de Earthdata la aplicación **"NASA GESDISC DATA ARCHIVE"**; sin esto, IMERG y GLDAS fallan con 401.
3. Credenciales en variables de entorno `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`, o en `EARTHDATA_TOKEN`, dentro de `.env`, que **nunca** se versiona.

### 4.2 Descarga histórica (backfill, se ejecuta una vez)

1. Para cada producto y mes:
   1. Buscar el granulo en CMR.
   2. Descargarlo a `data/tmp/`.
   3. **Recortar** al rectángulo del Golfo con 1° de margen: lat 17–32 N, lon 99–79 W.
   4. Guardar el recorte en `data/raw/<variable>/`.
   5. **Borrar el archivo global.**
   6. Registrar el granulo en el catálogo SQLite: nombre, checksum, fechas de observación y descarga, versión.
2. Es idempotente: si el granulo ya está en el catálogo con el mismo checksum, se salta.

| Producto | Archivos | MB/archivo (global) | Descarga total | Guardado tras recorte |
|---|---|---|---|---|
| CHL mensual 4 km | ~282 | ~45 | ~12.6 GB | ~50 MB |
| MUR25 diario | ~8 800 | ~1.8 | ~16 GB | ~60 MB |
| MODIS NSST mensual 4 km | ~282 | ~25 | ~7 GB | ~30 MB |
| IMERG mensual | ~333 | ~18 | ~6 GB | ~25 MB |
| GLDAS mensual (Fase 4) | ~320 | ~23 | ~7.4 GB | ~15 MB |

**Total transitorio:** unos 49 GB, que se descargan en streaming y se borran archivo por archivo. Ocupación permanente: **menos de 0.5 GB**. Hay 394 GB libres.

**Alternativa para MUR25:** NASA ofrece subsetting en el servidor (OPeNDAP / Harmony), con el que se descargaría solo el Golfo. Se evaluará en la Fase 1. Si funciona de forma estable, reduce la descarga de 16 GB a menos de 100 MB.

**Nota sobre "raw":** como el archivo global se puede volver a descargar con su DOI, se conserva como "raw" el **recorte sin transformar** (mismos valores, malla y atributos que el original). Así se cumple la separación entre raw y processed sin guardar 48 GB.

### 4.3 Actualización incremental (NRT y nuevas versiones refinadas)
- **Cada hora:** consultar CMR por granulos con `revision_date` posterior a la última consulta. Es solo metadato, no se descarga nada.
- **Si hay granulos nuevos:** descargar, recortar, registrar y procesar únicamente ese periodo.
- **Reemplazo NRT → refinado:** cada registro tiene clave `(variable, periodo, nivel)`. Cuando llega el producto refinado de un periodo que solo tenía NRT, se guarda junto al NRT. El dashboard y los análisis **prefieren el refinado**. El NRT se conserva para auditar las diferencias.
- **Nueva versión de producto** (p. ej. IMERG V08): se detecta como colección nueva. No se mezcla: se abre una tarea de reprocesamiento completo, que **requiere aprobación manual**.

### 4.4 "Última observación" vs "última actualización"
- `last_observation` es el fin del periodo cubierto por el granulo más reciente (`time_end`).
- `last_check` es la última consulta a CMR. `last_ingest` es la última descarga procesada.
- El dashboard muestra los tres por variable, junto con la etiqueta de nivel (FINAL / NRT / PROVISIONAL). **Nunca presenta `last_check` como si fuera la fecha del dato.**
