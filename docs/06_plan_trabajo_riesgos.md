# 06 · Plan de desarrollo, responsables, complejidad y riesgos

Complejidad: **S** = menos de 1 día‑persona · **M** = 1–3 días · **L** = 3–6 días.
Calendario: plazo de más de 1 mes (D12), así que se sigue el plan de 6 semanas completo, incluidas las extensiones de la Fase 4.

Equipos:
- **E1** Adquisición y automatización
- **E2** Procesamiento y estadística
- **E3** Mapas y dashboard
- **E4** Integración y reportes

## Fase 0 · Cimientos (semana 0, en paralelo)
| # | Tarea | Resp. | Cx | Entregable |
|---|---|---|---|---|
| 0.1 | Repositorio, estructura, `pyproject`, ruff, pytest y CI | E4 | S | Repo con CI en verde |
| 0.2 | Cuentas Earthdata y autorización de GES DISC para cada integrante | Todos | S | Login probado con `earthaccess.login()` |
| 0.3 | `config/products.yaml` con los productos de `02_productos_datos.md` | E1 | S | YAML validado |
| 0.4 | Polígonos de las regiones (IHO, INEGI, HydroBASINS) en GeoJSON | E2 + E3 | M | `data/spatial/regions/*.geojson` y una figura de control |
| 0.5 | Convenciones: ramas, nombres y plantilla de PR | E4 | S | `docs/CONTRIBUTING.md` |

## Fase 1 · Flujo completo con UNA variable: SST con MUR25 (semanas 1–2)
Primero se cierra el ciclo descarga → serie → tendencia → mapa con una variable. Las demás se agregan reutilizando ese molde.

| # | Tarea | Resp. | Cx | Depende de |
|---|---|---|---|---|
| 1.1 | `acquisition`: buscar y descargar MUR25, recortar, catálogo SQLite, idempotencia | E1 | M | 0.2, 0.3 |
| 1.2 | `processing`: lector MUR25, K→°C, agregación mensual, cubo regional | E2 | M | 1.1 |
| 1.3 | `geospatial`: máscaras `regionmask`, serie ponderada y cobertura | E2 | M | 0.4, 1.2 |
| 1.4 | `statistics`: climatología, anomalías, OLS‑HAC, MK estacional, Sen, ACF | E2 | L | 1.3 |
| 1.5 | Pruebas con series sintéticas y validación contra Giovanni | E2 + E4 | M | 1.4 |
| 1.6 | Mapa básico: PNG + bounds y página Streamlit mínima con folium | E3 | M | 1.2 |
| 1.7 | Notebook demostrativo `01_sst_gom_end_to_end.ipynb` | E2 | S | 1.4 |

**Hito 1:** tendencia de SST del Golfo 2003–2025 con IC, validada contra Giovanni y visible en un mapa.

## Fase 1b · Clorofila y precipitación (semana 2–3)
| # | Tarea | Resp. | Cx |
|---|---|---|---|
| 1.8 | Lector y QC de MODIS L3m CHL, promedio log10 y bandera costera | E2 | M |
| 1.9 | Lector de IMERG (HDF5 `Grid`, transponer, mm/h→mm/mes), serie sobre la cuenca | E2 | M |
| 1.10 | Descarga histórica (backfill) de CHL, IMERG y NSST, con reanudación tras fallo | E1 | M |
| 1.11 | Contraste MUR25 vs MODIS NSST (sesgo y RMSE) | E2 | S |

## Fase 2 · Dashboard (semanas 3–4)
| # | Tarea | Resp. | Cx |
|---|---|---|---|
| 2.1 | Esqueleto multipágina, tema, barra lateral global y barra de frescura | E3 | M |
| 2.2 | Página 2 Condiciones: deslizador mensual, clic en píxel, series | E3 | L |
| 2.3 | Página 3 Tendencias: veredicto, tabla de métodos, gráfica | E3 + E2 | M |
| 2.4 | Tendencias por píxel vectorizadas con FDR y su capa | E2 | L |
| 2.5 | Página 4: comparar regiones y correlaciones con desfases | E3 + E2 | L |
| 2.6 | Textos de interpretación (plantillas de las tres capas) | E2 + E4 | M |

## Fase 3 · Automatización NRT (semana 4–5)
| # | Tarea | Resp. | Cx |
|---|---|---|---|
| 3.1 | `mece update`: CMR incremental, bloqueo, reintentos, bitácora `runs` | E1 | M |
| 3.2 | NRT: MODIS CHL NRT, PACE BGC NRT, IMERG Late diario y composición de 8 días | E1 + E2 | L |
| 3.3 | Lógica de reemplazo NRT → final y tabla `availability` | E1 | M |
| 3.4 | Página 1 Monitor y escritura atómica del manifest | E3 | M |
| 3.5 | Contenedor worker con supercronic | E4 | S |

## Fase 4 · Reportes y extensiones (semana 5–6)
| # | Tarea | Resp. | Cx |
|---|---|---|---|
| 4.1 | Plantilla Jinja2/WeasyPrint y figuras estáticas | E4 | L |
| 4.2 | Exportación ZIP de CSV y JSON de metadatos | E4 | S |
| 4.3 | Página 5 Reportes | E3 + E4 | M |
| 4.4 | GLDAS: verificación, escorrentía y humedad del suelo sobre las cuencas (opcional) | E1 + E2 | M |
| 4.5 | Polígonos dibujados por el usuario (opcional) | E3 | M |
| 4.6 | Indicador de turbidez costera (opcional) | E2 | M |

## Fase 5 · Despliegue y cierre (semana 6)
| # | Tarea | Resp. | Cx |
|---|---|---|---|
| 5.1 | Docker Compose, límites de memoria y volumen persistente | E4 | M |
| 5.2 | Publicación vía Cloudflare Tunnel (ver `07_despliegue.md`) | E4 | S |
| 5.3 | Pruebas finales: carga, caída de NASA, mes sin datos, credenciales vencidas | Todos | M |
| 5.4 | README, manual de usuario, guion y presentación | E4 | M |

## Ruta crítica
`0.2 → 1.1 → 1.2 → 1.3 → 1.4 → 2.3 → 3.1 → 4.1 → 5.2`

Lo que se puede adelantar en paralelo:
- E3 puede trabajar 1.6 y 2.1 con datos sintéticos desde el día 1.
- E4 puede adelantar 4.1 con un JSON de ejemplo.

## Matriz de riesgos
| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| R1 | **Aqua se apaga** durante el proyecto | Alta | Medio | La SST ya no depende de Aqua (MUR25). La clorofila NRT pasa automáticamente a PACE. El histórico 2003–2025 no se afecta. |
| R2 | **Sale IMERG V08 Final** a mitad del proyecto | Media | Medio | La versión es configurable. Se reprocesa todo (unas 6 GB, horas). Se decide contigo si se adopta antes de la entrega. |
| R3 | Sesgo de clorofila en aguas costeras turbias | Alta | Alto (científico) | Separar costa y océano, bandera de pixel, avisos en el reporte y redacción prudente |
| R4 | RAM del servidor (3.6 GB compartidos) | Media | Alto | Recortar antes de cargar, límites `mem_limit` y tendencias por píxel en bloques de latitud |
| R5 | Fallos o mantenimiento de servidores NASA, o 401 por la autorización de GES DISC | Media | Medio | Reintentos, el estado aparece en la barra de frescura, el dashboard sigue con lo último válido y hay un checklist de cuentas |
| R6 | Polígonos mal definidos (pluma y cuenca) | Media | Alto | Script reproducible, figura de control revisada por el equipo y metadatos de la fuente |
| R7 | Sobre‑interpretación (correlación como causa, tendencia corta como "cambio climático") | Media | Alto | Las tres capas de texto, avisos fijos y reglas de decisión en `04` |
| R8 | Coordinación del equipo remoto | Media | Medio | Contratos de datos (esquemas de `03` §6) definidos antes de programar, PR pequeños y CI |
| R9 | Que el despliegue afecte el servicio RRHH existente | Baja con subdominio | Alto | Ver `07`: subdominio sin downtime |
| R10 | MUR25 es interpolado y suaviza la variabilidad costera fina | Media | Bajo | Contraste con MODIS NSST a 4 km, documentado |
