"""
01_extraccion_ccpc.py — Descarga y agregación de los datos abiertos oficiales.

Qué hace
--------
1. Descarga los 6 ZIP de datos abiertos de la CCPC (2009-2024) publicados por el INE.
   Cada ZIP trae 32 CSV (uno por entidad) con registros agregados por
   sección × sexo × edad: LN (lista nominal), SV (sí votó), NV (no votó), NS (no especificado).
2. Agrega a la celda analítica del proyecto:
       año × entidad × tipo de sección (U/M/R) × sexo × grupo de edad
   -> data/raw/ccpc_agregado_entidad.csv   (≈8,100 filas; sin datos personales)
3. Agrega también por Distrito Electoral Federal (capa operativa):
       año × entidad × DEF  -> data/raw/ccpc_agregado_distrito.csv
4. Extrae del Censo 2020 (ITER, INEGI) los totales estatales de población hablante de lengua
   indígena, afromexicana y en hogares indígenas -> data/raw/inegi_censo2020_iter_entidades.csv

Uso
---
    python src/01_extraccion_ccpc.py            # descarga todo (≈300 MB) y agrega
    python src/01_extraccion_ccpc.py --sin-descarga   # usa los ZIP ya presentes en data/raw/zips

Nota de reproducibilidad: el equipo ejecutó exactamente esta lógica de agregación sobre los ZIP
oficiales el 26/10/2026; los totales nacionales resultantes se validan al final del script.
"""
import argparse
import io
import sys
import urllib.request
import zipfile
from collections import defaultdict

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from config import CCPC_ZIPS, INEGI_ITER, RAW, grupo_edad  # noqa: E402

ZIPS = RAW / "zips"
ZIPS.mkdir(exist_ok=True)


def descargar(url: str, destino):
    """Descarga un archivo si no existe localmente."""
    if destino.exists():
        print(f"  ya existe: {destino.name}")
        return
    print(f"  descargando {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Hackathon INE 2026)"})
    with urllib.request.urlopen(req) as r, open(destino, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)


def agregar_ccpc():
    """Recorre los 32 CSV de cada año y acumula LN/SV/NV/NS por celda y por distrito."""
    celdas = defaultdict(lambda: [0, 0, 0, 0])
    distritos = defaultdict(lambda: [0, 0, 0, 0])
    nombres = {}
    for anio in CCPC_ZIPS:
        z = zipfile.ZipFile(ZIPS / f"ccpc{anio}.zip")
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        print(f"  {anio}: {len(csvs)} archivos estatales")
        for n in csvs:
            for df in pd.read_csv(z.open(n), chunksize=500_000, dtype={"TIPOSEC": str}, low_memory=False):
                df["TIPO"] = df["TIPOSEC"].astype(str).str.strip().str[0].str.upper()   # 'Urbana'/'U' -> 'U'
                df["GRUPO_EDAD"] = df["EDAD"].map(grupo_edad)
                for c in ("LN", "SV", "NV", "NS"):
                    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype("int64")
                g = df.groupby(["EDOCVE", "TIPO", "SEXO", "GRUPO_EDAD"])[["LN", "SV", "NV", "NS"]].sum()
                for k, v in g.iterrows():
                    acc = celdas[(anio, *k)]
                    for i, c in enumerate(("LN", "SV", "NV", "NS")):
                        acc[i] += int(v[c])
                g2 = df.groupby(["EDOCVE", "DEF"])[["LN", "SV", "NV", "NS"]].sum()
                for k, v in g2.iterrows():
                    acc = distritos[(anio, *k)]
                    for i, c in enumerate(("LN", "SV", "NV", "NS")):
                        acc[i] += int(v[c])
                nombres.update(df.drop_duplicates("EDOCVE").set_index("EDOCVE")["EDONOM"].to_dict())
    cel = pd.DataFrame([(*k, *v) for k, v in celdas.items()],
                       columns=["AELEC", "EDOCVE", "TIPOSEC", "SEXO", "GRUPO_EDAD", "LN", "SV", "NV", "NS"])
    cel.insert(2, "EDONOM", cel["EDOCVE"].map(nombres))
    cel = cel.sort_values(["AELEC", "EDOCVE", "TIPOSEC", "SEXO", "GRUPO_EDAD"])
    dis = pd.DataFrame([(*k, *v) for k, v in distritos.items()],
                       columns=["AELEC", "EDOCVE", "DEF", "LN", "SV", "NV", "NS"])
    return cel, dis


def extraer_iter():
    """Filas estatales (MUN=0, LOC=0) del ITER 2020 con las variables étnicas."""
    destino = ZIPS / "iter_00_cpv2020_csv.zip"
    descargar(INEGI_ITER, destino)
    z = zipfile.ZipFile(destino)
    n = [x for x in z.namelist() if x.endswith("conjunto_de_datos_iter_00CSV20.csv")][0]
    cols = ["ENTIDAD", "NOM_ENT", "MUN", "LOC", "POBTOT", "P_3YMAS", "P3YM_HLI", "POB_AFRO", "PHOG_IND"]
    it = pd.read_csv(z.open(n), usecols=cols, dtype=str, encoding="utf-8-sig")
    it = it[(it.MUN.astype(int) == 0) & (it.LOC.astype(int) == 0) & (it.ENTIDAD.astype(int) > 0)]
    it = it.drop(columns=["MUN", "LOC"])
    it["ENTIDAD"] = it["ENTIDAD"].astype(int)
    for c in cols[4:]:
        it[c] = pd.to_numeric(it[c])
    return it


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-descarga", action="store_true")
    a = ap.parse_args()
    if not a.sin_descarga:
        for anio, url in CCPC_ZIPS.items():
            descargar(url, ZIPS / f"ccpc{anio}.zip")
    print("Agregando CCPC…")
    cel, dis = agregar_ccpc()
    cel.to_csv(RAW / "ccpc_agregado_entidad.csv", index=False, encoding="utf-8-sig")
    dis.to_csv(RAW / "ccpc_agregado_distrito.csv", index=False)
    print("Extrayendo ITER 2020…")
    extraer_iter().to_csv(RAW / "inegi_censo2020_iter_entidades.csv", index=False)

    # Validación: 32 entidades por año y totales nacionales
    nat = cel.groupby("AELEC").agg(ENT=("EDOCVE", "nunique"), LN=("LN", "sum"), SV=("SV", "sum"), NV=("NV", "sum"))
    nat["PART_%"] = (100 * nat.SV / (nat.SV + nat.NV)).round(2)
    print(nat)
    assert (nat.ENT == 32).all(), "Falta alguna entidad"


if __name__ == "__main__":
    main()
