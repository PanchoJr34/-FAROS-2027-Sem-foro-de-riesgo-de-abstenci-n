"""
run_all.py — Ejecuta el flujo completo de punta a punta.

    python run_all.py                 # usa los agregados ya incluidos en data/raw (~30 s, incluye reporte y presentación)
    python run_all.py --desde-cero    # vuelve a descargar los microdatos oficiales del INE (~300 MB)
"""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
pasos = ["02_base_consolidada.py", "03_validacion_modelo.py", "04_escenarios_semaforo.py", "05_mapa_escenarios.py",
         "06_reporte_y_presentacion.py"]
if "--desde-cero" in sys.argv:
    pasos.insert(0, "01_extraccion_ccpc.py")

sys.path.insert(0, str(SRC))
for p in pasos:
    print(f"\n{'=' * 80}\n▶ {p}\n{'=' * 80}")
    sys.argv = [p]
    runpy.run_path(str(SRC / p), run_name="__main__")
print("\nListo. Revise data/processed/ y outputs/.")
