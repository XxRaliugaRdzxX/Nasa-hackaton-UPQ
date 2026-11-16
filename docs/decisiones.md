# Registro de decisiones (ADR)

Estados:
- **PROPUESTA**: falta la aprobación del responsable.
- **APROBADA**
- **RECHAZADA**
- **REEMPLAZADA**: sustituida por una decisión posterior.

Toda decisión importante se registra aquí **antes** de implementarla.

| ID | Decisión | Estado | Justificación (ver doc) | Fecha |
|---|---|---|---|---|
| D01 | SST principal = **GHRSST MUR25 v4.2**. MODIS‑Aqua NSST solo como contraste | APROBADA | La deriva orbital de Aqua sesga la SST diurna y la misión está en su final (`01` §2.3) | 2026‑11‑15 |
| D02 | Tendencias de clorofila solo con MODIS‑Aqua R2022.0, de 2003‑01 a 2025‑12. PACE solo para NRT, sin mezclarlos | APROBADA | `01` §2.4 | 2026‑11‑15 |
| D03 | Precipitación histórica = IMERG Final V07 hasta 2025‑09. Los meses posteriores con Late se marcan PROVISIONAL. Con V08 se reprocesa todo | APROBADA | `01` §2.1 | 2026‑11‑15 |
| D04 | Climatología de referencia 2003‑01 → 2022‑12 | APROBADA | `04` §0 | 2026‑11‑15 |
| D05 | Se descartan n8n y PostGIS. Almacenamiento con NetCDF + Parquet + SQLite | APROBADA | `01` §2.9 | 2026‑11‑15 |
| D06 | Paquete `src/mece/` instalable. Docker Compose con `app` y `worker` (supercronic) | APROBADA | `03` §2 | 2026‑11‑15 |
| D07 | Región como selector global. La página 4 pasa a "Comparar regiones" | APROBADA | `05` §1 | 2026‑11‑15 |
| D08 | Reportes con plantillas por reglas, sin LLM | APROBADA | `05` §5.1 | 2026‑11‑15 |
| D09 | Publicación por **subdominio**, sin bajar RRHH | REEMPLAZADA por D17 | `07` §2 | 2026‑11‑15 |
| D10 | Interfaz y reportes **bilingües ES/EN**, con selector de idioma | APROBADA | Posible jurado en inglés | 2026‑11‑15 |
| D11 | Repo `XxRaliugaRdzxX/Nasa-hackaton-UPQ` por SSH con deploy key del servidor (alias `github-nasa-upq`). Commits firmados por "Dan Aguilar" con el correo noreply de GitHub | APROBADA | `07` §4 | 2026‑11‑15 |
| D12 | Plazo de **más de 1 mes**: se ejecuta el plan completo de 6 semanas de `06`, incluidas las extensiones de la Fase 4 | APROBADA | — | 2026‑11‑15 |
| D13 | Licencia **MIT** para el código. Los datos de NASA y las fuentes de regiones conservan sus propias licencias | APROBADA | Permisiva y estándar en proyectos académicos | 2026‑11‑15 |
| D14 | Base del sistema = especificación "Trend Detective" del equipo: contratos `fetch_dataset`, `compute_anomalies`, `regional_series`, `trend_test`, `trend_map` y `fig_*` con sus firmas exactas, dentro del paquete `mece` | APROBADA | Herramienta parametrizada por `(dataset_id, variable, bbox, t0, t1, season)` | 2026‑11‑15 |
| D15 | Datos: el ERDDAP de la especificación (coastwatch.pfeg.noaa.gov) no responde desde el servidor. Se usa NASA directo: SST MUR25 por OPeNDAP de Earthdata Cloud (recorte en el servidor) y clorofila MODIS con earthaccess (descarga, recorte y borrado del global). ERDDAP queda como backend opcional | APROBADA | Probado: MUR25 da 36 KB en 1.4 s por día; OB.DAAC no tiene OPeNDAP en la nube y su OPeNDAP propio responde 429 | 2026‑11‑15 |
| D16 | Interfaz con nombre **Marine Ecosystem Change Explorer**, tema oscuro de la prueba de diseño y **globo 3D WebGL con SST real** (en lugar del Scattergeo ortográfico) | APROBADA | Mayor impacto visual para el hackatón | 2026‑11‑15 |
| D17 | Publicación en **nasa.cardenal-shekers.online** con un **túnel de Cloudflare propio del proyecto**, ejecutado como contenedor Docker; no se toca `/etc/cloudflared` ni RRHH | APROBADA | No requiere sudo; aísla el proyecto del servicio existente | 2026‑11‑15 |
| D18 | Clorofila: los titulares públicos usan la serie **corregida MODIS+VIIRS** (deriva de MODIS de +5 a +10 %/década detectada por el equipo). MODIS sola se muestra como "lo que habríamos concluido sin validar". Las cifras se recalculan desde el código y se reconcilian (Campeche −7.6 % en la presentación vs. −10.6 % en el notebook) | APROBADA | Resultado más defendible; validación con un segundo satélite | 2026-11-16 |
| D19 | La investigación del equipo (notebook de Colab) se **porta al paquete `mece.research`** y se reproduce en el servidor con las mismas regiones y métodos; las gráficas de la web salen de esos resultados | APROBADA | Reproducible, interactivo y actualizable | 2026-11-16 |
| D20 | Regiones: las 7 marinas y 5 cuencas del equipo son las oficiales en Análisis e Historia; los 4 casos siguen en la herramienta exploradora (vista Región) | APROBADA | — | 2026-11-16 |
| D21 | Privacidad: la web pública **no muestra nombres de integrantes ni la universidad**; a lo mucho el nombre del equipo, "Cardinals Hyperyon" | APROBADA | Decisión del responsable | 2026-11-16 |
