"""
07_paquete_entrega.py — Arma la carpeta comprimida de entrega (Bases Sexta y Séptima de la convocatoria).

Uso:  python src/07_paquete_entrega.py [--cartas RUTA_A_CARPETA_CON_ESCANEOS] [--destino CARPETA]

Estructura generada (nombre del equipo y eje temático, como pide la Base Séptima):

Commit_Democratico_Eje2_Prediccion_Riesgo_Abstencion.zip
└── Commit_Democratico_Eje2_Prediccion_Riesgo_Abstencion/
    ├── 1_Presentacion_Ejecutiva_Commit_Democratico_Eje2.pdf          (general: máx. 10 diapositivas)
    ├── 2_Reporte_Metodologico_Preventivo_Commit_Democratico_Eje2.pdf (Reto 2: 10-15 cuartillas)
    ├── 3_Mapa_Escenarios/                                            (Reto 2: mapa con y sin intervención)
    │   ├── Mapa_Escenarios_Con_y_Sin_Intervencion.html
    │   └── Capa_Escenarios_32_Entidades.geojson
    ├── 4_Base_Datos_Anonimizada/                                     (Reto 2: .CSV / .XLSX)
    │   ├── Base_Datos_Anonimizada_CCPC_2009_2024.csv
    │   └── Base_Datos_Anonimizada_CCPC_2009_2024.xlsx
    ├── 5_Codigo_Repositorio/                                         (general: código)
    └── 6_Cartas_Firmadas/                                            (general: las dos cartas escaneadas)
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOMBRE = "Commit_Democratico_Eje2_Prediccion_Riesgo_Abstencion"
EQ = "Commit_Democratico_Eje2"

ARCHIVOS = {
    f"1_Presentacion_Ejecutiva_{EQ}.pdf": "outputs/Presentacion_Ejecutiva_Reto2.pdf",
    f"2_Reporte_Metodologico_Preventivo_{EQ}.pdf": "outputs/Reporte_Metodologico_Preventivo_Reto2.pdf",
    "3_Mapa_Escenarios/Mapa_Escenarios_Con_y_Sin_Intervencion.html": "outputs/mapas/Mapa_Escenarios_Reto2.html",
    "3_Mapa_Escenarios/Capa_Escenarios_32_Entidades.geojson": "outputs/mapas/escenarios_reto2.geojson",
    "4_Base_Datos_Anonimizada/Base_Datos_Anonimizada_CCPC_2009_2024.csv": "data/processed/Base_Datos_Reto2_CCPC_2009_2024.csv",
    "4_Base_Datos_Anonimizada/Base_Datos_Anonimizada_CCPC_2009_2024.xlsx": "data/processed/Base_Datos_Reto2_CCPC_2009_2024.xlsx",
}
REPO = ["src", "data", "outputs", "README.md", "requirements.txt", "run_all.py", ".gitignore"]
IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", "entrega")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartas", type=Path, help="Carpeta con los escaneos de las dos cartas firmadas")
    ap.add_argument("--destino", type=Path, default=RAIZ / "outputs" / "entrega")
    a = ap.parse_args()

    base = a.destino / NOMBRE
    shutil.rmtree(base, ignore_errors=True)
    for dst, src in ARCHIVOS.items():
        (base / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RAIZ / src, base / dst)
    repo = base / "5_Codigo_Repositorio"
    for x in REPO:
        s = RAIZ / x
        (shutil.copytree(s, repo / x, ignore=IGNORAR) if s.is_dir() else shutil.copy2(s, repo / x))
    cartas = base / "6_Cartas_Firmadas"
    cartas.mkdir()
    n_cartas = 0
    if a.cartas:
        for f in sorted(a.cartas.iterdir()):
            if f.is_file():
                shutil.copy2(f, cartas / f.name)
                n_cartas += 1

    z = a.destino / f"{NOMBRE}.zip"
    z.unlink(missing_ok=True)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(base.rglob("*")):
            zf.write(p, p.relative_to(a.destino))
    with zipfile.ZipFile(z) as zf:
        assert zf.testzip() is None
    print(f"Paquete: {z} · {z.stat().st_size / 1e6:.1f} MB · cartas incluidas: {n_cartas}")
    if n_cartas < 2:
        print("AVISO: faltan las cartas firmadas en 6_Cartas_Firmadas (su omisión es causa de descalificación).",
              file=sys.stderr)


if __name__ == "__main__":
    main()
