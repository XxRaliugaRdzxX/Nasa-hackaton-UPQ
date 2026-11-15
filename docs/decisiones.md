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
| D09 | Publicación por **subdominio** del túnel existente, sin bajar RRHH | APROBADA | `07` §2 | 2026‑11‑15 |
| D10 | Interfaz y reportes **bilingües ES/EN**, con selector de idioma | APROBADA | Posible jurado en inglés | 2026‑11‑15 |
| D11 | Repo `XxRaliugaRdzxX/Nasa-hackaton-UPQ` por SSH con deploy key del servidor (alias `github-nasa-upq`). Commits firmados por "Dan Aguilar" con el correo noreply de GitHub | APROBADA | `07` §4 | 2026‑11‑15 |
| D12 | Plazo de **más de 1 mes**: se ejecuta el plan completo de 6 semanas de `06`, incluidas las extensiones de la Fase 4 | APROBADA | — | 2026‑11‑15 |
| D13 | Licencia **MIT** para el código. Los datos de NASA y las fuentes de regiones conservan sus propias licencias | APROBADA | Permisiva y estándar en proyectos académicos | 2026‑11‑15 |
