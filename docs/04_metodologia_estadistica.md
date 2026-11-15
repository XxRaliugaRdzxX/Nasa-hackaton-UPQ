# 04 · Metodología estadística

Objetivo: responder cuatro preguntas, **qué cambia, dónde, cuánto y si es significativo**, sin confundir magnitud con significancia ni correlación con causa.

Todos los parámetros (α, periodos, umbrales) viven en `config/analysis.yaml` y se imprimen en cada reporte.

## 0. Parámetros por defecto (propuestos)

| Parámetro | Valor | Justificación |
|---|---|---|
| Periodo climatológico de referencia | **2003‑01 → 2022‑12** (20 años) | Años completos comunes a las tres variables. No hay registro satelital de 30 años como pide la OMM, así que se declara la limitación. |
| Ventana de tendencia: clorofila y SST | 2003‑01 → 2025‑12 | Años completos. Cierra antes de que la deriva de Aqua se acentúe en 2026. |
| Ventana de tendencia: precipitación | 2003‑01 → 2025‑09 | Fin de IMERG Final V07. Se puede ampliar a 2001‑01 para la serie larga. |
| Ventana común para correlaciones | 2003‑01 → 2025‑09 | Periodo compartido por todas las variables. |
| Nivel de significancia | α = 0.05 | Convención. Siempre se reporta además el valor p exacto. |
| FDR para mapas | α_FDR = 0.10 (Benjamini‑Hochberg) | Recomendación de Wilks (2016) para campos espacialmente correlacionados. |
| Cobertura mínima por mes y región | ≥ 30 % de píxeles válidos | Por debajo, el promedio está sesgado por nubes y el mes se marca faltante. |
| Datos mínimos por píxel para tendencia | ≥ 70 % de meses válidos **y** cada mes calendario con ≥ 10 años | Sin esto, el píxel se marca "datos insuficientes". |
| Datos NRT y provisionales | **Excluidos** de tendencias y climatologías | Solo se muestran en el monitoreo. |

## A. Construcción de la serie regional
1. **Promedio espacial ponderado por área (cos φ)** de los píxeles válidos dentro del polígono.
2. **Clorofila:** su distribución es log‑normal (Campbell, 1995). Por eso se promedia `log10(chl)` y se reporta la **media geométrica** `10^mean(log10 chl)`.
3. **Precipitación:** lámina media en mm/mes sobre la cuenca. Opcionalmente se calcula el volumen en km³/mes.
4. Para cada mes se guardan la **cobertura** (fracción válida), la mediana, la desviación estándar espacial y el mínimo y máximo.

## B. Análisis exploratorio
- Descriptivos de la serie completa: media, mediana, desviación estándar, mínimo y máximo, con la fecha en que ocurrieron.
- **Climatología mensual:** media y percentiles 10, 50 y 90 por mes calendario en el periodo de referencia, para mostrar el ciclo estacional.
- Variabilidad interanual: medias anuales (solo años con ≥ 10 meses válidos) y desviación estándar entre años.
- Gráficas:
  - serie con su climatología de fondo;
  - matriz año × mes (heatmap);
  - boxplot por mes.

## C. Anomalías
- `anomalía(t) = x(t) − clim(mes(t))`
  - **SST:** en °C.
  - **Precipitación:** en mm y en % de la climatología (`100·anom/clim`).
  - **Clorofila:** en log10, que se traduce a factor (`10^anom`; por ejemplo ×1.3 = 30 % por encima de lo normal).
- Anomalía estandarizada: `z = anom / σ(mes)`. Con ella se ordenan las "regiones con mayores anomalías".
- Categorías para el monitor (se aplican igual a anomalías positivas y negativas):
  - |z| < 1: normal;
  - 1 ≤ |z| < 2: inusual;
  - |z| ≥ 2: extremo.

## D. Tendencia: un protocolo, tres estimadores
La tendencia se estima **sobre la serie de anomalías**, que ya no tiene estacionalidad. El Mann‑Kendall estacional se aplica sobre la serie original.

### D.1 Regresión lineal (OLS) con errores robustos
- Modelo: `anom(t) = β0 + β1·t + ε`, con t en años decimales.
- **Errores estándar HAC (Newey‑West)**, con un rezago automático de 12 meses como máximo. OLS clásico supone residuos independientes, cosa que no se cumple en series ambientales mensuales. Si se ignora, el valor p sale demasiado pequeño.
- Se reportan:
  - la pendiente **β1×10**, en °C/década, mg m⁻³/década o mm/mes/década;
  - el **IC 95 %**;
  - el **R²**;
  - el **valor p**.
- Para clorofila, la regresión se hace sobre log10 y se reporta como **%/década**: `(10^(10·β1) − 1)·100`.

### D.2 Mann‑Kendall estacional (Hirsch et al., 1982)
- Hace la prueba S de Mann‑Kendall para cada mes calendario por separado y suma los resultados. Así detecta una tendencia monotónica **sin que influya el ciclo estacional** y sin suponer que la tendencia es lineal ni que los datos son normales.
- **Autocorrelación:** se usa la versión con covarianza entre estaciones, `pymannkendall.correlated_seasonal_test`. Como chequeo de sensibilidad se aplica también **Hamed‑Rao modificado** sobre las anomalías. Si las dos pruebas no coinciden, el resultado se marca "**sensible a supuestos**".
- Se reportan Z, el valor p, la τ de Kendall y la dirección (creciente, decreciente o sin tendencia).

### D.3 Pendiente de Sen (estacional)
- Es la mediana de las pendientes entre pares del mismo mes calendario. Resiste los valores atípicos, como un huracán o un evento de lluvia extremo.
- Se reporta la pendiente por década con su IC 95 % no paramétrico.

### D.4 Revisión previa de autocorrelación
- Se calcula la función de autocorrelación (ACF) de los residuos, se reporta la autocorrelación de rezago 1 (r₁) y se aplica la prueba de Ljung‑Box.
- El reporte incluye r₁ y el **tamaño efectivo de muestra** `n_eff = n·(1−r₁)/(1+r₁)`, para que se entienda cuánta información independiente hay realmente.

### D.5 Cómo se combinan (regla de decisión que verá el usuario)
| Situación | Mensaje |
|---|---|
| MK estacional significativo **y** el IC de Sen no contiene 0 **y** el signo coincide con OLS | **Tendencia significativa** (creciente/decreciente) |
| Solo una de las pruebas es significativa | **Evidencia débil o sensible al método** |
| Ninguna es significativa | **Sin tendencia detectable en el periodo.** No es lo mismo que "no hay cambio", y se aclara. |
| Menos de 10 años de datos válidos | **Datos insuficientes** |

**Magnitud y significancia se muestran siempre por separado.** Una pendiente grande puede no ser significativa porque hay mucho ruido, y una pequeña puede serlo porque la serie es larga y estable.

**Cambio total:** `Δ = pendiente × longitud del periodo`, con su IC (por ejemplo, "+0.45 °C en 23 años, IC 95 %: 0.30–0.60").

## E. Tendencias por píxel (mapas)
1. Se usa la misma ventana y los mismos umbrales de datos que en D.
2. **Implementación vectorizada en numpy** de Sen y de MK con corrección Hamed‑Rao, para recorrer unos 135 000 píxeles de 4 km en minutos en lugar de horas. Se valida contra `pymannkendall` en 200 píxeles al azar como prueba automática en `tests/`.
3. Corrección por **comparaciones múltiples con FDR Benjamini‑Hochberg** (α_FDR = 0.10) sobre todos los píxeles válidos.
4. Cada píxel queda en una de cinco clases:
   - **creciente significativa**;
   - **decreciente significativa**;
   - **no significativa**, con la pendiente en color atenuado y textura punteada;
   - **datos insuficientes**, en gris;
   - **tierra o fuera de región**, transparente.
5. Para comparar la clorofila con la SST, el análisis por píxel conjunto se hace en una malla común de 0.25°. La clorofila se promedia (`coarsen`) a 0.25° antes de calcular la tendencia, así las dos variables miden lo mismo a la misma escala.

## F. Correlaciones entre variables
Pares: precipitación (cuenca) ↔ clorofila (mar receptor); precipitación ↔ SST; clorofila ↔ SST. Todos en la misma región y la ventana común.

1. **Preparación:** se usan anomalías, sin la tendencia lineal y con la clorofila en log10. Así no se correlacionan ni la estacionalidad ni dos tendencias que solo coinciden en el tiempo.
2. **Pearson** (relación lineal) y **Spearman** (relación monotónica, robusta a atípicos).
3. **Correlación cruzada** con la precipitación por delante, en desfases de 0 a 6 meses.
4. **Significancia:**
   - El tamaño efectivo de muestra se calcula con la fórmula de Bretherton et al. (1999), a partir de la autocorrelación de ambas series.
   - Al probar siete desfases se aplica FDR sobre ellos.
   - Se reporta el IC 95 % de r por bootstrap en bloques de 12 meses.
5. **Correlación por estación** (opcional): una correlación separada para la temporada de lluvias (jun–oct) y para la seca, porque el aporte fluvial domina en la primera.
6. **Lenguaje obligatorio** en la interfaz y en los reportes: "asociación estadística", nunca "causa". Se acompaña de la hipótesis física que **podría** explicarla, rotulada como hipótesis.

## G. Tres capas de texto en los reportes
Los reportes separan tres tipos de afirmación, cada uno con su propio estilo visual:
1. **Resultado estadístico:** número, IC y valor p. Se genera automáticamente.
2. **Interpretación:** texto a partir de reglas basadas en el resultado y el contexto, por ejemplo "consistente con…".
3. **Hipótesis:** mecanismos posibles, explícitamente no demostrados.

## H. Validación del método (Fase 1)
- Comparar la serie regional del Golfo con **Giovanni**, misma variable y misma caja. La diferencia esperada es menor a 2 % en la media y se documenta.
- Comparar MUR25 con MODIS NSST en el periodo común: sesgo y RMSE por región.
- Pruebas unitarias con series sintéticas de tendencia conocida y ruido AR(1). Los estimadores deben recuperar la pendiente y la tasa de falsos positivos debe quedar cerca de α.

## Referencias
- Benjamini, Y., & Hochberg, Y. (1995). *J. R. Stat. Soc. B*, 57(1), 289–300.
- Bretherton, C. S., et al. (1999). The effective number of spatial degrees of freedom of a time‑varying field. *J. Climate*, 12, 1990–2009.
- Campbell, J. W. (1995). The lognormal distribution as a model for bio‑optical variability in the sea. *JGR*, 100(C7).
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann‑Kendall trend test for autocorrelated data. *J. Hydrology*, 204.
- Hirsch, R. M., Slack, J. R., & Smith, R. A. (1982). *Water Resources Research*, 18(1).
- Newey, W. K., & West, K. D. (1987). *Econometrica*, 55(3).
- Sen, P. K. (1968). *JASA*, 63(324).
- Wilks, D. S. (2016). *BAMS*, 97(12), 2263–2273.
