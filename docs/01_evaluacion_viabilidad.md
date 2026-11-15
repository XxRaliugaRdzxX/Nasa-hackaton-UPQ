# 01 · Evaluación de viabilidad científica y técnica

> Estado: **borrador para revisión del equipo** · Fecha: 2026-11-15
> Toda la información de cobertura se verificó en el catálogo oficial NASA CMR en esa fecha (ver `02_productos_datos.md`).

## 1. Veredicto

| Aspecto | Viabilidad | Comentario |
|---|---|---|
| Científica (Golfo de México, escala regional) | **Alta** | Hay más de 20 años de clorofila, SST y precipitación con cobertura completa del Golfo. |
| Científica (Costa de Tabasco / Grijalva‑Usumacinta) | **Media** | Las aguas costeras son ópticamente complejas: la clorofila satelital tiene más sesgo. La cuenca se comparte con Guatemala. |
| Técnica (Fases 1 a 3) | **Alta** | Los volúmenes son pequeños tras el recorte (unos 0.2 GB). Todo funciona con Python y en el servidor actual. |
| Técnica (Fases 4 y 5) | **Alta / Media** | Los reportes PDF y el despliegue son directos. El límite real es la RAM del servidor (3.6 GB compartidos). |
| Monitoreo casi en tiempo real | **Media** | Funciona, pero hay que tratar con cuidado el fin de misión de Aqua y la transición de IMERG a V08 (ver §2). |

**Conclusión:** el proyecto es viable y defendible. La condición es corregir varias suposiciones del planteamiento original que hoy (noviembre de 2026) ya no son ciertas o que introducirían errores científicos.

## 2. Objeciones al planteamiento original y alternativas

Estas son las decisiones que **cuestiono**. Cada una está registrada en `decisiones.md` con su estado.

### 2.1 IMERG Final V07 ya no se actualiza (crítico)
- **Hecho verificado:** `GPM_3IMERGM` V07 cubre **1998‑01‑01 → 2025‑09‑30** y la colección está cerrada. NASA detuvo la serie Final V07 porque sus insumos (GPROF y CORRA) pasan a V08. La V08 Final se anunció para "otoño de 2026" y todavía no aparece en CMR.
- **Implicaciones:**
  1. El análisis histórico de precipitación termina en **2025‑09** mientras no se publique V08.
  2. De 2025‑10 a hoy solo existen **IMERG Late/Early V07** (productos NRT). Esos meses se muestran como **"provisional"** y **no entran** en las pruebas de tendencia.
  3. Cuando se publique V08 Final, **se reprocesa el registro completo con V08** y se reemplaza V07. Nunca se concatenan versiones.
- **Diseño:** el sistema guarda `product_version` y `processing_level` (final/nrt) en cada registro. La versión de IMERG es un parámetro de configuración, no un valor fijo en el código.

### 2.2 Unidades de IMERG mensual
- El enunciado dice "mm de precipitación acumulada". En realidad, la variable `precipitation` de `GPM_3IMERGM` es una **tasa media en mm/h**.
- **Conversión obligatoria:** `mm/mes = mm/h × 24 × días_del_mes`. El producto diario Late (`GPM_3IMERGDL`) viene en mm/día. Las unidades se leerán siempre del atributo `units` del archivo, nunca se asumirán.

### 2.3 Aqua‑MODIS está al final de su vida útil
- **Hechos:** Aqua dejó de corregir su órbita en 2021. Su hora de paso por el ecuador derivó de 13:30 a unas 15:30–15:50 h en 2026. NASA anunció el fin de la misión para agosto de 2026. Aun así, CMR muestra datos NRT diarios normales hasta el 2026‑11‑14, así que el instrumento sigue entregando, pero podría apagarse en cualquier momento.
- **Problema para la SST:** `MODISA_L3m_SST` es la SST **diurna** a 11 µm. Si el satélite pasa cada vez más tarde, mide en horas con más calentamiento diurno de la piel del océano. Eso puede **fabricar una tendencia de calentamiento artificial** en los últimos años. Es un error clásico que un jurado puede detectar.
- **Alternativa recomendada:** usar **GHRSST MUR25 v4.2** (NASA PO.DAAC) como SST principal para tendencias, anomalías y monitoreo. Combina varios sensores, representa la SST de "fundación" (sin ciclo diurno), no tiene huecos, cubre de 2002 a hoy con un día de latencia y **no depende de Aqua**. La SST de MODIS‑Aqua **nocturna** queda como producto de contraste y para cruces píxel a píxel con la clorofila.
- **Problema para la clorofila:** la deriva también cambia el ángulo solar. **Se propone cerrar la ventana de tendencia de clorofila en 2025‑12**, con años calendario completos de 2003 a 2025. Para la continuidad del monitoreo se agrega **PACE‑OCI** (2024‑03 → hoy, NRT activo), sin mezclarlo con MODIS en las tendencias (ver §2.4).

### 2.4 No mezclar sensores de clorofila en una misma tendencia
- MODIS‑Aqua (R2022.0) y PACE‑OCI (v3.2) tienen bandas, calibración y algoritmos distintos. Unirlos crea **saltos artificiales**.
- **Regla:** las tendencias de clorofila usan solo MODIS‑Aqua (2003–2025). PACE se usa para el monitoreo reciente. El traslape 2024–2026 sirve para cuantificar el sesgo entre sensores, que se documenta y se muestra. La serie combinada solo se construiría en una fase posterior y con un ajuste validado.

### 2.5 El versionado de MODIS no es homogéneo
- La clorofila está en **R2022.0** y la SST de MODIS en **R2019.0**. Es normal, pero debe declararse en metadatos y reportes.

### 2.6 La longitud del registro limita las conclusiones sobre clorofila
- Henson et al. (2010, *Biogeosciences*) estiman que se necesitan unos 40 años para separar una tendencia de clorofila ligada al clima de la variabilidad natural. Con 23 años, los resultados se redactan como **"tendencia observada en el periodo 2003–2025"**, sin atribuirlos al cambio climático. La plataforma debe decirlo de forma explícita.

### 2.7 Aguas costeras de Tabasco y desembocadura Grijalva‑Usumacinta
- Allí la materia orgánica disuelta y los sedimentos **sobreestiman** `chlor_a` (algoritmo OCI: OC3M + CI). Una "clorofila alta" en la pluma puede ser en parte turbidez.
- **Medidas:**
  1. Separar siempre las regiones costeras de las oceánicas.
  2. Agregar a los píxeles costeros la etiqueta "aguas ópticamente complejas".
  3. Promediar la clorofila en escala logarítmica.
  4. Agregar en una fase posterior un indicador de turbidez, como Kd_490 o Rrs(667), para distinguir sedimento de fitoplancton.
- **La cuenca Grijalva‑Usumacinta es transfronteriza (México y Guatemala).** Si la precipitación se calcula solo sobre Tabasco, se pierde la mayor parte de la cuenca alta. Se usará **HydroBASINS** (HydroSHEDS), que delimita la cuenca completa.

### 2.8 Las correlaciones se calculan sobre anomalías, no sobre datos brutos
- La lluvia, la SST y la clorofila tienen ciclos estacionales fuertes. Correlacionar las series brutas da coeficientes altos **por compartir la estación**, no porque estén relacionadas.
- **Regla:** se correlacionan anomalías sin tendencia. La significancia se corrige por autocorrelación (tamaño efectivo de muestra) y por número de desfases probados.

### 2.9 Herramientas que sobran o se postergan
| Propuesta original | Decisión | Motivo |
|---|---|---|
| n8n | **Se descarta** | Agrega un servicio más sin aportar nada: un cron dentro de un contenedor basta. |
| PostgreSQL/PostGIS | **Se posterga** | Para unos 0.2 GB de cubos y series, NetCDF + Parquet + SQLite basta y no ocupa RAM. Queda abierta la migración si crecen los usuarios o los polígonos personalizados. |
| rasterio directo | **Solo vía rioxarray** y solo para exportar GeoTIFF | El recorte por polígono se hace con `regionmask`, que es nativo de xarray y más simple. |
| GeoTIFF para mostrar capas | **PNG pre‑renderizado + GeoTIFF COG para descarga** | Leaflet muestra un PNG georreferenciado de forma instantánea, mientras que un GeoTIFF en el navegador es lento. |
| Giovanni | **Solo validación manual** | No se integra al sistema, pero sirve para comprobar series en la Fase 1. |
| GLDAS en el núcleo | **Fase 4, opcional** | Se acordó incorporarlo solo tras verificarlo. Está disponible hasta 2026‑07 (unos 4 meses de latencia). |

### 2.10 Consultas cada 30–60 minutos
- Sirven **solo para metadatos** (CMR), que son baratos. Los productos mensuales cambian una vez al mes y los NRT diarios una vez al día. Se mantiene una consulta cada hora, que descarga solo si aparece un granulo nuevo, y una ventana de reintentos.

### 2.11 Capacidad del servidor
- agui-server tiene 4 CPU y 3.6 GB de RAM, compartidos con RRHH (incluye Ollama), PostgreSQL, MySQL y MinIO, y ya usa swap. **El procesamiento debe ser incremental y ligero.** Se abre cada archivo global y se recorta a la región de interés **antes** de cargarlo en memoria (unos 0.36 % del globo). Los contenedores tendrán límites de memoria.

## 3. Lo que sí se mantiene del planteamiento
- Las tres variables principales y la complementaria (GLDAS).
- La separación entre monitoreo NRT y análisis histórico.
- El análisis por regiones, con precipitación sobre la cuenca y clorofila/SST sobre el mar.
- OLS + Mann‑Kendall estacional + Sen + FDR.
- Streamlit + Leaflet.
- La estructura de carpetas, adaptada en `03_arquitectura.md`.
- El desarrollo por fases, cerrando primero un flujo completo con una sola variable.

## Referencias clave
- Henson, S. A., et al. (2010). Detection of anthropogenic climate change in satellite records of ocean chlorophyll and productivity. *Biogeosciences*, 7, 621–640.
- Hirsch, R. M., Slack, J. R., & Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research*, 18(1).
- Wilks, D. S. (2016). "The stippling shows statistically significant grid points". *BAMS*, 97(12).
- NASA GPM, *IMERG V08 Transition Schedule*: https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule
- NASA Earthdata, *Aqua MODIS Acquisition Plan Through August 2026*: https://www.earthdata.nasa.gov/data/alerts-outages/aqua-modis-acquisition-plan-through-august-2026
