"""
02_base_consolidada.py — Limpieza y consolidación de la serie histórica 2009-2024.

Entradas : data/raw/ccpc_agregado_entidad.csv, data/raw/inegi_censo2020_iter_entidades.csv
Salidas  : data/processed/panel_entidad_anio.csv   (32 entidades × 6 elecciones, formato largo)
           data/processed/historico_entidad.csv      (32 filas, formato ancho: series + sociodemográficas)

Definiciones (idénticas a la Plataforma CCPC):
  Participación (%) = SV / (SV + NV) × 100     — excluye registros no especificados (NS)
  Abstención   (%) = 100 − Participación
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ANIOS, ENTIDADES, GOBERNATURA, INTERMEDIAS, JUVENTUD, PROC, RAW, TIPOS_SECCION  # noqa: E402


def part(df):
    return 100 * df.SV / (df.SV + df.NV)


def main():
    c = pd.read_csv(RAW / "ccpc_agregado_entidad.csv", encoding="utf-8-sig")
    # ---- Validaciones de calidad ----
    assert c.groupby("AELEC").EDOCVE.nunique().eq(32).all(), "Cada año debe tener 32 entidades"
    assert (c.LN == c.SV + c.NV + c.NS).all(), "LN debe ser SV + NV + NS"
    assert (c[["LN", "SV", "NV", "NS"]] >= 0).all().all()

    # ---- Panel largo entidad × año ----
    e = c.groupby(["AELEC", "EDOCVE"])[["LN", "SV", "NV", "NS"]].sum().reset_index()
    e["PARTICIPACION"] = part(e)
    e["ABSTENCION"] = 100 - e.PARTICIPACION
    e["TIPO_ELECCION"] = e.AELEC.map(lambda a: "Intermedia" if a in INTERMEDIAS else "Presidencial")
    e["GUBERNATURA_CONCURRENTE"] = [int(x in GOBERNATURA[a]) for a, x in zip(e.AELEC, e.EDOCVE)]
    e.insert(2, "ENTIDAD", e.EDOCVE.map(lambda x: ENTIDADES[x][0]))
    e.to_csv(PROC / "panel_entidad_anio.csv", index=False, encoding="utf-8-sig")

    # ---- Formato ancho: series históricas ----
    w = pd.DataFrame(index=pd.Index(range(1, 33), name="EDOCVE"))
    w["ENTIDAD"] = [ENTIDADES[i][0] for i in w.index]
    w["ABREV"] = [ENTIDADES[i][1] for i in w.index]
    for a in ANIOS:
        s = e[e.AELEC == a].set_index("EDOCVE")
        w[f"LN_{a}"] = s.LN
        w[f"VOTANTES_{a}"] = s.SV
        w[f"ABSTENCIONES_{a}"] = s.NV
        w[f"PART_{a}"] = s.PARTICIPACION.round(2)
        w[f"ABST_{a}"] = s.ABSTENCION.round(2)
        w[f"GOB_{a}"] = s.GUBERNATURA_CONCURRENTE

    # ---- Indicadores de ciclo (originalidad: intermedia vs presidencial, fatiga) ----
    w["CAIDA_INTERMEDIA_2018_2021"] = (w.PART_2018 - w.PART_2021).round(2)    # pp que se pierden al pasar a intermedia
    w["CAIDA_INTERMEDIA_PROM"] = ((w.PART_2012 - w.PART_2015) + (w.PART_2018 - w.PART_2021)) .div(2).round(2)
    w["TENDENCIA_INTERMEDIAS_2009_2021"] = ((w.PART_2021 - w.PART_2009) / 12).round(3)   # pp por año
    w["TENDENCIA_PRESIDENCIALES_2012_2024"] = ((w.PART_2024 - w.PART_2012) / 12).round(3)

    # ---- Cortes sociodemográficos (2021 = última intermedia; 2024 = última elección) ----
    for a in (2021, 2024):
        ca = c[c.AELEC == a]
        tot = ca.groupby("EDOCVE")[["LN", "SV", "NV"]].sum()
        juv = ca[ca.GRUPO_EDAD.isin(JUVENTUD)].groupby("EDOCVE")[["LN", "SV", "NV"]].sum()
        w[f"PART_JUVENTUD_18_29_{a}"] = part(juv).round(2)
        w[f"BRECHA_JUVENIL_{a}"] = (part(juv) - part(tot)).round(2)
        for g in ["30-39", "40-49", "50-59", "60-69", "70+"]:
            s = ca[ca.GRUPO_EDAD == g].groupby("EDOCVE")[["SV", "NV"]].sum()
            w[f"PART_EDAD_{g.replace('-', '_').replace('+', 'mas')}_{a}"] = part(s).round(2)
        for sx, nom in ((0, "HOMBRES"), (1, "MUJERES")):
            s = ca[ca.SEXO == sx].groupby("EDOCVE")[["SV", "NV"]].sum()
            w[f"PART_{nom}_{a}"] = part(s).round(2)
        w[f"BRECHA_GENERO_M_H_{a}"] = (w[f"PART_MUJERES_{a}"] - w[f"PART_HOMBRES_{a}"]).round(2)
        for t, nom in TIPOS_SECCION.items():
            s = ca[ca.TIPOSEC == t].groupby("EDOCVE")[["LN", "SV", "NV"]].sum()
            w[f"PART_{nom.upper()}_{a}"] = part(s).round(2)
            w[f"PCT_LN_{nom.upper()}_{a}"] = (100 * s.LN / tot.LN).round(2)
        w[f"BRECHA_RURAL_URBANA_{a}"] = (w[f"PART_RURAL_{a}"] - w[f"PART_URBANA_{a}"]).round(2)
        w[f"PCT_LN_JUVENTUD_{a}"] = (100 * juv.LN / tot.LN).round(2)

    # ---- Variables étnicas (Censo 2020, INEGI) ----
    it = pd.read_csv(RAW / "inegi_censo2020_iter_entidades.csv").set_index("ENTIDAD")
    w["PCT_HABLANTE_LENGUA_INDIGENA_2020"] = (100 * it.P3YM_HLI / it.P_3YMAS).round(2)
    w["PCT_POB_HOGARES_INDIGENAS_2020"] = (100 * it.PHOG_IND / it.POBTOT).round(2)
    w["PCT_POB_AFROMEXICANA_2020"] = (100 * it.POB_AFRO / it.POBTOT).round(2)

    # Rellenos imposibles: tipos de sección inexistentes en una entidad (p. ej. CDMX sin rural)
    faltantes = w.columns[w.isna().any()].tolist()
    if faltantes:
        print("Columnas con celdas vacías (sección inexistente en la entidad):", faltantes)
    w.to_csv(PROC / "historico_entidad.csv", encoding="utf-8-sig")
    print(w[["ENTIDAD"] + [f"PART_{a}" for a in ANIOS]].round(1).to_string())


if __name__ == "__main__":
    main()
