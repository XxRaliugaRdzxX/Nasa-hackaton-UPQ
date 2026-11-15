# Guía de contribución

Reglas comunes para que los cuatro equipos trabajen sobre el mismo repositorio sin pisarse.

## 1. Primer arranque (una vez por persona)
```bash
git clone git@github.com:XxRaliugaRdzxX/Nasa-hackaton-UPQ.git
cd Nasa-hackaton-UPQ
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env && chmod 600 .env    # poner tu EARTHDATA_TOKEN
mece check-config                         # valida la configuración
mece check-access                         # prueba acceso a NASA (no imprime secretos)
```
Requisitos de la cuenta Earthdata: ver `docs/02_productos_datos.md` §4.1. Hay que aprobar **NASA GESDISC DATA ARCHIVE**.

## 2. Ramas
- `main` siempre funciona. **No se hace push directo:** todo entra por Pull Request.
- Las ramas se nombran `<equipo>/<tema-corto>`. Por ejemplo `e1/descarga-mur25`, `e2/mann-kendall`, `e3/mapa-folium`, `e4/plantilla-pdf`.
- Un PR por tarea del plan (`docs/06_plan_trabajo_riesgos.md`), citando su número: "Tarea 1.4".

## 3. Commits
- En español e imperativo, con un prefijo:
  - `feat:` funcionalidad nueva
  - `fix:` corrección
  - `docs:` documentación
  - `test:` pruebas
  - `data:` regiones o configuración de productos
  - `refactor:`
  - `chore:` mantenimiento
- Ejemplo: `feat: descarga incremental de MUR25 con catálogo SQLite`.

## 4. Antes de abrir un PR
```bash
ruff check src tests        # estilo
ruff format src tests       # formato automático
pytest                      # todas las pruebas en verde
```
La CI de GitHub ejecuta lo mismo y un PR en rojo no se fusiona.

## 5. Convenciones de código
| Elemento | Convención | Ejemplo |
|---|---|---|
| Módulos y funciones | `snake_case`, en inglés | `compute_anomalies()` |
| Clases | `PascalCase` | `TrendResult` |
| Comentarios y docstrings | Español | — |
| Nombres internos de variables ambientales | `chlorophyll`, `sst`, `precipitation`, `runoff` | — |
| Nombres de productos | La clave de `config/products.yaml` | `mur25_sst_daily` |
| Regiones | El ID de `config/regions.yaml` | `tabasco_coast` |
| Fechas | ISO 8601 en UTC | `2025-09-01`; periodo mensual `2025-09` |
| Unidades en código | En sufijo | `sst_degc`, `precip_mm_month` |

- **Ningún valor fijo de producto, periodo o umbral en el código:** se leen de `config/`.
- Los notebooks importan `mece` y no copian funciones. Se nombran `NN_tema_autor.ipynb`, por ejemplo `03_correlaciones_ana.ipynb`, y se guardan **sin salidas pesadas**.

## 6. Datos
- **Nunca se versionan datos descargados ni procesados.** `.gitignore` lo impide.
- Lo único que se versiona en `data/` son los polígonos de `data/spatial/regions/`. Se regeneran con `mece regions build` y cualquier cambio se revisa con la figura `docs/figuras/regiones_control.png`.
- Las credenciales van solo en `.env`. Si alguien sube un token por error, se avisa de inmediato y se revoca en Earthdata.

## 7. Decisiones
Cualquier cambio de producto, periodo, método estadístico o arquitectura se registra primero en `docs/decisiones.md` como **PROPUESTA** y se implementa cuando está **APROBADA**.
