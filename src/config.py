"""
config.py — Parámetros globales del proyecto (Reto 2: Predicción y escenarios de riesgo de abstención).

Todo supuesto del modelo vive aquí para que el Comité (y el INE) puedan auditarlo o modificarlo
sin tocar la lógica. Ningún dato personal se usa en el proyecto: la unidad mínima es la
celda agregada entidad × tipo de sección × sexo × grupo de edad.
"""
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# Rutas
# ----------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
MAPAS = OUT / "mapas"
for p in (RAW, PROC, OUT, MAPAS):
    p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------------------------
# Fuentes oficiales
# ----------------------------------------------------------------------------------------------
# Datos abiertos de la Plataforma de los Conteos Censales de Participación Ciudadana (CCPC), INE-DECEyEC.
# Enlaces publicados en https://ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/
CCPC_ZIPS = {
    2009: "https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2009.zip",
    2012: "https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2012.zip",
    2015: "https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2015.zip",
    2018: "https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2018.zip",
    2021: "https://ine.mx/wp-content/uploads/2022/04/DatosAbiertos_DECEyEC_ConteosCensales2021.zip",
    2024: "https://ine.mx/wp-content/uploads/2025/08/DatosAbiertos_DECEyEC_ConteosCensales2024.zip",
}
# Fuente complementaria (variables étnicas, no incluidas en la CCPC): Censo 2020, INEGI, archivo ITER nacional.
INEGI_ITER = "https://www.inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip"
# Contornos estatales (dominio público, derivados de INEGI) para el mapa.
GEOJSON_ESTADOS = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"

# ----------------------------------------------------------------------------------------------
# Calendario electoral
# ----------------------------------------------------------------------------------------------
ANIOS = [2009, 2012, 2015, 2018, 2021, 2024]
INTERMEDIAS = {2009, 2015, 2021, 2027}          # sin elección presidencial
HORIZONTES = [2027, 2030]                        # 2027 = intermedia (horizonte principal); 2030 = presidencial

# Entidades con elección de GUBERNATURA concurrente con la federal (clave INE de entidad).
# Es la variable de contexto más influyente del modelo (ver reporte, sección de validación).
GOBERNATURA = {
    2009: [4, 6, 19, 22, 24, 26],
    2012: [7, 9, 11, 14, 17, 27, 31],
    2015: [3, 4, 6, 12, 16, 19, 22, 24, 26],
    2018: [7, 9, 11, 14, 17, 21, 27, 30, 31],
    2021: [2, 3, 4, 6, 8, 12, 16, 18, 19, 22, 24, 25, 26, 29, 32],
    2024: [7, 9, 11, 14, 17, 21, 27, 30, 31],
    2027: [1, 2, 3, 4, 6, 8, 12, 16, 18, 19, 22, 23, 24, 25, 26, 29, 32],   # 17 gubernaturas
    2030: [7, 9, 11, 14, 17, 21, 27, 30, 31],
}

# ----------------------------------------------------------------------------------------------
# Catálogos
# ----------------------------------------------------------------------------------------------
ENTIDADES = {
    1: ("Aguascalientes", "AGS", "MX-AGU"), 2: ("Baja California", "BC", "MX-BCN"),
    3: ("Baja California Sur", "BCS", "MX-BCS"), 4: ("Campeche", "CAMP", "MX-CAM"),
    5: ("Coahuila", "COAH", "MX-COA"), 6: ("Colima", "COL", "MX-COL"),
    7: ("Chiapas", "CHIS", "MX-CHP"), 8: ("Chihuahua", "CHIH", "MX-CHH"),
    9: ("Ciudad de México", "CDMX", "MX-CMX"), 10: ("Durango", "DGO", "MX-DUR"),
    11: ("Guanajuato", "GTO", "MX-GUA"), 12: ("Guerrero", "GRO", "MX-GRO"),
    13: ("Hidalgo", "HGO", "MX-HID"), 14: ("Jalisco", "JAL", "MX-JAL"),
    15: ("México", "MEX", "MX-MEX"), 16: ("Michoacán", "MICH", "MX-MIC"),
    17: ("Morelos", "MOR", "MX-MOR"), 18: ("Nayarit", "NAY", "MX-NAY"),
    19: ("Nuevo León", "NL", "MX-NLE"), 20: ("Oaxaca", "OAX", "MX-OAX"),
    21: ("Puebla", "PUE", "MX-PUE"), 22: ("Querétaro", "QRO", "MX-QUE"),
    23: ("Quintana Roo", "QROO", "MX-ROO"), 24: ("San Luis Potosí", "SLP", "MX-SLP"),
    25: ("Sinaloa", "SIN", "MX-SIN"), 26: ("Sonora", "SON", "MX-SON"),
    27: ("Tabasco", "TAB", "MX-TAB"), 28: ("Tamaulipas", "TAM", "MX-TAM"),
    29: ("Tlaxcala", "TLAX", "MX-TLA"), 30: ("Veracruz", "VER", "MX-VER"),
    31: ("Yucatán", "YUC", "MX-YUC"), 32: ("Zacatecas", "ZAC", "MX-ZAC"),
}
GRUPOS_EDAD = ["18-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+"]
JUVENTUD = ["18-19", "20-29"]                    # etapa de vida "Juventud" (18-29 años)
TIPOS_SECCION = {"U": "Urbana", "M": "Mixta", "R": "Rural"}


def grupo_edad(edad: int) -> str:
    """Asigna la edad cumplida al grupo decenal usado en todo el proyecto."""
    e = int(edad)
    if e < 20:
        return "18-19"
    if e >= 70:
        return "70+"
    d = (e // 10) * 10
    return f"{d}-{d + 9}"


# ----------------------------------------------------------------------------------------------
# Parámetros del modelo y de los escenarios (supuestos explícitos)
# ----------------------------------------------------------------------------------------------
PESO_LENTE_MISMO_TIPO = 0.5      # peso de la "memoria del mismo tipo de elección" (rezago 6 años);
                                 # 1 - peso = "memoria reciente" (rezago 3 años). Elegido por validación.
LIMITES_PARTICIPACION = (5.0, 98.0)

# Escenario 2 (con intervención hipotética DECEyEC): reducción RELATIVA de la abstención en los
# segmentos objetivo. 15% = escenario solicitado; 5% y 10% = sensibilidad conservadora.
REDUCCION_INTERVENCION = 0.15
SENSIBILIDAD = [0.05, 0.10, 0.15, 0.20]
SEGMENTO_OBJETIVO = {"edades": JUVENTUD, "tipos_seccion": ["R"]}   # jóvenes 18-29 Ó secciones rurales

# Semáforo: cuartiles de la abstención proyectada SIN intervención (umbrales fijos para comparar escenarios)
#   Rojo  : abstención >= percentil 75   | Verde : abstención <= percentil 25 | Amarillo: resto
CUANTIL_ROJO, CUANTIL_VERDE = 0.75, 0.25
