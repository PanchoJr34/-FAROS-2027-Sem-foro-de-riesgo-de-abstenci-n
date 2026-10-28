# FAROS-2027 · Semáforo de riesgo de abstención 2027

Equipo **Commit Democrático**: Francisco Jimenez Salgado y Víctor Manuel Ochoa-Zavala. Reto 2 · Hackathon INE 2026.

**Eje temático 2: Predicción y escenarios de riesgo de abstención.**
**Pregunta guía:** ¿Qué zonas podrían presentar mayor abstención en el futuro si no se interviene?

Este repositorio construye, a partir de los **Conteos Censales de Participación Ciudadana (CCPC) 2009-2024**, un
modelo transparente que proyecta la abstención de la **elección federal intermedia de 2027** por entidad,
segmento de edad, sexo y tipo de sección. También simula una intervención focalizada de la DECEyEC y produce un
semáforo territorial que el INE puede usar para priorizar presupuesto, brigadas y campañas ENCÍVICA.

> Sin datos personales: la unidad mínima es la celda agregada *entidad × tipo de sección × sexo × grupo de edad*.

---

## Resultados en una mirada (FAROS-2027)

| | 2024 observada | 2027 sin intervención | 2027 con intervención |
|---|---|---|---|
| Abstención nacional | 40.33 % | **49.1 %** | 46.0 % |
| Entidades en rojo | – | 8 | 4 |
| Personas que sí votarían gracias a la intervención | – | – | 3,247,560 (2A) · 952,822 si solo se interviene en las 8 rojas (2B) |

* **Rojo en 2027:** Baja California, Guanajuato, Durango, Sonora, Jalisco, Chihuahua, Baja California Sur y Michoacán.
* **Calendario:** 17 entidades eligen gubernatura en 2027. La concurrencia aporta cerca de **+9.5 pp** de participación.
  Guanajuato, Jalisco y Durango quedan en rojo **sin** esa elección.
* **Capa distrital:** 75 de los 300 distritos quedan en rojo. 22 de ellos están en 12 entidades amarillas o verdes, así que el
  promedio estatal los oculta.
* **Juventudes:** su participación (18-29 años) está unos 10 pp por debajo del total de su entidad en 2021.

## Estructura

```
├── run_all.py                         # ejecuta todo el flujo
├── requirements.txt
├── src/
│   ├── config.py                      # rutas, calendario electoral y TODOS los supuestos del modelo
│   ├── modelo.py                      # modelo de "dos lentes" (funciones reutilizables)
│   ├── 01_extraccion_ccpc.py          # descarga los ZIP oficiales del INE y del INEGI y agrega
│   ├── 02_base_consolidada.py         # limpieza, validaciones y base histórica 32 entidades
│   ├── 03_validacion_modelo.py        # validación retrospectiva 2021 y 2024 (6 modelos comparados)
│   ├── 04_escenarios_semaforo.py      # proyección 2027/2030, escenarios, semáforo, capa distrital
│   ├── 05_mapa_escenarios.py          # GeoJSON + tablero HTML + mapa PNG
│   ├── 06_reporte_y_presentacion.py   # figuras, reporte (DOCX/PDF) y presentación (PPTX/PDF)
│   ├── 07_paquete_entrega.py          # arma el .zip de entrega con los nombres oficiales
│   ├── plantilla_mapa.html            # plantilla del tablero (SVG, sin dependencias externas)
│   └── assets/                        # logos oficiales del INE y del Hackathon (ine.mx/hackathon-2026/)
├── data/
│   ├── raw/                           # agregados oficiales (CCPC, ITER 2020) y contornos estatales
│   └── processed/                     # Base_Datos_Reto2_CCPC_2009_2024.csv / .xlsx  ← ENTREGABLE 1
└── outputs/
    ├── Modelo_Riesgo_Escenarios_Reto2.csv
    ├── validacion_backtest.csv · coeficientes_modelo.csv · sensibilidad_intervencion.csv
    ├── semaforo_distritos_2027.csv    # 300 distritos federales (cartografía 2023)
    ├── proyeccion_celdas_2027.csv     # insumo para Power BI / Tableau
    ├── Reporte_Metodologico_Preventivo_Reto2.pdf / .docx   ← ENTREGABLE 4 (14 páginas)
    ├── Presentacion_Ejecutiva_Reto2.pdf / .pptx            ← ENTREGABLE 5 (10 diapositivas)
    ├── figuras/                       # fig1–fig5 a 300 DPI
    └── mapas/
        ├── Mapa_Escenarios_Reto2.html # tablero interactivo: Sin vs Con intervención  ← ENTREGABLE 3
        ├── escenarios_reto2.geojson   # capa geoespacial (QGIS, ArcGIS, Power BI, Tableau)
        └── mapa_semaforo_sin_vs_con.png
```

## Cómo ejecutar

```bash
pip install -r requirements.txt
python run_all.py                 # ~1 min, usa los agregados incluidos en data/raw (incluye reporte y presentación)
python run_all.py --desde-cero    # vuelve a descargar los microdatos oficiales (~300 MB) y reconstruye todo
```

El tablero `outputs/mapas/Mapa_Escenarios_Reto2.html` se abre con doble clic y funciona sin internet.
Para exportar el reporte y la presentación a PDF se usa LibreOffice (`soffice`); sin él se generan solo DOCX y PPTX.

Para armar el paquete de entrega (`outputs/entrega/Commit_Democratico_Eje2_Prediccion_Riesgo_Abstencion.zip`):

```bash
python src/07_paquete_entrega.py --cartas ruta/a/escaneos   # carpeta con las dos cartas firmadas
```

## Fuentes

| Fuente | Uso | Enlace |
|---|---|---|
| CCPC 2009, 2012, 2015, 2018, 2021, 2024 (INE-DECEyEC), datos abiertos | Serie histórica, edad, sexo, tipo de sección, distrito | ine.mx › Transparencia › Datos abiertos › Conteos Censales de Participación |
| Censo de Población y Vivienda 2020 (INEGI), ITER | % hablante de lengua indígena, % en hogares indígenas, % afromexicana | inegi.org.mx/programas/ccpv/2020 |
| Contornos estatales (dominio público, derivados de INEGI) | Mapa | github.com/angelnmara/geojson |

**Definiciones (iguales a las de la Plataforma CCPC).** Participación = SV / (SV + NV). Abstención = 100 − participación.
Los registros no especificados (NS) se excluyen. Validación: 32 entidades en cada año y LN = SV + NV + NS en todas las
celdas. Totales nacionales de participación: 44.1 % (2009), 62.1 % (2012), 47.1 % (2015), 62.4 % (2018), 51.8 % (2021)
y 59.7 % (2024).

## Metodología (resumen)

Para cada celda *c* y elección objetivo *t* se proyecta la participación con dos “lentes”:

* **Lente A, memoria del mismo tipo:** `P(c,t-6) + α_tipo + γ·ΔGubernatura`
* **Lente B, memoria reciente:** `P(c,t-3) + α_tipo + γ·ΔGubernatura`
* **Proyección final:** el promedio simple de A y B. Las celdas se agregan a entidad con la lista nominal proyectada.

`α_tipo` captura el **efecto ciclo** intermedia/presidencial y `γ` el efecto de tener **gubernatura concurrente**.
Se estiman por MCO ponderado con todas las transiciones 2009-2024. Son seis coeficientes en total, cada uno con lectura
directa (`outputs/coeficientes_modelo.csv`).

**Validación retrospectiva.** Se anticipó 2021 con datos hasta 2018 y 2024 con datos hasta 2021:

| Modelo | MAE (pp) | Acierto de color | Spearman |
|---|---|---|---|
| Ingenuo (repetir la elección del mismo tipo) | 5.81 | 54.7 % | 0.59 |
| Lente A | 4.58 | 56.3 % | 0.62 |
| Lente B | 6.46 | 78.1 % | 0.78 |
| **Modelo final (A+B)/2** | **4.62** | **64.1 %** | **0.72** |

El lente A acierta mejor el **nivel** y el lente B **ordena** mejor las entidades. El promedio equilibra ambas cosas. El
error medio (±4.6 pp) se reporta como banda de incertidumbre de cada proyección.

**Escenarios.**
1. *Sin intervención:* la proyección inercial.
2. *Con intervención hipotética:* la abstención baja 15 % relativo en personas de 18-29 años y en secciones rurales. Se
   incluye una variante que interviene solo en las entidades rojas y una sensibilidad con 5, 10, 15 y 20 %.

**Semáforo.** Usa los cuartiles de la abstención 2027 sin intervención: rojo ≥ 51.5 %, verde ≤ 45.9 %. Los umbrales
quedan fijos para comparar ambos escenarios.

## Limitaciones

* Hay seis elecciones; los efectos de ciclo y de gubernatura se estiman con pocas transiciones.
* La CCPC no incluye el voto en casillas especiales ni el voto desde el extranjero.
* Las variables indígena y afromexicana son estatales (Censo 2020), no de sección. Se usan para caracterizar y priorizar,
  no como predictores.
* La capa distrital aplica a cada distrito el cambio proyectado de su entidad sobre su abstención 2024 (cartografía 2023).
  La serie distrital 2009-2021 usa otra cartografía.
* El efecto de la intervención es un supuesto explícito, no una estimación causal. Por eso se presenta la sensibilidad.

## Derechos

Proyecto del equipo **Commit Democrático** (Francisco Jimenez Salgado y Víctor Manuel Ochoa-Zavala) para el Hackathon
INE 2026 «Hackea la participación: Datos que construyen democracia», Eje 2. De acuerdo con la Base Décimo primera de la
convocatoria, los derechos patrimoniales del trabajo se ceden al Instituto Nacional Electoral por diez años; las
personas autoras conservan la autoría. Este repositorio se publica solo para consulta y reproducibilidad, sin licencia
de uso abierta.
