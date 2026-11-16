"""Textos de la sección de investigación (vista Análisis) en es / en / pt."""

R = {
    "es": {
        "tab_tool": "Explorador interactivo", "tab_find": "Hallazgos", "tab_trend": "Tendencias",
        "tab_maps": "Mapas por celda", "tab_series": "Series y ciclos", "tab_rivers": "Ríos y clima",
        "tab_ext": "Extremos y régimen", "tab_val": "Validación", "tab_gal": "Galería y método",
        "intro": "Investigación reproducida en el servidor a partir del código del equipo: mismas regiones, mismos "
                 "métodos, datos de la NASA. Cada número de esta sección sale de ese proceso.",
        "generated": "Resultados generados",
        "h_sst": "Calentamiento del Golfo", "h_sst_s": "SST · validado con MUR25",
        "h_chl": "Clorofila del Golfo", "h_chl_s": "serie corregida MODIS+VIIRS",
        "h_banco": "Banco de Campeche", "h_banco_s": "clorofila corregida",
        "h_rain": "Lluvia Grijalva–Usumacinta", "h_rain_s": "precipitación de la cuenca",
        "h_ext": "Meses extremadamente cálidos", "h_ext_s": "de cada 10 · antes → ahora",
        "matrix_t": "Matriz de evidencia", "matrix_s": "Qué cambia, dónde, cuánto y con qué solidez. "
        "Sólida = p < 0.05, pasa FDR y es robusta al quitar cualquier año.",
        "col_year": "Año", "col_model": "Modelo", "m_linear": "Gradual", "m_step": "Salto", "m_either": "Indistinguible",
        "col_var": "Variable", "col_where": "Dónde", "col_what": "Qué cambia", "col_how": "Cuánto (Sen, IC 95 %)",
        "col_p": "p (Hamed-Rao)", "col_q": "q (FDR)", "col_ev": "Evidencia",
        "ev_solid": "Sólida", "ev_weak": "Débil", "ev_none": "No detectada",
        "res_increase_sig": "Aumento significativo", "res_decrease_sig": "Disminución significativa",
        "res_increase_marginal": "Aumento marginal", "res_decrease_marginal": "Disminución marginal",
        "res_none": "Sin tendencia detectada",
        "v_chl": "Clorofila-a", "v_sst": "Temperatura del mar", "v_pp": "Precipitación",
        "v_chl_c": "Clorofila-a (corregida)",
        "trend_t": "Pendiente de Sen por región", "trend_s": "Barras = IC 95 %. Relleno = significativo (Hamed-Rao). "
        "Compara la clorofila de MODIS sola con la serie corregida por la deriva del sensor.",
        "modis_only": "MODIS sola", "corrected": "Corregida (MODIS+VIIRS)",
        "maps_chl_note": "Mapa de MODIS sola: incluye la deriva del sensor (ver Validación).",
        "maps_t": "Tendencias por celda de 0.25°", "maps_s": "Mann-Kendall (Hamed-Rao) en cada celda; los puntos marcan "
        "celdas significativas tras FDR 5 %.", "sig_cells": "celdas significativas",
        "series_t": "Anomalías mensuales por región", "series_s": "Gris: anomalía mensual · color: media móvil de 12 meses.",
        "region": "Región", "cycle_t": "Ciclo anual promedio 2003–2025",
        "rain_t": "Lluvia de la cuenca → clorofila de la costa", "rain_s": "Correlación de Spearman entre anomalías sin "
        "tendencia, con la lluvia de 0 a 4 meses antes. Barra llena = significativa tras FDR. El último par es un "
        "control negativo.", "lag": "desfase (meses)", "control": "control",
        "rain_tr_t": "Tendencia de la lluvia por cuenca",
        "sstchl_t": "Agua más caliente, menos clorofila", "sstchl_s": "Correlación SST–clorofila (anomalías sin tendencia).",
        "reg_t": "¿Qué explica la clorofila? Regresión múltiple", "reg_s": "Coeficientes estandarizados (β) con errores "
        "HAC. Negritas = significativo tras FDR. Factores: SST, lluvia con su desfase, El Niño (ONI) y tiempo.",
        "attr_t": "Atribución de la tendencia de clorofila", "attr_s": "Aporte de cada factor a la tendencia (%/década).",
        "ext_t": "Probabilidad de meses extremos", "ext_s": "Regresión logística: mes muy cálido (SST > p90 de "
        "2003–2012) y mes con muy poca clorofila (< p10).",
        "regime_t": "¿Cambio gradual o salto?", "regime_s": "Prueba de Pettitt y comparación por BIC entre línea "
        "recta y escalón, sobre medias anuales.",
        "seas_t": "Tendencia por estación del año", "seas_s": "Valores en negrita: significativos tras FDR (q < 0.05).",
        "anova_t": "Anomalía media por periodo (ANOVA)",
        "drift_t": "Deriva del sensor MODIS frente a VIIRS", "drift_s": "Diferencia de clorofila MODIS−VIIRS (media "
        "móvil de 12 meses). Una diferencia que crece es deriva del instrumento, no un cambio del océano.",
        "drift_tab": "Resultado por región", "flh_t": "Fluorescencia (nFLH) y VIIRS como testigos",
        "mur_t": "SST validada con un producto independiente (MUR25)", "mur_s": "MUR25 es un análisis multisensor que no "
        "depende de Aqua: confirma el calentamiento de la SST diurna de MODIS.",
        "rob_t": "Robustez: quitar un año a la vez", "rob_s": "Clorofila (MODIS sola) en las regiones con p < 0.10: porcentaje de las 23 submuestras en que la "
        "tendencia sigue siendo significativa.",
        "weath_t": "¿Cuántos años hacen falta para detectar la tendencia?", "weath_s": "Weatherhead et al. (1998): "
        "95 % de confianza y 90 % de probabilidad.",
        "years_needed": "años necesarios", "years_have": "años disponibles",
        "gal_t": "Figuras originales del equipo", "gal_s": "Toca una figura para verla en grande.",
        "figs": [
            ("fig01_anomalias_regiones.jpg", "Anomalías de clorofila (%) y SST (°C) en las 7 regiones, 2003–2025."),
            ("fig02_pendientes_sen.jpg", "Pendientes de Sen con IC 95 % (Hamed-Rao)."),
            ("fig03_ciclo_anual.jpg", "Ciclo anual promedio de clorofila y SST por región."),
            ("fig04_lluvia_clorofila_desfase.jpg", "Lluvia de la cuenca frente a clorofila costera según el desfase."),
            ("fig05_tendencia_por_estacion.jpg", "Tendencias por estación del año."),
            ("fig06_mapas_tendencia.jpg", "Mapas de tendencia por celda de 0.25° con FDR."),
            ("fig07_probabilidad_extremos.jpg", "Probabilidad de meses extremos 2003–2025."),
            ("fig08_regresion_multiple.jpg", "Coeficientes de la regresión múltiple."),
        ],
        "method_t": "Método", "method": [
            "Datos mensuales 2003–2025 (276 meses): MODIS-Aqua L3m clorofila R2022.0 y SST diurna R2019.0 "
            "(calidad ≤ 1), GPM IMERG Final V07 (hasta 2025-09), VIIRS-SNPP clorofila (2012+), nFLH y MUR25.",
            "7 regiones marinas (cajas ∩ polígono GCOOS del Golfo) y 5 cuencas (USGS HUC2 para el Mississippi).",
            "Medias espaciales ponderadas por cos(lat); clorofila en log10 (media geométrica); meses con < 25 % de "
            "píxeles válidos se descartan. Anomalías respecto a la climatología del mismo mes.",
            "Tendencia: pendiente de Sen con IC de Gilbert usando la varianza corregida de Hamed-Rao; Mann-Kendall "
            "clásico, Hamed-Rao y estacional; regresión con errores Newey-West; FDR Benjamini-Hochberg.",
            "Correlaciones de Spearman sin tendencia con n efectivo de Bretherton; regresión múltiple con El Niño (ONI); "
            "bootstrap por bloques de 12 meses; Pettitt + BIC; Weatherhead.",
        ],
        "limits_t": "Limitaciones", "limits": [
            "En aguas costeras turbias el algoritmo OCI puede confundir sedimentos y materia orgánica disuelta con clorofila.",
            "MODIS-Aqua deriva con la edad de su órbita; por eso los titulares de clorofila usan la serie corregida con VIIRS.",
            "La clorofila es biomasa superficial, no productividad. Correlación no implica causalidad.",
            "23 años no bastan para atribuir una tendencia de clorofila al cambio climático (Weatherhead).",
            "IMERG Final V07 termina en septiembre de 2025; la versión 8 aún no se publica.",
        ],
        "dl_t": "Descargar resultados", "dl_json": "Resultados (JSON)", "dl_series": "Series mensuales (CSV)",
        "not_ready": "La investigación se está reproduciendo en el servidor con los datos de la NASA. Esta sección "
                     "se completa sola en cuanto terminen las descargas y el cálculo.",
        "corr_note": "Nota de reconciliación: la presentación del equipo citaba −7.6 %/década para el Banco de Campeche tras "
                     "la corrección; el cálculo reproducido da",
    },
    "en": {
        "tab_tool": "Interactive explorer", "tab_find": "Findings", "tab_trend": "Trends",
        "tab_maps": "Cell maps", "tab_series": "Series & cycles", "tab_rivers": "Rivers & climate",
        "tab_ext": "Extremes & regime", "tab_val": "Validation", "tab_gal": "Gallery & method",
        "intro": "Research reproduced on the server from the team's code: same regions, same methods, NASA data. "
                 "Every number in this section comes from that process.",
        "generated": "Results generated",
        "h_sst": "Gulf warming", "h_sst_s": "SST · validated with MUR25",
        "h_chl": "Gulf chlorophyll", "h_chl_s": "corrected MODIS+VIIRS series",
        "h_banco": "Campeche Bank", "h_banco_s": "corrected chlorophyll",
        "h_rain": "Grijalva–Usumacinta rain", "h_rain_s": "basin precipitation",
        "h_ext": "Extremely hot months", "h_ext_s": "out of 10 · before → now",
        "matrix_t": "Evidence matrix", "matrix_s": "What changes, where, how much and how solidly. Solid = p < 0.05, "
        "passes FDR and is robust to removing any single year.",
        "col_year": "Year", "col_model": "Model", "m_linear": "Gradual", "m_step": "Jump", "m_either": "Indistinguishable",
        "col_var": "Variable", "col_where": "Where", "col_what": "What changes", "col_how": "How much (Sen, 95% CI)",
        "col_p": "p (Hamed-Rao)", "col_q": "q (FDR)", "col_ev": "Evidence",
        "ev_solid": "Solid", "ev_weak": "Weak", "ev_none": "Not detected",
        "res_increase_sig": "Significant increase", "res_decrease_sig": "Significant decrease",
        "res_increase_marginal": "Marginal increase", "res_decrease_marginal": "Marginal decrease",
        "res_none": "No trend detected",
        "v_chl": "Chlorophyll-a", "v_sst": "Sea temperature", "v_pp": "Precipitation",
        "v_chl_c": "Chlorophyll-a (corrected)",
        "trend_t": "Sen's slope by region", "trend_s": "Bars = 95% CI. Filled = significant (Hamed-Rao). Compares "
        "MODIS-only chlorophyll with the series corrected for sensor drift.",
        "modis_only": "MODIS only", "corrected": "Corrected (MODIS+VIIRS)",
        "maps_chl_note": "MODIS-only map: it includes sensor drift (see Validation).",
        "maps_t": "Trends per 0.25° cell", "maps_s": "Mann-Kendall (Hamed-Rao) in each cell; dots mark cells significant "
        "after 5% FDR.", "sig_cells": "significant cells",
        "series_t": "Monthly anomalies by region", "series_s": "Grey: monthly anomaly · color: 12-month moving average.",
        "region": "Region", "cycle_t": "Average annual cycle 2003–2025",
        "rain_t": "Basin rain → coastal chlorophyll", "rain_s": "Spearman correlation between detrended anomalies, rain "
        "0 to 4 months earlier. Filled bar = significant after FDR. The last pair is a negative control.",
        "lag": "lag (months)", "control": "control",
        "rain_tr_t": "Rain trend by basin",
        "sstchl_t": "Warmer water, less chlorophyll", "sstchl_s": "SST–chlorophyll correlation (detrended anomalies).",
        "reg_t": "What explains chlorophyll? Multiple regression", "reg_s": "Standardized coefficients (β) with HAC errors. "
        "Bold = significant after FDR. Factors: SST, lagged rain, El Niño (ONI) and time.",
        "attr_t": "Attribution of the chlorophyll trend", "attr_s": "Contribution of each factor to the trend (%/decade).",
        "ext_t": "Probability of extreme months", "ext_s": "Logistic regression: very hot month (SST > p90 of 2003–2012) "
        "and very low-chlorophyll month (< p10).",
        "regime_t": "Gradual change or jump?", "regime_s": "Pettitt test and BIC comparison between a straight line and a "
        "step, on annual means.",
        "seas_t": "Trend by season", "seas_s": "Bold values: significant after FDR (q < 0.05).",
        "anova_t": "Mean anomaly by period (ANOVA)",
        "drift_t": "MODIS sensor drift against VIIRS", "drift_s": "MODIS−VIIRS chlorophyll difference (12-month moving "
        "average). A growing difference is instrument drift, not an ocean change.",
        "drift_tab": "Result by region", "flh_t": "Fluorescence (nFLH) and VIIRS as witnesses",
        "mur_t": "SST validated with an independent product (MUR25)", "mur_s": "MUR25 is a multi-sensor analysis that "
        "does not depend on Aqua: it confirms the warming in MODIS daytime SST.",
        "rob_t": "Robustness: leave one year out", "rob_s": "Chlorophyll (MODIS only) in regions with p < 0.10: share of the 23 subsamples in which the trend remains significant.",
        "weath_t": "How many years are needed to detect the trend?", "weath_s": "Weatherhead et al. (1998): 95% confidence "
        "and 90% probability.",
        "years_needed": "years needed", "years_have": "years available",
        "gal_t": "The team's original figures", "gal_s": "Tap a figure to enlarge it.",
        "figs": [
            ("fig01_anomalias_regiones.jpg", "Chlorophyll (%) and SST (°C) anomalies in the 7 regions, 2003–2025."),
            ("fig02_pendientes_sen.jpg", "Sen's slopes with 95% CI (Hamed-Rao)."),
            ("fig03_ciclo_anual.jpg", "Average annual cycle of chlorophyll and SST by region."),
            ("fig04_lluvia_clorofila_desfase.jpg", "Basin rain versus coastal chlorophyll by lag."),
            ("fig05_tendencia_por_estacion.jpg", "Trends by season."),
            ("fig06_mapas_tendencia.jpg", "Trend maps per 0.25° cell with FDR."),
            ("fig07_probabilidad_extremos.jpg", "Probability of extreme months 2003–2025."),
            ("fig08_regresion_multiple.jpg", "Multiple regression coefficients."),
        ],
        "method_t": "Method", "method": [
            "Monthly data 2003–2025 (276 months): MODIS-Aqua L3m chlorophyll R2022.0 and daytime SST R2019.0 (quality ≤ 1), "
            "GPM IMERG Final V07 (to 2025-09), VIIRS-SNPP chlorophyll (2012+), nFLH and MUR25.",
            "7 marine regions (boxes ∩ GCOOS Gulf polygon) and 5 basins (USGS HUC2 for the Mississippi).",
            "Spatial means weighted by cos(lat); chlorophyll in log10 (geometric mean); months with < 25% valid pixels "
            "are discarded. Anomalies relative to the same-month climatology.",
            "Trend: Sen's slope with Gilbert CI using Hamed-Rao corrected variance; classic, Hamed-Rao and seasonal "
            "Mann-Kendall; regression with Newey-West errors; Benjamini-Hochberg FDR.",
            "Detrended Spearman correlations with Bretherton effective n; multiple regression with El Niño (ONI); "
            "12-month block bootstrap; Pettitt + BIC; Weatherhead.",
        ],
        "limits_t": "Limitations", "limits": [
            "In turbid coastal waters the OCI algorithm can confuse sediment and dissolved organic matter with chlorophyll.",
            "MODIS-Aqua drifts as its orbit ages; that is why chlorophyll headlines use the VIIRS-corrected series.",
            "Chlorophyll is surface biomass, not productivity. Correlation does not imply causation.",
            "23 years are not enough to attribute a chlorophyll trend to climate change (Weatherhead).",
            "IMERG Final V07 ends in September 2025; version 8 is not yet published.",
        ],
        "dl_t": "Download results", "dl_json": "Results (JSON)", "dl_series": "Monthly series (CSV)",
        "not_ready": "The research is being reproduced on the server with NASA data. This section fills in on its own "
                     "as soon as downloads and computation finish.",
        "corr_note": "Reconciliation note: the team's presentation cited −7.6%/decade for the Campeche Bank after "
                     "correction; the reproduced computation gives",
    },
    "pt": {
        "tab_tool": "Explorador interativo", "tab_find": "Descobertas", "tab_trend": "Tendências",
        "tab_maps": "Mapas por célula", "tab_series": "Séries e ciclos", "tab_rivers": "Rios e clima",
        "tab_ext": "Extremos e regime", "tab_val": "Validação", "tab_gal": "Galeria e método",
        "intro": "Pesquisa reproduzida no servidor a partir do código da equipe: mesmas regiões, mesmos métodos, dados "
                 "da NASA. Cada número desta seção sai desse processo.",
        "generated": "Resultados gerados",
        "h_sst": "Aquecimento do Golfo", "h_sst_s": "TSM · validado com MUR25",
        "h_chl": "Clorofila do Golfo", "h_chl_s": "série corrigida MODIS+VIIRS",
        "h_banco": "Banco de Campeche", "h_banco_s": "clorofila corrigida",
        "h_rain": "Chuva Grijalva–Usumacinta", "h_rain_s": "precipitação da bacia",
        "h_ext": "Meses extremamente quentes", "h_ext_s": "a cada 10 · antes → agora",
        "matrix_t": "Matriz de evidências", "matrix_s": "O que muda, onde, quanto e com que solidez. Sólida = p < 0,05, "
        "passa no FDR e é robusta ao retirar qualquer ano.",
        "col_year": "Ano", "col_model": "Modelo", "m_linear": "Gradual", "m_step": "Salto", "m_either": "Indistinguível",
        "col_var": "Variável", "col_where": "Onde", "col_what": "O que muda", "col_how": "Quanto (Sen, IC 95 %)",
        "col_p": "p (Hamed-Rao)", "col_q": "q (FDR)", "col_ev": "Evidência",
        "ev_solid": "Sólida", "ev_weak": "Fraca", "ev_none": "Não detectada",
        "res_increase_sig": "Aumento significativo", "res_decrease_sig": "Diminuição significativa",
        "res_increase_marginal": "Aumento marginal", "res_decrease_marginal": "Diminuição marginal",
        "res_none": "Sem tendência detectada",
        "v_chl": "Clorofila-a", "v_sst": "Temperatura do mar", "v_pp": "Precipitação",
        "v_chl_c": "Clorofila-a (corrigida)",
        "trend_t": "Declive de Sen por região", "trend_s": "Barras = IC 95 %. Preenchido = significativo (Hamed-Rao). "
        "Compara a clorofila só do MODIS com a série corrigida pela deriva do sensor.",
        "modis_only": "Só MODIS", "corrected": "Corrigida (MODIS+VIIRS)",
        "maps_chl_note": "Mapa só do MODIS: inclui a deriva do sensor (ver Validação).",
        "maps_t": "Tendências por célula de 0,25°", "maps_s": "Mann-Kendall (Hamed-Rao) em cada célula; os pontos marcam "
        "células significativas após FDR 5 %.", "sig_cells": "células significativas",
        "series_t": "Anomalias mensais por região", "series_s": "Cinza: anomalia mensal · cor: média móvel de 12 meses.",
        "region": "Região", "cycle_t": "Ciclo anual médio 2003–2025",
        "rain_t": "Chuva da bacia → clorofila da costa", "rain_s": "Correlação de Spearman entre anomalias sem tendência, "
        "com a chuva de 0 a 4 meses antes. Barra cheia = significativa após FDR. O último par é um controle negativo.",
        "lag": "defasagem (meses)", "control": "controle",
        "rain_tr_t": "Tendência da chuva por bacia",
        "sstchl_t": "Água mais quente, menos clorofila", "sstchl_s": "Correlação TSM–clorofila (anomalias sem tendência).",
        "reg_t": "O que explica a clorofila? Regressão múltipla", "reg_s": "Coeficientes padronizados (β) com erros HAC. "
        "Negrito = significativo após FDR. Fatores: TSM, chuva defasada, El Niño (ONI) e tempo.",
        "attr_t": "Atribuição da tendência de clorofila", "attr_s": "Contribuição de cada fator para a tendência (%/década).",
        "ext_t": "Probabilidade de meses extremos", "ext_s": "Regressão logística: mês muito quente (TSM > p90 de "
        "2003–2012) e mês com muito pouca clorofila (< p10).",
        "regime_t": "Mudança gradual ou salto?", "regime_s": "Teste de Pettitt e comparação por BIC entre reta e degrau, "
        "sobre médias anuais.",
        "seas_t": "Tendência por estação do ano", "seas_s": "Valores em negrito: significativos após FDR (q < 0,05).",
        "anova_t": "Anomalia média por período (ANOVA)",
        "drift_t": "Deriva do sensor MODIS frente ao VIIRS", "drift_s": "Diferença de clorofila MODIS−VIIRS (média móvel "
        "de 12 meses). Uma diferença que cresce é deriva do instrumento, não mudança do oceano.",
        "drift_tab": "Resultado por região", "flh_t": "Fluorescência (nFLH) e VIIRS como testemunhas",
        "mur_t": "TSM validada com um produto independente (MUR25)", "mur_s": "O MUR25 é uma análise multissensor que não "
        "depende do Aqua: confirma o aquecimento da TSM diurna do MODIS.",
        "rob_t": "Robustez: retirar um ano por vez", "rob_s": "Clorofila (só MODIS) nas regiões com p < 0,10: porcentagem das 23 subamostras em que a tendência continua significativa.",
        "weath_t": "Quantos anos são necessários para detectar a tendência?", "weath_s": "Weatherhead et al. (1998): "
        "95 % de confiança e 90 % de probabilidade.",
        "years_needed": "anos necessários", "years_have": "anos disponíveis",
        "gal_t": "Figuras originais da equipe", "gal_s": "Toque em uma figura para ampliá-la.",
        "figs": [
            ("fig01_anomalias_regiones.jpg", "Anomalias de clorofila (%) e TSM (°C) nas 7 regiões, 2003–2025."),
            ("fig02_pendientes_sen.jpg", "Declives de Sen com IC 95 % (Hamed-Rao)."),
            ("fig03_ciclo_anual.jpg", "Ciclo anual médio de clorofila e TSM por região."),
            ("fig04_lluvia_clorofila_desfase.jpg", "Chuva da bacia frente à clorofila costeira segundo a defasagem."),
            ("fig05_tendencia_por_estacion.jpg", "Tendências por estação do ano."),
            ("fig06_mapas_tendencia.jpg", "Mapas de tendência por célula de 0,25° com FDR."),
            ("fig07_probabilidad_extremos.jpg", "Probabilidade de meses extremos 2003–2025."),
            ("fig08_regresion_multiple.jpg", "Coeficientes da regressão múltipla."),
        ],
        "method_t": "Método", "method": [
            "Dados mensais 2003–2025 (276 meses): MODIS-Aqua L3m clorofila R2022.0 e TSM diurna R2019.0 (qualidade ≤ 1), "
            "GPM IMERG Final V07 (até 2025-09), VIIRS-SNPP clorofila (2012+), nFLH e MUR25.",
            "7 regiões marinhas (caixas ∩ polígono GCOOS do Golfo) e 5 bacias (USGS HUC2 para o Mississippi).",
            "Médias espaciais ponderadas por cos(lat); clorofila em log10 (média geométrica); meses com < 25 % de pixels "
            "válidos são descartados. Anomalias em relação à climatologia do mesmo mês.",
            "Tendência: declive de Sen com IC de Gilbert usando a variância corrigida de Hamed-Rao; Mann-Kendall clássico, "
            "Hamed-Rao e sazonal; regressão com erros Newey-West; FDR Benjamini-Hochberg.",
            "Correlações de Spearman sem tendência com n efetivo de Bretherton; regressão múltipla com El Niño (ONI); "
            "bootstrap por blocos de 12 meses; Pettitt + BIC; Weatherhead.",
        ],
        "limits_t": "Limitações", "limits": [
            "Em águas costeiras turvas o algoritmo OCI pode confundir sedimentos e matéria orgânica dissolvida com clorofila.",
            "O MODIS-Aqua deriva com o envelhecimento de sua órbita; por isso as manchetes de clorofila usam a série corrigida com VIIRS.",
            "A clorofila é biomassa superficial, não produtividade. Correlação não implica causalidade.",
            "23 anos não bastam para atribuir uma tendência de clorofila à mudança climática (Weatherhead).",
            "O IMERG Final V07 termina em setembro de 2025; a versão 8 ainda não foi publicada.",
        ],
        "dl_t": "Baixar resultados", "dl_json": "Resultados (JSON)", "dl_series": "Séries mensais (CSV)",
        "not_ready": "A pesquisa está sendo reproduzida no servidor com dados da NASA. Esta seção se completa sozinha "
                     "assim que os downloads e o cálculo terminarem.",
        "corr_note": "Nota de reconciliação: a apresentação da equipe citava −7,6 %/década para o Banco de Campeche após "
                     "a correção; o cálculo reproduzido dá",
    },
}
