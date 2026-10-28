"""
05_mapa_escenarios.py — Mapa de escenarios ejecutable.

Genera:
  outputs/mapas/escenarios_reto2.geojson     Capa geoespacial (32 entidades) con todas las variables del
                                             modelo: abrir en QGIS, ArcGIS, Power BI (mapa de formas) o Tableau.
  outputs/mapas/Mapa_Escenarios_Reto2.html   Tablero interactivo autocontenido (SVG + JS, sin dependencias ni internet): compara lado a lado
                                             "Sin intervención" vs "Con intervención" (semáforo o abstención %).
  outputs/mapas/mapa_semaforo_sin_vs_con.png Versión estática para reporte y presentación.
"""
import json
import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Polygon  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ENTIDADES, MAPAS, OUT, RAW  # noqa: E402

COLOR = {"Riesgo Alto (Rojo)": "#C8102E", "Riesgo Medio (Amarillo)": "#F2B705", "Riesgo Bajo (Verde)": "#2E8B57"}
ISO2ID = {v[2]: k for k, v in ENTIDADES.items()}


def main():
    r = pd.read_csv(OUT / "Modelo_Riesgo_Escenarios_Reto2.csv", index_col="EDOCVE", encoding="utf-8-sig")
    h = pd.read_csv(RAW.parent / "processed" / "historico_entidad.csv", index_col="EDOCVE", encoding="utf-8-sig")
    geo = json.load(open(RAW / "mexico_estados.geojson", encoding="utf-8"))

    # ---------------- GeoJSON enriquecido ----------------
    campos_h = ["ABST_2009", "ABST_2012", "ABST_2015", "ABST_2018", "ABST_2021", "ABST_2024",
                "BRECHA_JUVENIL_2021", "BRECHA_RURAL_URBANA_2021", "PCT_HABLANTE_LENGUA_INDIGENA_2020",
                "PCT_POB_AFROMEXICANA_2020"]
    for f in geo["features"]:
        e = ISO2ID[f["properties"]["id"]]
        props = {"EDOCVE": e, "ENTIDAD": ENTIDADES[e][0], "ISO": f["properties"]["id"]}
        props |= {k: (v.item() if hasattr(v, "item") else v) for k, v in r.loc[e].items()}
        props |= {k: float(h.loc[e, k]) for k in campos_h}
        f["properties"] = props
    json.dump(geo, open(MAPAS / "escenarios_reto2.geojson", "w", encoding="utf-8"), ensure_ascii=False)

    # ---------------- Tablero HTML ----------------
    datos = []
    for e, row in r.iterrows():
        datos.append({
            "id": ENTIDADES[e][2], "ent": row.ENTIDAD, "gob": int(row.GUBERNATURA_2027),
            "sin": row.Escenario_Sin_Intervencion_2027, "con": row.Escenario_Con_Intervencion,
            "semSin": row.Semaforo_Riesgo, "semCon": row.Semaforo_Con_Intervencion,
            "a21": float(h.loc[e, "ABST_2021"]), "a24": float(h.loc[e, "ABST_2024"]),
            "juv": row.ABST_2027_JUVENTUD_18_29, "rur": row.ABST_2027_RURAL,
            "rec": int(row.Personas_recuperadas), "abs": int(row.Abstencionistas_esperados_sin),
            "lo": row.Banda_inferior_2027, "hi": row.Banda_superior_2027,
            "s2b": row.Escenario_2B_solo_rojos, "sem2b": row.Semaforo_2B_solo_rojos,   # Escenario 2B
            "s30": row.Escenario_Sin_Intervencion_2030,                                 # horizonte 2030
            "ln": int(row.LN_PROYECTADA_2027), "rec2b": int(row.Personas_recuperadas_2B),
        })

    # ---------------- Capa distrital (300 DEF) para el tablero ----------------
    dd = pd.read_csv(OUT / "semaforo_distritos_2027.csv", encoding="utf-8-sig")
    rojo = "Riesgo Alto (Rojo)"
    dd["OCULTO"] = ((dd.SEMAFORO_DISTRITO == rojo) & (dd.SEMAFORO_ENTIDAD != rojo)).astype(int)
    dist = {
        "resumen": {k: int(v) for k, v in dd.SEMAFORO_DISTRITO.value_counts().items()} | {"ocultos": int(dd.OCULTO.sum()), "total": len(dd)},
        "filas": [{"ent": x.ENTIDAD, "def": int(x.DEF), "a24": float(x.ABST_2024), "a27": float(x.ABST_PROY_2027),
                   "sem": x.SEMAFORO_DISTRITO, "semEnt": x.SEMAFORO_ENTIDAD, "abs": int(x.ABSTENCIONISTAS_ESPERADOS),
                   "ln": int(x.LN), "oculto": int(x.OCULTO)}
                  for x in dd.sort_values("ABST_PROY_2027", ascending=False).itertuples()],
    }
    sens = pd.read_csv(OUT / "sensibilidad_intervencion.csv").to_dict("records")
    resumen = json.load(open(OUT / "resumen_modelo.json"))
    geo_min = json.load(open(RAW / "mexico_estados.geojson", encoding="utf-8"))
    for f in geo_min["features"]:
        f["properties"] = {"id": f["properties"]["id"]}
    html = (Path(__file__).parent / "plantilla_mapa.html").read_text(encoding="utf-8")
    html = (html.replace("/*__GEO__*/", json.dumps(geo_min, separators=(",", ":")))
                .replace("/*__DATA__*/", json.dumps(datos, ensure_ascii=False))
                .replace("/*__SENS__*/", json.dumps(sens, ensure_ascii=False))
                .replace("/*__RES__*/", json.dumps(resumen, ensure_ascii=False, default=str))
                .replace("/*__DIST__*/", json.dumps(dist, ensure_ascii=False)))
    # Logos oficiales (https://ine.mx/hackathon-2026/) incrustados como data URI: el archivo sigue funcionando sin internet
    import base64
    assets = Path(__file__).parent / "assets"
    b64 = lambda f: base64.b64encode((assets / f).read_bytes()).decode()  # noqa: E731
    logos = (f'<img class="ine" alt="Instituto Nacional Electoral" src="data:image/png;base64,{b64("logo_ine_2026.png")}">'
             f'<img class="hack" alt="Hackea la participación: datos que construyen democracia" '
             f'src="data:image/png;base64,{b64("logo_hackea_la_participacion.png")}">')
    html = html.replace("<!--__LOGOS__-->", logos)
    (MAPAS / "Mapa_Escenarios_Reto2.html").write_text(html, encoding="utf-8")

    # ---------------- PNG estático ----------------
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.4), dpi=150)
    for ax, col, tit in ((axes[0], "Semaforo_Riesgo", "Escenario 1 · Sin intervención (2027)"),
                         (axes[1], "Semaforo_Con_Intervencion", "Escenario 2 · Con intervención focalizada (2027)")):
        for f in geo["features"]:
            c = COLOR[f["properties"][col]]
            g = f["geometry"]
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            for poly in polys:
                ax.add_patch(Polygon(poly[0], closed=True, facecolor=c, edgecolor="white", linewidth=0.6))
        ax.set_xlim(-118.5, -86.5); ax.set_ylim(14.3, 33); ax.set_aspect("equal"); ax.axis("off")
        n = r[col].value_counts()
        ax.set_title(f"{tit}\nRojo {n.get('Riesgo Alto (Rojo)', 0)} · Amarillo {n.get('Riesgo Medio (Amarillo)', 0)} · "
                     f"Verde {n.get('Riesgo Bajo (Verde)', 0)}", fontsize=12)
    fig.legend(handles=[Patch(color=v, label=k) for k, v in COLOR.items()], loc="lower center", ncol=3, frameon=False)
    fig.suptitle("Semáforo de riesgo de abstención por entidad — elección federal intermedia 2027", fontsize=14, weight="bold")
    fig.text(0.5, 0.06, "Fuente: CCPC 2009-2024 (INE). Umbrales fijos: cuartiles de la abstención proyectada sin intervención.",
             ha="center", fontsize=8, color="#555")
    fig.savefig(MAPAS / "mapa_semaforo_sin_vs_con.png", bbox_inches="tight")
    print("Mapas generados en", MAPAS)


if __name__ == "__main__":
    main()
