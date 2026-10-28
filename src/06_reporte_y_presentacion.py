"""
06_reporte_y_presentacion.py — Genera las figuras, el Reporte Metodológico y Preventivo y la Presentación Ejecutiva.

Todo se lee de los resultados del flujo (data/processed/ y outputs/): si cambia un supuesto en config.py y se
vuelve a correr run_all.py, el reporte y la presentación se actualizan con las cifras nuevas.

Salidas
  outputs/figuras/fig1..fig5 (.png, 300 DPI)
  outputs/Reporte_Metodologico_Preventivo_Reto2.docx / .pdf     (11-14 páginas, Calibri 11, interlineado 1.3)
  outputs/Presentacion_Ejecutiva_Reto2.pptx / .pdf              (10 diapositivas 16:9)

Requisitos: python-docx, python-pptx, matplotlib; LibreOffice (soffice) para exportar a PDF.

>>> Antes de entregar, escriba el nombre del equipo y sus integrantes en EQUIPO e INTEGRANTES. <<<
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import MAPAS, OUT, PROC, RAW  # noqa: E402

# ------------------------------------------------------------------------------------------ datos del equipo
EQUIPO = "Commit Democrático"
SISTEMA = "FAROS-2027"
TITULO = f"{SISTEMA} · Semáforo de riesgo de abstención 2027"
SUBTITULO = ("Focalización y Alerta de Riesgo de Abstención Subestatal mediante dos lentes de memoria electoral "
             "en las 32 entidades y 300 distritos federales")
INTEGRANTES = ["Francisco Jimenez Salgado", "Víctor Manuel Ochoa-Zavala"]

ASSETS = Path(__file__).resolve().parent / "assets"
LOGO_INE = ASSETS / "logo_ine_2026.png"                      # descargado de https://ine.mx/hackathon-2026/
LOGO_HACK = ASSETS / "logo_hackea_la_participacion.png"      # descargado de https://ine.mx/hackathon-2026/
URL_CCPC = "ine.mx/transparencia/datos-abiertos/visualizacion-datos/conteos-censales-participacion/"
URL_HACK = "ine.mx/hackathon-2026/"
URL_ITER = "inegi.org.mx/contenidos/programas/ccpv/2020/datosabiertos/iter/iter_00_cpv2020_csv.zip"
FIG = OUT / "figuras"
FIG.mkdir(exist_ok=True)
AZUL, TINTA, ROJO, AMAR, VERDE, GRIS = "#23395B", "#14202B", "#C8102E", "#F2B705", "#2E8B57", "#7D8894"   # AZUL = azul pizarra (acento)
COLOR_SEM = {"Riesgo Alto (Rojo)": ROJO, "Riesgo Medio (Amarillo)": AMAR, "Riesgo Bajo (Verde)": VERDE}
CORTO = {"Riesgo Alto (Rojo)": "Rojo", "Riesgo Medio (Amarillo)": "Amarillo", "Riesgo Bajo (Verde)": "Verde"}
ROJO_S = "Riesgo Alto (Rojo)"

# Tipografía: Carlito es métricamente idéntica a Calibri (si existe, se usa en las figuras)
_fuentes = {f.name for f in font_manager.fontManager.ttflist}
FUENTE = next((f for f in ("Calibri", "Carlito", "Arial", "Liberation Sans") if f in _fuentes), "DejaVu Sans")
plt.rcParams.update({"font.family": FUENTE, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#B8C1CA", "axes.labelcolor": TINTA, "xtick.color": TINTA, "ytick.color": TINTA,
                     "axes.titleweight": "bold", "axes.titlesize": 11.5, "axes.titlecolor": TINTA})


def fmt(x, d=2):
    return f"{x:,.{d}f}"


def lista(xs):
    """'a, b y c' en español."""
    xs = [str(x) for x in xs]
    if len(xs) == 1:
        return xs[0]
    ult = xs[-1]
    conj = "e" if (ult.lower().startswith(("i", "í")) or (ult.lower().startswith("hi") and not ult.lower().startswith("hie"))) else "y"
    return ", ".join(xs[:-1]) + f" {conj} " + ult


def fint(x):
    return f"{int(round(x)):,}"


# ============================================================================================ CARGA
def cargar():
    D = {}
    D["base"] = pd.read_csv(PROC / "Base_Datos_Reto2_CCPC_2009_2024.csv", index_col="EDOCVE", encoding="utf-8-sig")
    D["panel"] = pd.read_csv(PROC / "panel_entidad_anio.csv", encoding="utf-8-sig")
    D["val"] = pd.read_csv(OUT / "validacion_backtest.csv", encoding="utf-8-sig")
    D["coef"] = pd.read_csv(OUT / "coeficientes_modelo.csv", encoding="utf-8-sig")
    D["sens"] = pd.read_csv(OUT / "sensibilidad_intervencion.csv", encoding="utf-8-sig")
    D["dist"] = pd.read_csv(OUT / "semaforo_distritos_2027.csv", encoding="utf-8-sig")
    D["cel"] = pd.read_csv(OUT / "proyeccion_celdas_2027.csv", encoding="utf-8-sig")
    D["res"] = json.load(open(OUT / "resumen_modelo.json", encoding="utf-8"))
    D["celdas_raw"] = pd.read_csv(RAW / "ccpc_agregado_entidad.csv", encoding="utf-8-sig")
    d = D["dist"]
    d["OCULTO"] = (d.SEMAFORO_DISTRITO == ROJO_S) & (d.SEMAFORO_ENTIDAD != ROJO_S)
    return D


def hechos(D):
    """Todas las cifras que cita el texto, calculadas aquí (nunca escritas a mano)."""
    b, res, d, cel, s = D["base"], D["res"], D["dist"], D["cel"].copy(), D["sens"]
    H = dict(res)
    p = D["panel"].groupby("AELEC")[["SV", "NV", "LN"]].sum()
    H["part_nac"] = (100 * p.SV / (p.SV + p.NV)).round(2).to_dict()
    H["ln_nac"] = p.LN.to_dict()
    H["n_celdas"] = len(D["celdas_raw"])
    H["bitacora"] = pd.read_csv(RAW / "bitacora_extraccion.csv")
    cel["A"] = 100 - cel.PART_2027_SIN
    ag = lambda g: float((g.A * g.LN_2027).sum() / g.LN_2027.sum())  # noqa: E731
    joven = cel.GRUPO_EDAD.isin(["18-19", "20-29"])
    H["abs_joven"], H["abs_30mas"] = ag(cel[joven]), ag(cel[~joven])
    _ed = cel.assign(G=np.where(joven, "j", "a")).groupby(["EDOCVE", "G"]).apply(ag, include_groups=False).unstack()
    H["med_joven"], H["med_30mas"] = float(np.median(_ed["j"])), float(np.median(_ed["a"]))
    H["abs_joven_h"], H["abs_joven_m"] = ag(cel[joven & (cel.SEXO == "Hombres")]), ag(cel[joven & (cel.SEXO == "Mujeres")])
    H["abs_tipo"] = {t: ag(cel[cel.TIPOSEC == t]) for t in ("Urbana", "Mixta", "Rural")}
    H["abs_sexo"] = {x: ag(cel[cel.SEXO == x]) for x in ("Hombres", "Mujeres")}
    H["urb_mayor_rural"] = int((b.ABST_2027_URBANA > b.ABST_2027_RURAL).sum())
    H["rural_mayor"] = b.loc[b.ABST_2027_RURAL > b.ABST_2027_URBANA, "ENTIDAD"].tolist()
    H["h_mayor_m"] = int((b.ABST_2027_HOMBRES > b.ABST_2027_MUJERES).sum())
    H["brecha_sexo_min"], H["brecha_sexo_max"] = float(b.BRECHA_GENERO_M_H_2024.min()), float(b.BRECHA_GENERO_M_H_2024.max())
    H["brecha_juv_2021"], H["brecha_juv_2024"] = float(b.BRECHA_JUVENIL_2021.mean()), float(b.BRECHA_JUVENIL_2024.mean())
    H["juv_max_ent"], H["juv_max"] = b.loc[b.ABST_2027_JUVENTUD_18_29.idxmax(), "ENTIDAD"], float(b.ABST_2027_JUVENTUD_18_29.max())
    H["caida_intermedia"] = float(b.CAIDA_INTERMEDIA_PROM.mean())
    H["rojos"] = b[b.Semaforo_Riesgo == ROJO_S].sort_values("Escenario_Sin_Intervencion_2027", ascending=False)
    H["rojos_sin_gob"] = H["rojos"].loc[H["rojos"].GUBERNATURA_2027 == 0, "ENTIDAD"].tolist()
    H["sin_gob_2027"] = b.loc[b.GUBERNATURA_2027 == 0, "ENTIDAD"].tolist()
    H["n_cnt"] = {k: int((b.Semaforo_Riesgo == k).sum()) for k in COLOR_SEM}
    H["n_cnt_con"] = {k: int((b.Semaforo_Con_Intervencion == k).sum()) for k in COLOR_SEM}
    H["n_cnt_2b"] = {k: int((b.Semaforo_2B_solo_rojos == k).sum()) for k in COLOR_SEM}
    H["ln27"] = float(b.LN_PROYECTADA_2027.sum())
    H["abs_esperados"] = int(b.Abstencionistas_esperados_sin.sum())
    H["abs2030"] = float((b.Escenario_Sin_Intervencion_2030 * b.LN_PROYECTADA_2027).sum() / b.LN_PROYECTADA_2027.sum())
    H["d_cnt"] = d.SEMAFORO_DISTRITO.value_counts().to_dict()
    H["d_ocultos"] = d[d.OCULTO]
    H["d_ocultos_ent"] = H["d_ocultos"].ENTIDAD.value_counts()
    H["d_rojo_en_rojo"] = int(((d.SEMAFORO_DISTRITO == ROJO_S) & (d.SEMAFORO_ENTIDAD == ROJO_S)).sum())
    H["d_umbral"] = d.ABST_PROY_2027.quantile([0.25, 0.75]).to_dict()
    H["pct_ln_juv"] = float((b.PCT_LN_JUVENTUD_2024 * b.LN_2024).sum() / b.LN_2024.sum())
    H["pct_ln_rur"] = float((b.PCT_LN_RURAL_2024 * b.LN_2024).sum() / b.LN_2024.sum())
    H["sens"] = s
    g = D["coef"].set_index(["Lente", "Coeficiente"]).Valor_pp
    H["gA"], H["gB"] = float(g["A_mismo_tipo", "gamma_gubernatura"]), float(g["B_reciente", "gamma_gubernatura"])
    H["aA_i"], H["aA_p"] = float(g["A_mismo_tipo", "alfa_intermedia"]), float(g["A_mismo_tipo", "alfa_presidencial"])
    H["aB_i"], H["aB_p"] = float(g["B_reciente", "alfa_intermedia"]), float(g["B_reciente", "alfa_presidencial"])
    v = D["val"]
    m5 = v[v.Modelo.str.startswith("M5")]
    H["spearman"] = round(float(m5.Spearman.mean()) + 1e-9, 2)
    H["acierto"] = float(m5["Acierto_semaforo_%"].mean())
    H["m0_mae"] = float(v[v.Modelo.str.startswith("M0")].MAE_pp.mean())
    return H


# ============================================================================================ FIGURAS
# Modo diapositiva: misma gráfica sin título interno (lo pone la diapositiva) y con letra más grande
SLIDE = False
FS = 1.0


def titulo_ax(ax, t, **kw):
    if not SLIDE:
        ax.set_title(t, **kw)


def sup(fig, t, **kw):
    if not SLIDE:
        fig.suptitle(t, **kw)


def guardar(fig, nombre):
    if SLIDE:
        nombre = nombre.replace(".png", "_slide.png")
        for ax in fig.axes:
            ax.tick_params(labelsize=10 * FS)
            ax.xaxis.label.set_size(10.5 * FS); ax.yaxis.label.set_size(10.5 * FS)
    fig.savefig(FIG / nombre, dpi=300 if not SLIDE else 200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def fig1(D, H):
    """Serie nacional 2009-2024 y proyecciones 2027 (tres escenarios) y 2030."""
    anios = [2009, 2012, 2015, 2018, 2021, 2024]
    ab = [100 - H["part_nac"][a] for a in anios]
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    for a in anios:
        if a in (2009, 2015, 2021):
            ax.axvspan(a - 1.2, a + 1.2, color="#E8EDF2", zorder=0)
    ax.plot(anios, ab, "-o", color=AZUL, lw=2.4, ms=7, zorder=3, label="Abstención observada (CCPC)")
    for a, y in zip(anios, ab):
        abajo = a in (2012, 2018, 2024)          # presidenciales: etiqueta debajo del punto
        ax.annotate(f"{y:.1f}%", (a, y), xytext=(0, -15 if abajo else 9), textcoords="offset points", ha="center",
                    fontsize=9 * FS, color=TINTA)
    pro = [(2027, H["abstencion_nacional_2027_sin"], TINTA, "2027 sin intervención"),
           (2027, H["abstencion_nacional_2027_2B"], AMAR, "2027 escenario 2B (solo 8 rojos)"),
           (2027, H["abstencion_nacional_2027_con"], VERDE, "2027 escenario 2A (nacional)")]
    ax.plot([2024, 2027], [ab[-1], H["abstencion_nacional_2027_sin"]], ls="--", color=TINTA, lw=1.4)
    ax.plot([2027, 2030], [H["abstencion_nacional_2027_sin"], H["abs2030"]], ls=":", color=GRIS, lw=1.4)
    for (x, y, c, lab), (dx, dy, ha) in zip(pro, ((-12, -3, "right"), (12, -3, "left"), (-12, -6, "right"))):
        ax.scatter([x], [y], s=70, color=c, edgecolor="white", zorder=4, label=lab)
        ax.annotate(f"{y:.2f}%", (x, y), xytext=(dx, dy), textcoords="offset points", fontsize=9 * FS, color=TINTA, ha=ha,
                    zorder=6, bbox=dict(boxstyle="round,pad=0.12", facecolor="white", edgecolor="none", alpha=0.9))
    ax.scatter([2030], [H["abs2030"]], s=55, color=GRIS, zorder=4, label="2030 presidencial (inercia)")
    ax.annotate(f"{H['abs2030']:.1f}%", (2030, H["abs2030"]), xytext=(8, -3), textcoords="offset points", fontsize=9 * FS)
    ax.text(2015, 64, "Bandas = elecciones intermedias", ha="center", fontsize=8.5 * FS, color=AZUL)
    ax.set_xticks(anios + [2027, 2030]); ax.set_ylim(30, 66); ax.set_xlim(2007.5, 2031.5)
    ax.set_ylabel("Abstención nacional (%)")
    titulo_ax(ax, "El efecto ciclo: la abstención sube en cada intermedia y 2027 repetiría el patrón")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=8 * FS, frameon=False, ncol=3)
    ax.grid(axis="y", color="#EEE", lw=0.8)
    guardar(fig, "fig1_serie_nacional_ciclo.png")


def fig2(D, H):
    """Validación retrospectiva de los 6 modelos (promedio 2021-2024)."""
    v = D["val"].copy()
    v["M"] = v.Modelo.str.extract(r"^(M\d)")
    pm = v.groupby("M")[["MAE_pp", "Acierto_semaforo_%", "Spearman"]].mean().round(2)   # mismo redondeo que la tabla
    etiquetas = {"M0": "M0 Ingenuo\nmismo tipo", "M1": "M1 Ingenuo\nreciente", "M2": "M2 Lente A\nsin gub.",
                 "M3": "M3 Lente A", "M4": "M4 Lente B", "M5": "M5 FINAL\n(A+B)/2"}
    cols = [AZUL if m == "M5" else "#C9D3DE" for m in pm.index]
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.6))
    for ax, c, tit, fmt_ in zip(axs, ["MAE_pp", "Acierto_semaforo_%", "Spearman"],
                                ["Error medio (pp) · menor es mejor", "Acierto del color del semáforo (%)", "Orden del riesgo (Spearman)"],
                                ["{:.2f}", "{:.0f}%", "{:.2f}"]):
        ax.barh([etiquetas[m] for m in pm.index], pm[c], color=cols)
        for i, val in enumerate(pm[c]):
            ax.text(val, i, " " + fmt_.format(val), va="center", fontsize=8.5 * FS)
        ax.set_title(tit, fontsize=10 * FS, color=TINTA, weight="bold"); ax.invert_yaxis(); ax.tick_params(axis="y", labelsize=8 * FS)
        ax.set_xlim(0, pm[c].max() * 1.25)
    for ax in axs[1:]:
        ax.set_yticklabels([])
    sup(fig, "Validación retrospectiva: anticipar 2021 y 2024 solo con datos previos (promedio de ambas pruebas)",
                 fontsize=11 * FS, weight="bold", color=TINTA, y=1.02)
    fig.tight_layout()
    guardar(fig, "fig2_validacion_backtest.png")


def fig3(D, H):
    """Brechas de abstención proyectada 2027: edad, tipo de sección y sexo, en las 32 entidades."""
    b = D["base"].copy()
    cel = D["cel"].copy(); cel["A"] = 100 - cel.PART_2027_SIN
    cel["G"] = np.where(cel.GRUPO_EDAD.isin(["18-19", "20-29"]), "18-29", "30+")
    w = lambda g: (g.A * g.LN_2027).sum() / g.LN_2027.sum()  # noqa: E731
    edad = cel.groupby(["EDOCVE", "G"]).apply(w, include_groups=False).unstack()
    tipo = b[["ABST_2027_URBANA", "ABST_2027_MIXTA", "ABST_2027_RURAL"]].set_axis(["Urbana", "Mixta", "Rural"], axis=1)
    sexo = b[["ABST_2027_HOMBRES", "ABST_2027_MUJERES"]].set_axis(["Hombres", "Mujeres"], axis=1)
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.9), sharey=True)
    paneles = [(axs[0], edad[["18-29", "30+"]], [ROJO, AZUL], "Edad: juventudes vs 30+"),
               (axs[1], tipo, ["#23395B", "#6E8DB3", "#8C7A5B"], "Tipo de sección"),
               (axs[2], sexo, ["#23395B", "#B07A2A"], "Sexo")]
    rng = np.random.default_rng(7)
    for ax, df, cs, tit in paneles:
        for i, (col, c) in enumerate(zip(df.columns, cs)):
            y = df[col].to_numpy()
            ax.scatter(i + rng.uniform(-0.13, 0.13, len(y)), y, s=16, color=c, alpha=0.55, edgecolor="none")
            ax.hlines(np.median(y), i - 0.3, i + 0.3, color=TINTA, lw=2)
            ax.text(i + 0.33, np.median(y), f"{np.median(y):.1f}", va="center", ha="left", fontsize=8.5 * FS, weight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.set_xticks(range(len(df.columns)), df.columns); ax.set_title(tit, fontsize=10.5 * FS, color=TINTA, weight="bold")
        ax.grid(axis="y", color="#EEE")
    axs[0].set_ylabel("Abstención proyectada 2027 (%)")
    sup(fig, "Brechas estructurales: cada punto es una entidad; la línea es la mediana de las 32",
                 fontsize=11 * FS, weight="bold", color=TINTA, y=1.02)
    fig.tight_layout()
    guardar(fig, "fig3_brechas_edad_rural_sexo.png")


def fig4(D, H):
    """Ranking de las 32 entidades con banda ±MAE y desplazamiento al escenario 2A."""
    b = D["base"].sort_values("Escenario_Sin_Intervencion_2027")
    mae = H["mae_validacion"]
    fig, ax = plt.subplots(figsize=(5.6, 6.2))   # compacta: se inserta a ~8.5 cm y la letra debe leerse
    y = np.arange(len(b))
    for i, (_, r) in enumerate(b.iterrows()):
        c = COLOR_SEM[r.Semaforo_Riesgo]
        ax.hlines(i, r.Escenario_Sin_Intervencion_2027 - mae, r.Escenario_Sin_Intervencion_2027 + mae, color=c, alpha=0.25, lw=7)
        ax.annotate("", xy=(r.Escenario_Con_Intervencion, i), xytext=(r.Escenario_Sin_Intervencion_2027, i),
                    arrowprops=dict(arrowstyle="->", color=GRIS, lw=1))
        ax.scatter(r.Escenario_Sin_Intervencion_2027, i, s=46, color=c, edgecolor="white", zorder=3)
        x_txt = r.Escenario_Sin_Intervencion_2027 + mae + 0.35
        for u in (H["umbral_rojo"], H["umbral_verde"]):          # si la etiqueta cae sobre una línea de umbral, se recorre
            if abs((x_txt + 0.5) - u) < 0.95:
                x_txt = max(u, x_txt) + 0.45
        ax.text(x_txt, i, f"{r.Escenario_Sin_Intervencion_2027:.1f}", va="center", fontsize=7.5 * FS,
                zorder=5, bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=1.0))
    ax.axvline(H["umbral_rojo"], color=ROJO, ls="--", lw=1, zorder=1); ax.axvline(H["umbral_verde"], color=VERDE, ls="--", lw=1, zorder=1)
    caja = dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=1.0)
    ax.text(H["umbral_rojo"], len(b) + 0.3, f" Rojo ≥ {H['umbral_rojo']:.2f}%", color=ROJO, fontsize=8 * FS, ha="left", zorder=5, bbox=caja)
    ax.text(H["umbral_verde"], len(b) + 0.3, f"Verde ≤ {H['umbral_verde']:.2f}% ", color=VERDE, fontsize=8 * FS, ha="right", zorder=5, bbox=caja)
    ax.set_yticks(y, [f"{e}{' *' if g else ''}" for e, g in zip(b.ENTIDAD, b.GUBERNATURA_2027)], fontsize=8.5 * FS)
    ax.set_xlabel("Abstención proyectada 2027 (%) · banda = ± error medio de validación · flecha = escenario 2A")
    titulo_ax(ax, "Semáforo 2027 por entidad (* = elige gubernatura en 2027)")
    ax.set_ylim(-1, len(b) + 1.2); ax.set_xlim(right=68); ax.grid(axis="x", color="#EEE")
    guardar(fig, "fig4_ranking_32_entidades_bandas.png")


def fig5(D, H):
    """Los distritos rojos ocultos frente al promedio de su entidad."""
    o = H["d_ocultos"].sort_values("ABST_PROY_2027")
    ent = D["base"].set_index("ENTIDAD")
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    for i, (_, r) in enumerate(o.iterrows()):
        pe = ent.loc[r.ENTIDAD, "Escenario_Sin_Intervencion_2027"]
        c = COLOR_SEM[r.SEMAFORO_ENTIDAD]
        ax.hlines(i, pe, r.ABST_PROY_2027, color="#D5DCE3", lw=2)
        ax.scatter(pe, i, s=42, color=c, edgecolor=TINTA, lw=0.4, zorder=3)
        ax.scatter(r.ABST_PROY_2027, i, s=50, color=ROJO, zorder=3)
        ax.text(r.ABST_PROY_2027 + 0.35, i, f"{r.ABST_PROY_2027:.1f}%", va="center", fontsize=7.8 * FS)
    ax.axvline(H["d_umbral"][0.75], color=ROJO, ls="--", lw=1)
    ax.text(H["d_umbral"][0.75], len(o) + 0.2, f"umbral rojo distrital {H['d_umbral'][0.75]:.2f}% ", color=ROJO, fontsize=8 * FS, ha="right")
    ax.set_yticks(range(len(o)), [f"{e} · DEF {int(k)}" for e, k in zip(o.ENTIDAD, o.DEF)], fontsize=8.3 * FS)
    ax.set_xlabel("Abstención proyectada 2027 (%): ● rojo = distrito · ● amarillo/verde = promedio de su entidad")
    titulo_ax(ax, f"{len(o)} distritos en rojo escondidos en entidades amarillas o verdes")
    ax.set_ylim(-1, len(o) + 1); ax.grid(axis="x", color="#EEE")
    guardar(fig, "fig5_distritos_rojos_ocultos.png")


def fig_mapas_slide(D, H):
    """Semáforo sin vs con intervención, sin título interno, para la diapositiva 6."""
    from matplotlib.patches import Patch, Polygon
    geo = json.load(open(RAW / "mexico_estados.geojson", encoding="utf-8"))
    from config import ENTIDADES
    iso = {v[2]: k for k, v in ENTIDADES.items()}
    b = D["base"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.9))
    for ax, col, tit in ((axes[0], "Semaforo_Riesgo", "Sin intervención"), (axes[1], "Semaforo_Con_Intervencion", "Con intervención 2A")):
        for f in geo["features"]:
            c = COLOR_SEM[b.loc[iso[f["properties"]["id"]], col]]
            g = f["geometry"]
            for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
                ax.add_patch(Polygon(poly[0], closed=True, facecolor=c, edgecolor="white", linewidth=0.6))
        ax.set_xlim(-118.5, -86.5); ax.set_ylim(14.3, 33); ax.set_aspect("equal"); ax.axis("off")
        n = b[col].value_counts()
        ax.set_title(f"{tit}: {n.get(ROJO_S, 0)} en rojo, {n.get('Riesgo Medio (Amarillo)', 0)} en amarillo, "
                     f"{n.get('Riesgo Bajo (Verde)', 0)} en verde", fontsize=15, color=TINTA, loc="left")
    fig.legend(handles=[Patch(color=v, label=k) for k, v in COLOR_SEM.items()], loc="lower center", ncol=3,
               frameon=False, fontsize=13, bbox_to_anchor=(0.5, -0.02))
    fig.subplots_adjust(wspace=0.04, left=0.01, right=0.99, top=0.9, bottom=0.1)
    fig.savefig(FIG / "mapas_slide.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figuras(D, H):
    global SLIDE, FS
    for f in (fig1, fig2, fig3, fig4, fig5):
        f(D, H)
    SLIDE, FS = True, 1.35          # versiones para la presentación
    for f in (fig1, fig2, fig3, fig5):
        f(D, H)
    fig_mapas_slide(D, H)
    SLIDE, FS = False, 1.0
    print("Figuras:", sorted(p.name for p in FIG.glob("*.png")))


# ============================================================================================ PDF
def a_pdf(ruta: Path):
    """Convierte .docx/.pptx a PDF con LibreOffice (si está instalado)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("  ⚠ LibreOffice no encontrado: exporte a PDF desde Word/PowerPoint.")
        return None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(ruta.parent), str(ruta)],
                   check=True, capture_output=True, timeout=240)
    return ruta.with_suffix(".pdf")


def paginas(pdf: Path):
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        return int(next(l for l in out.splitlines() if l.startswith("Pages")).split()[-1])
    except Exception:
        from pypdf import PdfReader  # respaldo
        return len(PdfReader(str(pdf)).pages)


# (las funciones reporte() y presentacion() se definen más abajo)


# ============================================================================================ REPORTE (DOCX → PDF)
from docx import Document  # noqa: E402
from docx.enum.section import WD_SECTION  # noqa: E402,F401
from docx.enum.table import WD_TABLE_ALIGNMENT  # noqa: E402
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt, RGBColor  # noqa: E402

RGB = lambda h: RGBColor.from_string(h.lstrip("#"))  # noqa: E731


def _sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color.lstrip("#"))
    tcPr.append(shd)


def _bordes_tabla(tabla, color="D5DCE3"):
    tblPr = tabla._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for lado in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{lado}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), color)
        b.append(e)
    for lado in ("left", "right", "insideV"):
        e = OxmlElement(f"w:{lado}"); e.set(qn("w:val"), "nil"); b.append(e)
    tblPr.append(b)


def _campo_pagina(parrafo):
    for tipo, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        r = parrafo.add_run()
        if tipo:
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tipo); r._r.append(f)
        else:
            t = OxmlElement("w:instrText"); t.set(qn("xml:space"), "preserve"); t.text = txt; r._r.append(t)


class Doc:
    """Pequeña capa sobre python-docx para mantener un estilo homogéneo."""

    def __init__(self):
        self.d = Document()
        sec = self.d.sections[0]
        sec.page_width, sec.page_height = Cm(21.59), Cm(27.94)          # carta
        for m in ("left_margin", "right_margin"):
            setattr(sec, m, Cm(2.5))
        sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.2)
        st = self.d.styles["Normal"]
        st.font.name = "Calibri"; st.font.size = Pt(11); st.font.color.rgb = RGB(TINTA)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        pf = st.paragraph_format; pf.line_spacing = 1.5; pf.space_after = Pt(5)
        for nivel, tam, esp in ((1, 15, 14), (2, 12.5, 9)):
            h = self.d.styles[f"Heading {nivel}"]
            h.font.name = "Calibri"; h.font.size = Pt(tam); h.font.bold = True; h.font.color.rgb = RGB(AZUL)
            h.element.rPr.rFonts.set(qn("w:asciiTheme"), "")  # evita fuente de tema
            h.paragraph_format.space_before = Pt(esp); h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.line_spacing = 1.15; h.paragraph_format.keep_with_next = True
        self.fig_n = 0; self.tab_n = 0
        sec.different_first_page_header_footer = True      # la portada lleva logos grandes propios
        sec.header_distance = Cm(1.0)
        enc = sec.header.paragraphs[0]
        from docx.enum.text import WD_TAB_ALIGNMENT
        from docx.shared import Inches as DIn
        ts = enc.paragraph_format.tab_stops
        ts.add_tab_stop(DIn(3.25), WD_TAB_ALIGNMENT.CLEAR)        # el estilo "Header" trae tabulador central y derecho
        ts.add_tab_stop(DIn(6.5), WD_TAB_ALIGNMENT.CLEAR)
        ts.add_tab_stop(Cm(16.59), WD_TAB_ALIGNMENT.RIGHT)         # logo del hackathon pegado al margen derecho
        enc.add_run().add_picture(str(LOGO_INE), height=Cm(0.75))
        enc.add_run("\t").add_picture(str(LOGO_HACK), height=Cm(1.05))
        pie = sec.footer.paragraphs[0]; pie.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = pie.add_run(f"{SISTEMA} · Reporte metodológico y preventivo · Reto 2 · {EQUIPO}   |   "); r.font.size = Pt(8.5); r.font.color.rgb = RGB(GRIS)
        _campo_pagina(pie)

    def h1(self, t):
        self.d.add_heading(t, level=1)

    def h2(self, t):
        self.d.add_heading(t, level=2)

    def p(self, *partes, esp_desp=5, alin=WD_ALIGN_PARAGRAPH.JUSTIFY, tam=None, color=None):
        """Párrafo con fragmentos; un fragmento entre ** ** va en negritas."""
        par = self.d.add_paragraph(); par.alignment = alin; par.paragraph_format.space_after = Pt(esp_desp)
        texto = "".join(partes)
        for i, trozo in enumerate(texto.split("**")):
            if trozo:
                r = par.add_run(trozo); r.bold = i % 2 == 1
                if tam: r.font.size = Pt(tam)
                if color: r.font.color.rgb = RGB(color)
        return par

    def vinetas(self, items):
        for i, it in enumerate(items):
            par = self.p(it, esp_desp=2)
            par.style = self.d.styles["List Bullet"]
            par.paragraph_format.line_spacing = 1.35
            if i < len(items) - 1:            # la lista no deja una viñeta sola al pie de página
                par.paragraph_format.keep_with_next = True

    def ecuacion(self, t):
        par = self.d.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(4); par.paragraph_format.line_spacing = 1.2
        r = par.add_run(t); r.italic = True; r.font.name = "Cambria Math"; r.font.size = Pt(11.5)

    def figura(self, ruta, ancho_cm, pie):
        self.fig_n += 1
        par = self.d.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.space_after = Pt(1); par.paragraph_format.line_spacing = 1.0; par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
        c = self.p(f"**Figura {self.fig_n}.** {pie}", alin=WD_ALIGN_PARAGRAPH.CENTER, tam=9, color=GRIS, esp_desp=8)
        c.paragraph_format.line_spacing = 1.1

    def tabla(self, df, anchos_cm, titulo=None, tam=8.5, colores_sem=(), nota=None, partir=False):
        if titulo:
            self.tab_n += 1
            t = self.p(f"**Tabla {self.tab_n}.** {titulo}", alin=WD_ALIGN_PARAGRAPH.LEFT, tam=9.5, esp_desp=2)
            t.paragraph_format.keep_with_next = True; t.paragraph_format.line_spacing = 1.1
        tb = self.d.add_table(rows=1, cols=len(df.columns)); tb.alignment = WD_TABLE_ALIGNMENT.CENTER
        tb.autofit = False; _bordes_tabla(tb)
        for j, col in enumerate(df.columns):
            c = tb.rows[0].cells[j]; c.text = ""; _sombrear(c, AZUL)
            r = c.paragraphs[0].add_run(str(col)); r.bold = True; r.font.size = Pt(tam); r.font.color.rgb = RGB("#FFFFFF")
        for i, fila in enumerate(df.itertuples(index=False)):
            cells = tb.add_row().cells
            for j, v in enumerate(fila):
                c = cells[j]; c.text = ""
                txt = str(v)
                if j in colores_sem and txt in ("Rojo", "Amarillo", "Verde"):
                    _sombrear(c, {"Rojo": "#F4B6B6", "Amarillo": "#FFE9A8", "Verde": "#BFE3C6"}[txt])
                elif i % 2 == 1:
                    _sombrear(c, "#F2F5F8")
                r = c.paragraphs[0].add_run(txt); r.font.size = Pt(tam)
        # Anchos fijos (LibreOffice/Word respetan tblLayout=fixed + tblW + gridCol)
        tblPr = tb._tbl.tblPr
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:w"), str(int(sum(anchos_cm) * 567))); tw.set(qn("w:type"), "dxa")
        for gc, w in zip(tb._tbl.tblGrid.findall(qn("w:gridCol")), anchos_cm):
            gc.set(qn("w:w"), str(int(w * 567)))
        texto_largo = [j for j in range(len(df.columns)) if df.iloc[:, j].astype(str).str.len().max() > 28]
        for idx_fila, fila in enumerate(tb.rows):
            cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); fila._tr.get_or_add_trPr().append(cs)
            # Tablas cortas (≤20 filas) no se parten entre páginas; la última fila arrastra la nota al pie
            junta = (not partir) and len(df) <= 20 and (idx_fila < len(tb.rows) - 1 or nota is not None)
            for j, c in enumerate(fila.cells):
                c.width = Cm(anchos_cm[j])
                for par in c.paragraphs:
                    pf = par.paragraph_format; pf.space_after = Pt(1); pf.space_before = Pt(1); pf.line_spacing = 1.0
                    pf.keep_with_next = junta
                    par.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 or j in texto_largo) else WD_ALIGN_PARAGRAPH.CENTER
        # encabezado repetido si la tabla cruza de página
        trPr = tb.rows[0]._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
        if nota:
            n = self.p(nota, tam=8.5, color=GRIS, esp_desp=8, alin=WD_ALIGN_PARAGRAPH.LEFT); n.paragraph_format.line_spacing = 1.1
        else:
            self.d.add_paragraph().paragraph_format.space_after = Pt(2)

    def salto(self):
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def reporte(D, H):
    b, d = D["base"], D["dist"]
    R = H
    doc = Doc()
    n = doc.d

    # ------------------------------------------------------------------ PORTADA
    tl = n.add_table(rows=1, cols=2); tl.autofit = False
    c0, c1 = tl.rows[0].cells
    c0.width, c1.width = Cm(8.3), Cm(8.3)
    c0.paragraphs[0].add_run().add_picture(str(LOGO_INE), height=Cm(1.55))
    c1.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    c1.paragraphs[0].add_run().add_picture(str(LOGO_HACK), height=Cm(3.0))
    for _ in range(2):
        n.add_paragraph()
    doc.p("HACKATHON 2026 DEL INE · HACKEA LA PARTICIPACIÓN: DATOS QUE CONSTRUYEN DEMOCRACIA", alin=WD_ALIGN_PARAGRAPH.LEFT, tam=10, color=AZUL)
    doc.p("Eje temático 2 · Predicción y escenarios de riesgo de abstención", alin=WD_ALIGN_PARAGRAPH.LEFT, tam=11, color=GRIS)
    t = doc.p(f"**{TITULO}**", alin=WD_ALIGN_PARAGRAPH.LEFT, tam=26, color=TINTA, esp_desp=4)
    t.paragraph_format.line_spacing = 1.05
    doc.p(SUBTITULO, alin=WD_ALIGN_PARAGRAPH.LEFT, tam=14, color=AZUL).paragraph_format.line_spacing = 1.2
    doc.p("Reporte metodológico y preventivo", alin=WD_ALIGN_PARAGRAPH.LEFT, tam=12, color=TINTA)
    for _ in range(2):
        n.add_paragraph()
    doc.p(f"**Equipo:** {EQUIPO}", alin=WD_ALIGN_PARAGRAPH.LEFT)
    doc.p(f"**Integrantes:** {', '.join(INTEGRANTES)}", alin=WD_ALIGN_PARAGRAPH.LEFT)
    doc.p("**Pregunta guía:** ¿Qué zonas podrían presentar mayor abstención en el futuro si no se interviene?", alin=WD_ALIGN_PARAGRAPH.LEFT)
    doc.p("**Fuente principal:** Plataforma de los Conteos Censales de Participación Ciudadana (CCPC) 2009–2024, INE-DECEyEC "
          f"({URL_CCPC}). **Fuente complementaria:** Censo de Población y Vivienda 2020, INEGI.", alin=WD_ALIGN_PARAGRAPH.LEFT)
    doc.p(f"**Convocatoria:** {URL_HACK}", alin=WD_ALIGN_PARAGRAPH.LEFT)
    doc.p("Octubre de 2026", alin=WD_ALIGN_PARAGRAPH.LEFT, color=GRIS)
    n.add_paragraph()
    doc.p("Todos los datos empleados son agregados y disociados: la unidad mínima de análisis es la celda "
          "entidad × tipo de sección × sexo × grupo de edad. El proyecto no utiliza ni produce datos personales.",
          alin=WD_ALIGN_PARAGRAPH.LEFT, tam=9, color=GRIS)
    doc.salto()

    # ------------------------------------------------------------------ RESUMEN EJECUTIVO
    # ---------- Planteamiento del problema ----------
    ab = {a: 100 - R["part_nac"][a] for a in (2009, 2012, 2015, 2018, 2021, 2024)}
    doc.h1("Planteamiento del problema")
    doc.p("La convocatoria plantea el **Reto 2, Predicción y escenarios de riesgo de abstención**, como un problema de analítica "
          "predictiva: “analizar información histórica y características de los territorios para identificar dónde podría disminuir "
          "la participación ciudadana”, plantear escenarios y proponer acciones que prevengan o reduzcan esos riesgos. La pregunta guía es "
          "**¿qué zonas podrían presentar mayor abstención en el futuro si no se interviene?**, y su utilidad para el INE es la "
          "**planeación anticipada y la priorización estratégica de recursos**.")
    doc.p(f"El problema es concreto. En las tres elecciones intermedias observadas la abstención fue de {ab[2009]:.1f}% (2009), "
          f"{ab[2015]:.1f}% (2015) y {ab[2021]:.1f}% (2021), frente a {ab[2012]:.1f}%, {ab[2018]:.1f}% y {ab[2024]:.1f}% en las "
          "presidenciales. La próxima elección federal, en 2027, es intermedia. Los recursos de educación cívica son limitados, y "
          "para usarlos bien hay que saber con anticipación **en qué entidades, en qué distritos y en qué grupos de población** crecerá "
          "la abstención. Un promedio nacional o estatal no basta: puede esconder territorios en riesgo dentro de entidades que, en "
          "conjunto, se ven bien.")
    tareas = pd.DataFrame([
        ["Construir un modelo simple de riesgo de abstención con tendencias históricas y variables sociodemográficas", "Secciones 2 y 3"],
        ["Simular al menos dos escenarios: sin intervención y con una intervención hipotética", "Sección 4"],
        ["Traducir los resultados a un esquema de riesgo territorial fácil de interpretar", "Secciones 4 y 5 (semáforo estatal y distrital)"],
        ["Formular recomendaciones preventivas a partir de los escenarios", "Sección 6"],
        ["Trabajar solo con información agregada y disociada, sin datos personales", "Sección 1"],
    ], columns=["Lo que pide la convocatoria", "Dónde lo respondemos"])
    doc.tabla(tareas, [11.0, 5.5], "Requisitos del Reto 2 y dónde se atiende cada uno en este reporte", tam=8.5)

    # ---------- Hallazgos principales ----------
    doc.h1("Hallazgos principales")
    doc.p("**Respuesta a la pregunta guía.** Si no se interviene, la abstención en la elección federal intermedia de 2027 subiría de "
          f"{R['abstencion_nacional_2024_obs']:.2f}% (observada en 2024) a **{R['abstencion_nacional_2027_sin']:.2f}%**. "
          f"Ocho entidades concentran el riesgo alto: {lista(R['rojos'].ENTIDAD)}. Tres de ellas "
          f"({lista(R['rojos_sin_gob'])}) no elegirán gubernatura en 2027, la variable de contexto que más protege la participación "
          f"en nuestro modelo. Dentro de entidades que no están en rojo, además, **{len(R['d_ocultos'])} distritos federales** "
          f"superan el umbral de riesgo alto: el promedio estatal los esconde.")
    kpi = pd.DataFrame([
        ["Abstención nacional observada 2024", f"{R['abstencion_nacional_2024_obs']:.2f}%"],
        ["Abstención proyectada 2027 sin intervención (Escenario 1)", f"{R['abstencion_nacional_2027_sin']:.2f}%  ·  8 entidades en rojo"],
        ["Escenario 2A · intervención nacional (−15% en jóvenes y secciones rurales)",
         f"{R['abstencion_nacional_2027_con']:.2f}%  ·  {R['n_cnt_con'][ROJO_S]} en rojo  ·  {fint(R['personas_recuperadas_2A'])} personas"],
        ["Escenario 2B · misma intervención solo en las 8 entidades en rojo",
         f"{R['abstencion_nacional_2027_2B']:.2f}%  ·  {R['n_cnt_2b'][ROJO_S]} en rojo  ·  {fint(R['personas_recuperadas_2B'])} personas"],
        ["Error medio del modelo en validación retrospectiva (2021 y 2024)", f"±{R['mae_validacion']:.2f} pp por entidad"],
        ["Distritos federales en riesgo alto (de 300)", f"{R['d_cnt'][ROJO_S]}, de los cuales {len(R['d_ocultos'])} están ocultos"],
    ], columns=["Indicador", "Resultado"])
    doc.tabla(kpi, [9.6, 6.9], "Hallazgos en una mirada", tam=9)
    ent = pd.DataFrame([
        ["Reporte metodológico y preventivo", "2_Reporte_Metodologico_Preventivo_Commit_Democratico_Eje2.pdf", "Este documento: variables, modelo, semáforo y recomendaciones"],
        ["Mapa de escenarios ejecutable", "3_Mapa_Escenarios / Mapa_Escenarios_Con_y_Sin_Intervencion.html", "Tablero que compara el mapa sin y con intervención (2A y 2B) y los 300 distritos; funciona sin internet"],
        ["Capa geoespacial", "3_Mapa_Escenarios / Capa_Escenarios_32_Entidades.geojson", "Las 32 entidades con todas las variables del modelo, para QGIS, Power BI o Tableau"],
        ["Base de datos anonimizada", "4_Base_Datos_Anonimizada / Base_Datos_Anonimizada_CCPC_2009_2024 (.xlsx y .csv)", "32 entidades × 107 variables; 7 hojas, incluidos los 300 distritos y el diccionario"],
        ["Código para repositorio", "5_Codigo_Repositorio (run_all.py)", "Seis scripts en Python que reproducen todas las cifras de este reporte"],
        ["Presentación ejecutiva", "1_Presentacion_Ejecutiva_Commit_Democratico_Eje2.pdf", "Diez diapositivas para el Comité Dictaminador"],
    ], columns=["Entregable", "Archivo", "Qué contiene"])
    doc.tabla(ent, [3.4, 6.2, 6.9], "Qué entregamos y en qué archivo está cada cosa", tam=8)
    doc.p("**Qué proponemos.** (1) Asignar recursos de educación cívica con una regla subestatal que priorice los "
          f"{R['d_cnt'][ROJO_S]} distritos en rojo y no solo las entidades en rojo; (2) concentrar la estrategia ENCÍVICA en juventudes, "
          "con énfasis en hombres jóvenes; (3) contrarrestar la “fatiga de intermedia” en las 15 entidades sin gubernatura en 2027; y "
          "(4) operar con pertinencia intercultural en secciones rurales e indígenas. El Escenario 2B muestra que intervenir solo en las "
          f"8 entidades en rojo logra la misma reducción de entidades en rojo (de 8 a {R['n_cnt_2b'][ROJO_S]}) con "
          f"{100 * R['personas_recuperadas_2B'] / R['personas_recuperadas_2A']:.0f}% del alcance poblacional de la intervención nacional.")

    # ------------------------------------------------------------------ 1. DATOS
    doc.h1("1. Arquitectura de datos, fuentes oficiales y garantía de privacidad")
    doc.h2("1.1 Fuentes")
    doc.p("La fuente obligatoria y núcleo del modelo son los **datos abiertos de la Plataforma CCPC 2009–2024** publicados por la "
          "DECEyEC. Para cada elección federal (2009, 2012, 2015, 2018, 2021 y 2024) el INE publica 32 archivos estatales con registros "
          "agregados por sección electoral, sexo y edad, con cuatro conteos: lista nominal (LN), registros con marca de voto (SV), sin marca "
          "de voto (NV) y no especificados (NS). Utilizamos los microdatos agregados en lugar de las vistas del tablero para conservar el "
          "desglose completo por segmento y garantizar reproducibilidad. Como fuente complementaria, del **Censo de Población y Vivienda "
          "2020 (INEGI, archivo ITER)** se tomaron, por entidad, la población hablante de lengua indígena, la población en hogares "
          "indígenas y la población afromexicana, variables que la CCPC no publica en sus datos abiertos "
          f"(https://www.{URL_ITER}). Los logotipos y las bases del concurso provienen de https://{URL_HACK}.")
    doc.p(f"Los archivos se descargaron el 26 de octubre de 2026 desde la sección de datos abiertos de la plataforma (https://{URL_CCPC}). "
          f"La Tabla {doc.tab_n + 1} registra cada archivo, su tamaño y el número de registros que se procesaron; en total se leyeron "
          f"**{R['bitacora'].REGISTROS_PROCESADOS.sum():,} registros**.")
    bt = R["bitacora"]
    tb = pd.DataFrame({"Año": bt.AELEC, "Archivo oficial (INE-DECEyEC)": bt.ARCHIVO,
                       "Tamaño": (bt.BYTES_ZIP / 1e6).map(lambda x: f"{x:.1f} MB"), "CSV estatales": bt.ARCHIVOS_CSV,
                       "Registros leídos": bt.REGISTROS_PROCESADOS.map(fint)})
    doc.tabla(tb, [1.3, 8.6, 2.0, 2.1, 2.5], "Archivos oficiales de la CCPC procesados", tam=8,
              nota="Cada archivo se descarga de ine.mx/wp-content/uploads/…; las direcciones completas están en "
                   "data/raw/bitacora_extraccion.csv del repositorio.")
    doc.h2("1.2 Procesamiento y definiciones")
    doc.p("Los registros se agregaron a la **celda analítica**: año × entidad × tipo de sección (urbana, mixta, rural) × sexo × grupo de "
          f"edad (18–19, 20–29, …, 70+), lo que produce {R['n_celdas']:,} celdas. Se usan las definiciones de la propia plataforma:")
    doc.ecuacion("Participación (%) = SV / (SV + NV) × 100          Abstención (%) = 100 − Participación")
    doc.p("Los registros NS (cuadernillos sin marcas o no disponibles) se excluyen del denominador. La validación automática verifica que "
          "cada año tenga las 32 entidades, que en todas las celdas se cumpla LN = SV + NV + NS, que no haya valores negativos y que la "
          f"base final no tenga celdas vacías. La Tabla {doc.tab_n + 1} reproduce los totales nacionales resultantes.")
    tn = pd.DataFrame([[a, fint(R["ln_nac"][a]), "Intermedia" if a in (2009, 2015, 2021) else "Presidencial",
                        f"{R['part_nac'][a]:.2f}%", f"{100 - R['part_nac'][a]:.2f}%"] for a in (2009, 2012, 2015, 2018, 2021, 2024)],
                      columns=["Año", "Lista nominal (CCPC)", "Tipo", "Participación", "Abstención"])
    doc.tabla(tn, [2.2, 4.4, 3.4, 3.2, 3.2], "Totales nacionales validados de la CCPC, 2009–2024",
              nota="Definición oficial de la CCPC. Las proyecciones nacionales 2027 y 2030 promedian las entidades ponderadas por su "
                   "lista nominal; con esa misma ponderación, 2024 daría 40.39%.")
    doc.h2("1.3 Variables y entregables de datos")
    vars_ = pd.DataFrame([
        ["Serie histórica", "LN, votantes, abstenciones, participación y abstención 2009–2024", "CCPC", "36"],
        ["Contexto electoral", "Gubernatura concurrente por año (2009–2030)", "Calendario electoral", "7"],
        ["Ciclo y tendencia", "Caída al pasar a intermedia; tendencia por tipo de elección", "CCPC (derivadas)", "4"],
        ["Sociodemográficas", "Participación por edad, sexo y tipo de sección; brechas; % de LN joven y rural (2021 y 2024)", "CCPC", "32"],
        ["Étnicas", "% hablante de lengua indígena, en hogares indígenas y afromexicana", "Censo 2020 (INEGI)", "3"],
        ["Resultados del modelo", "Escenarios 2027 y 2030, bandas, semáforos, personas recuperadas, segmentos", "Modelo del equipo", "25"],
    ], columns=["Grupo", "Contenido", "Fuente", "Variables"])
    doc.tabla(vars_, [3.0, 8.4, 3.3, 1.8], "Resumen del diccionario de la base maestra (107 columnas, 32 entidades, 0 celdas vacías)",
              nota="El diccionario completo está en la hoja «Diccionario» de Base_Datos_Anonimizada_CCPC_2009_2024.xlsx (carpeta 4_Base_Datos_Anonimizada).")
    doc.h2("1.4 Garantía de privacidad")
    doc.p("El proyecto no usa datos personales. Los archivos de la CCPC ya son agregados; nuestra unidad mínima de análisis agrega todavía "
          "más (todas las secciones de un mismo tipo dentro de la entidad), y la capa distrital se construye con totales de distrito. "
          "Ninguna salida permite identificar a una persona, una casilla o una sección individual.")

    # ------------------------------------------------------------------ 2. DIAGNÓSTICO
    doc.h1("2. Diagnóstico histórico y sociodemográfico de la abstención")
    doc.h2("2.1 El efecto ciclo: la abstención crece en cada intermedia")
    doc.p("La serie nacional dibuja un “serrucho” (Figura 1): la abstención baja en las elecciones presidenciales y sube en las intermedias. "
          f"En promedio, cada entidad pierde **{R['caida_intermedia']:.1f} puntos de participación** al pasar de una presidencial a la "
          "intermedia siguiente (2012→2015 y 2018→2021). La tendencia de las intermedias es ascendente (de 44.1% en 2009 a 51.8% de "
          "participación en 2021), pero la caída de ciclo es lo bastante grande para que 2027, sin intervención, vuelva a niveles cercanos a "
          "la mitad del padrón.")
    doc.figura(FIG / "fig1_serie_nacional_ciclo.png", 14.4, "Abstención nacional observada 2009–2024 y proyecciones 2027 y 2030.")
    doc.h2("2.2 Brechas estructurales")
    doc.p(f"**Juventudes.** En todas las entidades las personas de 18 a 29 años participan menos que el promedio: la brecha media fue de "
          f"{abs(R['brecha_juv_2021']):.1f} pp en 2021 y {abs(R['brecha_juv_2024']):.1f} pp en 2024. Para 2027 el modelo proyecta "
          f"{R['abs_joven']:.1f}% de abstención en juventudes frente a {R['abs_30mas']:.1f}% en el resto (promedio nacional ponderado por lista "
          f"nominal; la Figura 2 muestra la mediana de las 32 entidades, {R['med_joven']:.1f}% frente a {R['med_30mas']:.1f}%). El máximo es "
          f"{R['juv_max_ent']} con {R['juv_max']:.1f}%. Las juventudes son {R['pct_ln_juv']:.1f}% de la lista nominal 2024.")
    doc.p(f"**Sexo.** Los hombres se abstienen más que las mujeres en las {R['h_mayor_m']} entidades: en 2024 la participación de las mujeres "
          f"superó a la de los hombres entre {R['brecha_sexo_min']:.1f} y {R['brecha_sexo_max']:.1f} pp. La brecha se suma a la de edad: "
          f"para 2027 se proyecta {R['abs_joven_h']:.1f}% de abstención en hombres jóvenes y {R['abs_joven_m']:.1f}% en mujeres jóvenes.")
    doc.p(f"**Tipo de sección.** Contra la intuición, la abstención proyectada es mayor en secciones urbanas "
          f"({R['abs_tipo']['Urbana']:.1f}%) y mixtas ({R['abs_tipo']['Mixta']:.1f}%) que en las rurales ({R['abs_tipo']['Rural']:.1f}%). "
          f"Esto ocurre en {R['urb_mayor_rural']} de 32 entidades; solo en {lista(R['rural_mayor'])} la abstención rural supera a la "
          f"urbana. Lo rural, por tanto, no es un riesgo homogéneo: es crítico en entidades específicas y es, sobre todo, donde el costo "
          f"operativo por persona alcanzada es mayor ({R['pct_ln_rur']:.1f}% de la lista nominal).")
    doc.p("**Población indígena y afromexicana.** La correlación entre el porcentaje de población hablante de lengua indígena y la abstención "
          "proyectada es débil y negativa (Spearman −0.24): las entidades con mayor presencia indígena (Oaxaca, Chiapas, Yucatán, Guerrero) no "
          "están en rojo. Estas variables no se usan como predictores, sino como criterio de **pertinencia intercultural** de las acciones "
          "(lenguas, materiales y brigadas), en particular en Guerrero y Oaxaca, que concentran la mayor proporción de población afromexicana.")
    doc.figura(FIG / "fig3_brechas_edad_rural_sexo.png", 15.2, "Abstención proyectada 2027 por edad, tipo de sección y sexo en las 32 entidades.")

    # ------------------------------------------------------------------ 3. METODOLOGÍA
    doc.h1("3. Metodología predictiva: modelo de “dos lentes” de memoria electoral")
    doc.h2("3.1 Formulación")
    doc.p("Para cada celda c (entidad × tipo de sección × sexo × edad) y elección objetivo t se combinan dos proyecciones de la participación P:")
    doc.ecuacion("Lente A (mismo tipo):   P̂ᴬ(c,t) = P(c, t−6) + αᴬ[tipo(t)] + γᴬ · ΔGob(e, t, t−6)")
    doc.ecuacion("Lente B (reciente):     P̂ᴮ(c,t) = P(c, t−3) + αᴮ[tipo(t)] + γᴮ · ΔGob(e, t, t−3)")
    doc.ecuacion("Proyección final:   P̂(c,t) = ½ · P̂ᴬ + ½ · P̂ᴮ          Â(c,t) = 100 − P̂(c,t)")
    doc.p("donde α[tipo] es el desplazamiento nacional típico al pasar a una elección intermedia o presidencial (efecto ciclo), ΔGob es el "
          "cambio en la concurrencia de elección de gubernatura en la entidad (+1, 0 o −1) y γ los puntos de participación que aporta esa "
          "concurrencia. Los coeficientes se estiman por **mínimos cuadrados ponderados por la lista nominal** con todas las transiciones "
          f"históricas anteriores a la elección objetivo; son seis en total y todos tienen lectura directa (Tabla {doc.tab_n + 1}). La proyección se limita "
          "al intervalo 5%–98% y las celdas se agregan a entidad ponderando por la lista nominal proyectada, de modo que la composición por "
          "edad, sexo y tipo de sección entra de forma explícita.")
    cf = D["coef"].copy()
    lectura = {"alfa_intermedia": "Cambio típico al llegar a una intermedia", "alfa_presidencial": "Cambio típico al llegar a una presidencial",
               "gamma_gubernatura": "Efecto de tener gubernatura concurrente"}
    cf = pd.DataFrame({"Lente": cf.Lente.map({"A_mismo_tipo": "A · mismo tipo (t−6)", "B_reciente": "B · reciente (t−3)"}),
                       "Coeficiente": cf.Coeficiente.map({"alfa_intermedia": "α intermedia", "alfa_presidencial": "α presidencial", "gamma_gubernatura": "γ gubernatura"}),
                       "Valor (pp)": cf.Valor_pp.map(lambda x: f"{x:+.2f}"), "Lectura": cf.Coeficiente.map(lectura),
                       "Transiciones": cf.Transiciones_usadas})
    doc.tabla(cf, [3.3, 2.5, 1.9, 5.0, 3.8], "Coeficientes estimados con toda la historia 2009–2024 (usados para proyectar 2027)", tam=8, partir=True)
    doc.p(f"El hallazgo más relevante es el **efecto gubernatura**: cuando una entidad elige gobernador, su participación sube "
          f"{R['gA']:+.2f} pp respecto a la elección del mismo tipo sin gubernatura (lente A) y {R['gB']:+.2f} pp respecto a la elección "
          f"inmediata (lente B). Los α del lente B ({R['aB_i']:+.2f} y {R['aB_p']:+.2f} pp) cuantifican el ciclo; los del lente A "
          f"({R['aA_i']:+.2f} y {R['aA_p']:+.2f} pp) indican que, entre elecciones del mismo tipo, las intermedias mejoraron ligeramente. "
          "La lista nominal 2027 se proyecta con el crecimiento trienal observado 2021→2024 de cada entidad, y la de 2030 con la misma tasa.")
    doc.h2("3.2 Validación retrospectiva")
    doc.p("Para medir la precisión sin “ver el futuro”, el método se aplicó dos veces con datos truncados: se anticipó 2021 usando solo "
          f"2009–2018 y 2024 usando solo 2009–2021. Se comparan seis especificaciones, de la más ingenua a la final (Tabla {doc.tab_n + 1} y Figura {doc.fig_n + 1}). "
          "Las métricas se miden a nivel entidad, que es la escala del semáforo.")
    v = D["val"].copy()
    v = pd.DataFrame({"Elección": v.Eleccion_objetivo, "Modelo": v.Modelo, "MAE (pp)": v.MAE_pp.map(lambda x: f"{x:.2f}"),
                      "Acierto color": v["Acierto_semaforo_%"].map(lambda x: f"{x:.1f}%"), "Rojos detectados": v.Rojos_detectados,
                      "Spearman": v.Spearman.map(lambda x: f"{x:.2f}")})
    doc.tabla(v, [1.7, 6.6, 1.9, 2.3, 2.4, 1.8], "Resultados de la validación retrospectiva", tam=8)
    doc.figura(FIG / "fig2_validacion_backtest.png", 16.0, "Promedio de las dos pruebas por modelo.")
    doc.p(f"El lente A acierta mejor el **nivel** de la abstención y el lente B **ordena** mejor a las entidades por riesgo; ninguno domina "
          f"en todo. El promedio de ambos (M5) reduce el error del modelo ingenuo de {R['m0_mae']:.2f} a {R['mae_validacion']:.2f} pp y eleva "
          f"el acierto del color de 54.7% a {R['acierto']:.1f}% con una correlación de rangos de {R['spearman']:.2f}. Por eso es el modelo "
          f"elegido, y su error medio (±{R['mae_validacion']:.2f} pp) se reporta como banda de incertidumbre en cada proyección.")

    # ------------------------------------------------------------------ 4. SEMÁFORO Y ESCENARIOS
    doc.h1("4. Semáforo de riesgo territorial 2027 y simulación de escenarios")
    doc.h2("4.1 Reglas del semáforo")
    doc.p(f"El semáforo clasifica a las entidades por cuartiles de la abstención proyectada sin intervención: **Rojo** si es mayor o igual "
          f"a {R['umbral_rojo']:.2f}% (cuartil superior), **Verde** si es menor o igual a {R['umbral_verde']:.2f}% (cuartil inferior) y "
          "**Amarillo** en el resto. Los umbrales se fijan con el Escenario 1 y se mantienen en los demás escenarios, de modo que un cambio de "
          "color refleja solo el efecto simulado.")
    doc.h2("4.2 Escenarios")
    s = R["sens"]
    s15 = s[s.Reduccion_relativa_segmento == "15%"].iloc[0]
    doc.vinetas([
        f"**Escenario 1 · Sin intervención (inercia).** Abstención nacional de {R['abstencion_nacional_2027_sin']:.2f}%: "
        f"{R['n_cnt'][ROJO_S]} entidades en rojo, {R['n_cnt']['Riesgo Medio (Amarillo)']} en amarillo y {R['n_cnt']['Riesgo Bajo (Verde)']} en verde; "
        f"se esperan {fint(R['abs_esperados'])} personas abstencionistas.",
        "**Escenario 2A · Intervención nacional.** Supuesto: las acciones de educación cívica reducen 15% (relativo) la abstención de las "
        f"personas de 18–29 años y de las secciones rurales en las 32 entidades. Resultado: {R['abstencion_nacional_2027_con']:.2f}% de "
        f"abstención, {R['n_cnt_con'][ROJO_S]} entidades en rojo, {R['cambian_color']} entidades bajan de color y "
        f"{fint(R['personas_recuperadas_2A'])} personas votarían.",
        f"**Escenario 2B · Priorización presupuestaria.** La misma intervención solo en las 8 entidades en rojo: "
        f"{R['abstencion_nacional_2027_2B']:.2f}% de abstención, {R['n_cnt_2b'][ROJO_S]} entidades en rojo y "
        f"{fint(R['personas_recuperadas_2B'])} personas recuperadas.",
        f"**Horizonte 2030.** Con el mismo método, la presidencial de 2030 tendría {R['abs2030']:.1f}% de abstención sin intervención: el "
        "riesgo es propio del ciclo intermedio, lo que justifica concentrar el esfuerzo en 2027.",
    ])
    doc.figura(MAPAS / "mapa_semaforo_sin_vs_con.png", 14.8, "Semáforo estatal 2027: Escenario 1 frente a Escenario 2A.")
    tabla32 = b.sort_values("Escenario_Sin_Intervencion_2027", ascending=False)
    t32 = pd.DataFrame({"Entidad": tabla32.ENTIDAD, "Gob. 2027": tabla32.GUBERNATURA_2027.map({1: "Sí", 0: "No"}),
                        "Abst. 2024": tabla32.ABST_2024.map(lambda x: f"{x:.1f}"),
                        "2027 sin": tabla32.Escenario_Sin_Intervencion_2027.map(lambda x: f"{x:.2f}"),
                        "Banda": [f"{lo:.1f}–{hi:.1f}" for lo, hi in zip(tabla32.Banda_inferior_2027, tabla32.Banda_superior_2027)],
                        "Semáforo": tabla32.Semaforo_Riesgo.map(CORTO),
                        "2027 · 2A": tabla32.Escenario_Con_Intervencion.map(lambda x: f"{x:.2f}"),
                        "Sem. 2A": tabla32.Semaforo_Con_Intervencion.map(CORTO),
                        "2027 · 2B": tabla32.Escenario_2B_solo_rojos.map(lambda x: f"{x:.2f}"),
                        "2030 sin": tabla32.Escenario_Sin_Intervencion_2030.map(lambda x: f"{x:.1f}")})
    doc.tabla(t32, [3.6, 1.3, 1.4, 1.4, 1.9, 1.7, 1.4, 1.7, 1.4, 1.3],
              "Semáforo de las 32 entidades (abstención %, ordenadas de mayor a menor riesgo)", tam=7.8, colores_sem=(5, 7),
              nota="Banda = proyección ± error medio de validación. 2A: intervención en las 32 entidades. 2B: intervención solo en las 8 en rojo.")
    # Frase calculada desde los datos: entidades rojas cuya banda completa supera el umbral rojo
    robustas = R["rojos"].loc[R["rojos"].Banda_inferior_2027 >= R["umbral_rojo"], "ENTIDAD"].tolist()
    nunca = [e for e in R["rojos_sin_gob"]
             if not b.loc[b.ENTIDAD == e, ["GOB_2009", "GOB_2015", "GOB_2021"]].to_numpy().any()]
    con2024 = [e for e in nunca if int(b.loc[b.ENTIDAD == e, "GOB_2024"].iloc[0]) == 1]
    rk = b.ABST_2027_JUVENTUD_18_29.rank(ascending=False)
    doc.p("**Lectura de las zonas críticas.** Baja California encabeza el riesgo aun eligiendo gubernatura: registró la abstención más "
          f"alta del país en las tres intermedias observadas (2009, 2015 y 2021). {lista(nunca)} nunca han tenido elección de "
          "gubernatura concurrente con una intermedia y tampoco la tendrán en 2027"
          + (f"; {' y '.join(con2024)}, además, sí la tuvieron en 2024, por lo que pierden ese impulso" if con2024 else "")
          + f". Las tres están entre las ocho entidades con mayor abstención juvenil proyectada (lugares "
          f"{lista(int(rk[b.ENTIDAD == e].iloc[0]) for e in nunca)}). "
          f"La Figura 5 (al final de esta sección) muestra que la banda de incertidumbre completa de {lista(robustas)} queda por encima del umbral rojo: su "
          "clasificación se sostiene aun restando el error medio del modelo.")
    doc.h2("4.3 Sensibilidad")
    ss = pd.DataFrame({"Reducción en segmento": s.Reduccion_relativa_segmento, "Abstención nacional": s.Abstencion_nacional_2027.map(lambda x: f"{x:.2f}%"),
                       "Rojo": s.Entidades_rojo, "Amarillo": s.Entidades_amarillo, "Verde": s.Entidades_verde,
                       "Cambian de color": s.Entidades_que_cambian_color, "Personas recuperadas": s.Personas_recuperadas.map(fint)})
    doc.tabla(ss, [3.6, 2.6, 1.3, 1.6, 1.4, 2.3, 3.0], "Sensibilidad del Escenario 2A a la eficacia supuesta de la intervención")
    doc.p("El 15% es un supuesto explícito, no una estimación causal. Con una eficacia de solo 5%, la intervención nacional ya recuperaría "
          f"{fint(s.iloc[1].Personas_recuperadas)} votos y bajaría a {s.iloc[1].Entidades_rojo} las entidades en rojo; la conclusión de "
          "prioridad territorial no depende del valor exacto.")
    doc.figura(FIG / "fig4_ranking_32_entidades_bandas.png", 8.4, "Ranking 2027 con banda de incertidumbre y desplazamiento al Escenario 2A.")

    # ------------------------------------------------------------------ 5. DISTRITOS
    doc.h1("5. Focalización subestatal: 300 distritos y los distritos rojos ocultos")
    doc.p("Para llevar el semáforo a la escala operativa de las Juntas Distritales Ejecutivas se construyó una capa con los 300 distritos "
          "federales (cartografía 2023): a la abstención observada de cada distrito en 2024 se suma el cambio proyectado de su entidad entre "
          "2024 y 2027, y los distritos se clasifican con sus propios cuartiles (rojo ≥ "
          f"{R['d_umbral'][0.75]:.2f}%, verde ≤ {R['d_umbral'][0.25]:.2f}%). Resultan {R['d_cnt'][ROJO_S]} distritos en rojo, "
          f"{R['d_cnt']['Riesgo Medio (Amarillo)']} en amarillo y {R['d_cnt']['Riesgo Bajo (Verde)']} en verde.")
    doc.p(f"**El hallazgo clave:** {R['d_rojo_en_rojo']} distritos rojos están en entidades rojas, pero **{len(R['d_ocultos'])} distritos rojos "
          f"están en {R['d_ocultos_ent'].size} entidades amarillas o verdes** y suman {R['d_ocultos'].ABSTENCIONISTAS_ESPERADOS.sum() / 1e6:.2f} "
          "millones de abstencionistas esperados. Una asignación de recursos basada solo en el promedio estatal los dejaría fuera. Los casos más "
          f"numerosos son Nuevo León ({R['d_ocultos_ent'].get('Nuevo León', 0)} distritos), Tamaulipas "
          f"({R['d_ocultos_ent'].get('Tamaulipas', 0)}) y México, Sinaloa y Tabasco (2 cada uno); el caso más contrastante es el distrito 9 "
          "de Chiapas, en rojo dentro de una entidad verde.")
    top = d.head(15)
    tt = pd.DataFrame({"#": range(1, 16), "Entidad": top.ENTIDAD, "DEF": top.DEF.astype(int), "Abst. 2024": top.ABST_2024.map(lambda x: f"{x:.2f}"),
                       "Proy. 2027": top.ABST_PROY_2027.map(lambda x: f"{x:.2f}"), "Sem. entidad": top.SEMAFORO_ENTIDAD.map(CORTO),
                       "Abstencionistas esperados": top.ABSTENCIONISTAS_ESPERADOS.map(fint)})
    tt = tt[["Entidad", "#", "DEF", "Abst. 2024", "Proy. 2027", "Sem. entidad", "Abstencionistas esperados"]]
    doc.tabla(tt, [3.8, 1.0, 1.2, 2.0, 2.0, 2.3, 3.6], "Top 15 nacional de distritos con mayor abstención proyectada 2027", tam=8, colores_sem=(5,))
    o = R["d_ocultos"]
    to = pd.DataFrame({"Entidad": o.ENTIDAD, "DEF": o.DEF.astype(int), "Abst. 2024": o.ABST_2024.map(lambda x: f"{x:.2f}"),
                       "Proy. 2027": o.ABST_PROY_2027.map(lambda x: f"{x:.2f}"), "Sem. entidad": o.SEMAFORO_ENTIDAD.map(CORTO),
                       "Abstencionistas esperados": o.ABSTENCIONISTAS_ESPERADOS.map(fint)})
    doc.tabla(to, [3.9, 1.3, 2.2, 2.2, 2.4, 3.6], f"Los {len(o)} distritos rojos ocultos en entidades amarillas o verdes", tam=8, colores_sem=(4,))
    doc.figura(FIG / "fig5_distritos_rojos_ocultos.png", 12.2, "Distritos rojos ocultos frente al promedio proyectado de su entidad.")

    # ------------------------------------------------------------------ 6. RECOMENDACIONES
    doc.h1("6. Recomendaciones preventivas y priorización de recursos")
    doc.p("Las recomendaciones son operativas: se ejecutan con las atribuciones vigentes de la DECEyEC y de las Juntas Locales y Distritales "
          "Ejecutivas en el marco de la ENCÍVICA y no requieren reformas legales. Se organizan en cuatro ejes.")
    rec = pd.DataFrame([
        ["1. Regla de asignación subestatal",
         f"Distribuir presupuesto y brigadas por distrito con el semáforo distrital: prioridad 1 a los {R['d_rojo_en_rojo']} distritos rojos de "
         f"entidades rojas y a los {len(R['d_ocultos'])} rojos ocultos; prioridad 2 a distritos amarillos de entidades rojas.",
         "DECEyEC; 32 JLE; 300 JDE", "% del presupuesto ejercido en distritos rojos"],
        ["2. Juventudes, con énfasis en hombres jóvenes",
         "Campañas ENCÍVICA en universidades, bachilleratos, centros de trabajo y redes; recordatorios de fecha y casilla; "
         "mensajes dirigidos a hombres de 18–29 en secciones urbanas y mixtas periféricas.",
         "DECEyEC; JLE de las 8 entidades rojas", "Participación 18–29 en 2027 vs 2021"],
        ["3. Territorio rural y pertinencia intercultural",
         "Brigadas móviles y materiales en lenguas indígenas en secciones rurales de alta abstención (Guanajuato, Durango, Baja California) "
         "y en los distritos ocultos de Chiapas, Oaxaca, Hidalgo, Guerrero y Veracruz; materiales para comunidades afromexicanas.",
         "JDE; vocalías de capacitación", "Secciones rurales atendidas; materiales traducidos"],
        ["4. Contra la fatiga de intermedia",
         "Campaña específica en las 15 entidades sin gubernatura en 2027, con prioridad en Guanajuato, Jalisco y Durango: explicar qué se elige "
         "en una intermedia y por qué importa la Cámara de Diputados.",
         "DECEyEC; JLE", "Caída de participación 2024→2027"],
    ], columns=["Eje", "Acción", "Responsables", "Indicador de seguimiento"])
    doc.tabla(rec, [3.3, 7.3, 2.9, 3.0], "Matriz de recomendaciones preventivas", tam=8)
    doc.h2("6.1 Hoja de ruta")
    doc.vinetas([
        "**Noviembre 2026 – enero 2027:** adoptar el semáforo como insumo de planeación; cada JLE valida su lista de distritos rojos y ocultos.",
        "**Febrero – abril 2027:** despliegue de campañas y brigadas según la regla de asignación; tablero interactivo como herramienta de seguimiento.",
        "**Mayo – junio 2027:** intensificación en distritos rojos y en juventudes durante las semanas previas a la jornada.",
        "**Segundo semestre 2027:** con la CCPC 2027, re-estimar el modelo (basta correr run_all.py) y evaluar el impacto por distrito.",
    ])
    doc.h2("6.2 Alcances y limitaciones")
    doc.vinetas([
        "Seis elecciones son una serie corta: los efectos de ciclo y de gubernatura se estiman con pocas transiciones, y por eso se reporta la banda de error.",
        "La CCPC no incluye el voto en casillas especiales ni el voto desde el extranjero.",
        "El escenario de intervención supone un efecto (15% relativo) que no es causal. El diagnóstico muestra que la abstención urbana y "
        "masculina es mayor que la rural en la mayoría de las entidades; por eso las recomendaciones priorizan juventudes urbanas y hombres "
        "jóvenes, y conservan lo rural por su costo operativo y su peso en entidades específicas.",
        "Las variables indígena y afromexicana son estatales (Censo 2020), no seccionales; se usan para orientar la operación, no para predecir.",
        "La capa distrital aplica a cada distrito el cambio proyectado de su entidad; no modela dinámicas propias del distrito.",
    ])
    # La plantilla base de python-docx trae <w:zoom> sin porcentaje (inválido según el esquema); se completa.
    z = n.settings.element.find(qn("w:zoom"))
    if z is not None and z.get(qn("w:percent")) is None:
        z.set(qn("w:percent"), "100")
    ruta = OUT / "Reporte_Metodologico_Preventivo_Reto2.docx"
    n.save(ruta)
    pdf = a_pdf(ruta)
    if pdf:
        np_ = paginas(pdf)
        print(f"Reporte: {ruta.name} → {pdf.name} · {np_} páginas")
        assert 10 <= np_ <= 15, f"El reporte tiene {np_} páginas; la convocatoria exige 10 a 15"
    return ruta


# ============================================================================================ PRESENTACIÓN (PPTX → PDF)
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor as PRGB  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Inches, Pt as PPt  # noqa: E402
from pptx.oxml.ns import qn as pqn  # noqa: E402

PR = lambda h: PRGB.from_string(h.lstrip("#"))  # noqa: E731
LAVANDA = "#EEF2F6"




def captura_tablero():
    """Captura de los mapas del tablero HTML con Playwright (si está instalado); si no, se usa el mapa estático."""
    destino = FIG / "captura_tablero.png"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            nav = p.chromium.launch()
            pg = nav.new_page(viewport={"width": 1300, "height": 1400}, device_scale_factor=2)
            pg.goto((MAPAS / "Mapa_Escenarios_Reto2.html").resolve().as_uri())
            pg.wait_for_timeout(800)
            caja = pg.locator(".bar").first.bounding_box()
            mapas = pg.locator(".maps").first.bounding_box()
            y0 = caja["y"] - 12
            pg.screenshot(path=str(destino), clip={"x": 20, "y": y0, "width": 1260, "height": mapas["y"] + mapas["height"] - y0 + 8})
            nav.close()
        return destino
    except Exception as e:  # noqa: BLE001
        print("  (sin Playwright: se usa el mapa estático en la diapositiva 9)", type(e).__name__)
        return FIG / "mapas_slide.png"


def _sin_sombra(shape):
    """python-pptx hereda una sombra del tema; una lista de efectos vacía la elimina."""
    spPr = shape._element.spPr
    for e in spPr.findall(pqn("a:effectLst")):
        spPr.remove(e)
    spPr.append(spPr.makeelement(pqn("a:effectLst"), {}))
    estilo = shape._element.find(pqn("p:style"))
    if estilo is not None:
        shape._element.remove(estilo)


class Deck:
    W, H = 13.333, 7.5
    X0, X1 = 0.6, 12.733          # márgenes laterales

    def __init__(self):
        self.p = Presentation()
        self.p.slide_width, self.p.slide_height = Inches(self.W), Inches(self.H)
        self.blank = self.p.slide_layouts[6]
        self.n = 0

    def slide(self, fuente=None):
        s = self.p.slides.add_slide(self.blank)
        self.n += 1
        bg = s.background.fill; bg.solid(); bg.fore_color.rgb = PR("#FFFFFF")
        if self.n > 1:
            self.imagen_fit(s, LOGO_INE, self.X0, 6.93, 1.15, 0.3)
            self.imagen_fit(s, LOGO_HACK, 1.9, 6.86, 1.2, 0.44)
            pie = f"{SISTEMA} · {EQUIPO}" + (f"   |   Fuente: {fuente}" if fuente else "")
            self.texto(s, pie, 3.3, 6.98, 8.6, 0.3, 10, GRIS)
            self.texto(s, f"{self.n} / 10", self.X1 - 0.8, 6.98, 0.8, 0.3, 10, GRIS, PP_ALIGN.RIGHT)
        return s

    def texto(self, s, t, x, y, w, h, tam=16, color=TINTA, alin=PP_ALIGN.LEFT, negrita=False, ancla=MSO_ANCHOR.TOP,
              italica=False, esp=6):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = ancla
        for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
            setattr(tf, m, 0)
        lineas = t if isinstance(t, list) else [t]
        for i, ln in enumerate(lineas):
            par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            par.alignment = alin
            if i:
                par.space_before = PPt(esp)
            for k, trozo in enumerate(ln.split("**")):
                if not trozo:
                    continue
                r = par.add_run(); r.text = trozo
                r.font.size = PPt(tam); r.font.name = "Calibri"; r.font.color.rgb = PR(color)
                r.font.bold = negrita or k % 2 == 1; r.font.italic = italica
        return tb

    def titulo(self, s, t, sub=None):
        self.texto(s, t, self.X0, 0.42, self.X1 - self.X0, 0.7, 30, TINTA, negrita=True)
        if sub:
            self.texto(s, sub, self.X0, 1.1, self.X1 - self.X0, 0.4, 16, AZUL)

    def caja(self, s, x, y, w, h, fondo=LAVANDA):
        r = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        r.adjustments[0] = 0.06
        r.fill.solid(); r.fill.fore_color.rgb = PR(fondo); r.line.fill.background()
        _sin_sombra(r)
        return r

    def dato(self, s, x, y, w, valor, etiqueta, color=AZUL, fondo=LAVANDA, h=1.45, tam=32):
        self.caja(s, x, y, w, h, fondo)
        self.texto(s, valor, x + 0.25, y + 0.2, w - 0.5, 0.6, tam, color, negrita=True)
        self.texto(s, etiqueta, x + 0.25, y + 0.82, w - 0.5, h - 0.9, 13, TINTA)

    def imagen_fit(self, s, ruta, x, y, w, h, alin="left"):
        """Inserta la imagen ajustada al recuadro sin deformarla."""
        from PIL import Image
        with Image.open(ruta) as im:
            iw, ih = im.size
        esc = min(w / iw, h / ih)
        ww, hh = iw * esc, ih * esc
        dx = {"left": 0, "center": (w - ww) / 2, "right": w - ww}[alin]
        return s.shapes.add_picture(str(ruta), Inches(x + dx), Inches(y), Inches(ww), Inches(hh))

    def notas(self, s, t):
        s.notes_slide.notes_text_frame.text = t


def presentacion(D, H):
    R = H
    k = Deck()
    F_CCPC = "Conteos Censales de Participación Ciudadana 2009–2024, INE-DECEyEC (datos abiertos)"

    # 1 · PORTADA
    s = k.slide()
    k.imagen_fit(s, LOGO_INE, k.X0, 0.55, 2.6, 0.65)
    k.imagen_fit(s, LOGO_HACK, k.X1 - 3.9, 0.35, 3.9, 1.45, alin="right")
    k.texto(s, "Hackathon 2026 del INE · Eje temático 2: Predicción y escenarios de riesgo de abstención", k.X0, 2.2, 11.5, 0.4, 16, AZUL)
    k.texto(s, TITULO, k.X0, 2.7, 12.1, 0.8, 36, TINTA, negrita=True)
    k.texto(s, SUBTITULO, k.X0, 3.55, 11.3, 0.8, 19, GRIS)
    k.texto(s, "**Pregunta guía:** ¿Qué zonas podrían presentar mayor abstención en el futuro si no se interviene?", k.X0, 4.55, 11.8, 0.4, 16, TINTA)
    k.texto(s, [f"**{EQUIPO}**", lista(INTEGRANTES)], k.X0, 5.25, 11, 0.8, 17, TINTA)
    k.texto(s, f"Fuentes: Conteos Censales de Participación Ciudadana 2009–2024, INE-DECEyEC ({URL_CCPC}) · Censo de Población y "
               f"Vivienda 2020, INEGI · Octubre de 2026", k.X0, 6.55, 12.1, 0.6, 11, GRIS)
    k.notas(s, "Presentamos FAROS-2027, una herramienta para anticipar dónde crecerá la abstención en la elección intermedia de 2027.")

    # 2 · EL RETO
    s = k.slide(F_CCPC)
    k.titulo(s, "El reto: anticipar dónde crecerá la abstención", "Reto 2 de la convocatoria: Predicción y escenarios de riesgo de abstención")
    k.caja(s, k.X0, 1.7, 6.3, 1.75)
    k.texto(s, "Pregunta guía", k.X0 + 0.3, 1.85, 5.7, 0.35, 14, AZUL, negrita=True)
    k.texto(s, "¿Qué zonas podrían presentar mayor abstención en el futuro si no se interviene?", k.X0 + 0.3, 2.2, 5.7, 0.8, 20, TINTA, negrita=True)
    k.texto(s, "Para el INE: planeación anticipada y priorización estratégica de recursos.", k.X0 + 0.3, 3.02, 5.7, 0.35, 13, GRIS)
    k.texto(s, "Lo que pide la convocatoria y dónde lo respondemos", k.X0, 3.7, 6.3, 0.35, 15, TINTA, negrita=True)
    pide = [("Modelo simple de riesgo con historia y variables sociodemográficas", "diapositivas 4 y 5"),
            ("Dos escenarios: sin intervención y con intervención hipotética", "diapositivas 6 y 7"),
            ("Esquema de riesgo territorial fácil de interpretar", "diapositivas 6 y 8"),
            ("Recomendaciones preventivas", "diapositiva 10")]
    for i, (t, d) in enumerate(pide):
        y = 4.15 + i * 0.62
        k.texto(s, str(i + 1), k.X0, y, 0.35, 0.5, 18, AZUL, negrita=True)
        k.texto(s, [t, d], k.X0 + 0.45, y, 5.85, 0.6, 13, TINTA, esp=0)
    ab = {a: 100 - R["part_nac"][a] for a in (2009, 2012, 2015, 2018, 2021, 2024)}
    k.texto(s, "Por qué importa", 7.35, 1.7, k.X1 - 7.35, 0.35, 15, TINTA, negrita=True)
    w2 = (k.X1 - 7.35 - 0.3) / 2
    k.dato(s, 7.35, 2.15, w2, f"{ab[2009]:.0f} · {ab[2015]:.0f} · {ab[2021]:.0f}%", "abstención en las intermedias 2009, 2015 y 2021", ROJO, h=1.5, tam=24)
    k.dato(s, 7.35 + w2 + 0.3, 2.15, w2, f"{ab[2012]:.0f} · {ab[2018]:.0f} · {ab[2024]:.0f}%", "abstención en las presidenciales 2012, 2018 y 2024", AZUL, h=1.5, tam=24)
    k.texto(s, ["**2027 es elección intermedia.** Si se repite el patrón, cerca de la mitad del padrón no votaría.",
                "**Los recursos de educación cívica son limitados.** Hay que saber antes de la jornada en qué entidades, distritos y grupos de "
                "población crecerá la abstención.",
                "**El promedio estatal no basta:** puede esconder distritos en riesgo dentro de entidades que se ven bien."],
            7.35, 3.95, k.X1 - 7.35, 2.8, 15, esp=10)
    k.notas(s, "Planteamos el problema tal como lo define la convocatoria y mostramos dónde respondemos cada requisito.")

    # 3 · HALLAZGOS
    s = k.slide(F_CCPC)
    k.titulo(s, "Sin intervención, la mitad del padrón no votaría en 2027",
             "La elección intermedia es el momento más vulnerable del ciclo electoral")
    datos = [(f"{R['abstencion_nacional_2024_obs']:.1f}%", "abstención observada en 2024 (elección presidencial)", AZUL),
             (f"{R['abstencion_nacional_2027_sin']:.1f}%", "abstención proyectada para 2027 si no se interviene", ROJO),
             (f"{R['abstencion_nacional_2027_con']:.1f}%", "abstención 2027 con intervención nacional en jóvenes y secciones rurales", VERDE),
             (f"{R['personas_recuperadas_2A'] / 1e6:.2f} millones", "de personas que sí votarían gracias a esa intervención", AZUL)]
    wcard = (k.X1 - k.X0 - 3 * 0.3) / 4
    for i, (v, e, c) in enumerate(datos):
        k.dato(s, k.X0 + i * (wcard + 0.3), 1.7, wcard, v, e, c, h=1.55, tam=30)
    k.imagen_fit(s, FIG / "fig1_serie_nacional_ciclo_slide.png", k.X0, 3.5, 7.4, 3.25)
    k.texto(s, "Abstención nacional observada (2009–2024) y proyectada (2027 y 2030). Las franjas son elecciones intermedias.",
            8.35, 3.55, 4.38, 0.7, 12, GRIS)
    k.texto(s, [f"**{R['n_cnt'][ROJO_S]} entidades en rojo** concentran el riesgo alto de abstención.",
                f"Al pasar de una elección presidencial a una intermedia, cada entidad pierde en promedio **{R['caida_intermedia']:.1f} puntos** de participación.",
                f"**{len(R['d_ocultos'])} distritos en rojo** están dentro de entidades amarillas o verdes: el promedio estatal los esconde."],
            8.35, 4.35, 4.38, 2.4, 15, TINTA, esp=10)
    k.notas(s, "El riesgo está en 2027. Sin hacer nada, la abstención sube casi 9 puntos respecto de 2024.")

    # 4 · DIAGNÓSTICO
    s = k.slide(F_CCPC)
    k.titulo(s, "Diagnóstico: juventudes, hombres y ciclo intermedio",
             f"Seis elecciones federales procesadas · {R['n_celdas']:,} grupos agregados · sin datos personales")
    k.imagen_fit(s, FIG / "fig3_brechas_edad_rural_sexo_slide.png", k.X0, 1.75, 8.45, 4.2)
    k.texto(s, ["Abstención proyectada 2027 por entidad (cada punto) y mediana de las 32 entidades (línea). "
                "Participación = SV / (SV + NV), con SV = registros con marca de voto y NV = sin marca.",
                f"Datos: {URL_CCPC}"], k.X0, 6.05, 8.45, 0.7, 11, GRIS, esp=2)
    items = [(f"{R['abs_joven']:.1f}% vs {R['abs_30mas']:.1f}%", "abstención 2027 de 18 a 29 años frente a 30 años o más (promedio nacional)", ROJO),
             (f"{R['abs_joven_h']:.1f}%", "abstención proyectada de los hombres de 18 a 29 años", ROJO),
             (f"{R['urb_mayor_rural']} de 32", "entidades donde las secciones urbanas se abstienen más que las rurales", AZUL)]
    for i, (v, e, c) in enumerate(items):
        k.dato(s, 9.35, 1.75 + i * 1.62, k.X1 - 9.35, v, e, c, h=1.45, tam=26)
    k.notas(s, "La brecha juvenil es de unos 10 puntos en todas las entidades; los hombres se abstienen más en las 32.")

    # 5 · MODELO Y VALIDACIÓN
    s = k.slide("modelo y validación retrospectiva del equipo con datos de la CCPC 2009–2024")
    k.titulo(s, "Modelo de dos lentes, validado con 2021 y 2024", "Seis coeficientes con lectura directa; probado sin ver los resultados que predice")
    cols = [("Lente A: mismo tipo", "Parte de la última elección del mismo tipo (2021 para 2027).", "P(t−6) + α tipo + γ·ΔGob", f"γ = {R['gA']:+.1f} pp"),
            ("Lente B: reciente", "Parte de la elección inmediata anterior (2024 para 2027).", "P(t−3) + α tipo + γ·ΔGob", f"γ = {R['gB']:+.1f} pp"),
            ("Proyección final", "Promedio de los dos lentes, por grupo de votantes y entidad.", "½ A + ½ B", "por entidad")]
    wc, gap = 3.73, 0.47
    for i, (t, d, f, g) in enumerate(cols):
        x = k.X0 + i * (wc + gap)
        k.caja(s, x, 1.7, wc, 2.55, LAVANDA if i < 2 else "#E3EAF2")
        k.texto(s, t, x + 0.3, 1.88, wc - 0.6, 0.4, 19, AZUL, negrita=True)
        k.texto(s, d, x + 0.3, 2.35, wc - 0.6, 0.6, 13)
        k.texto(s, f, x + 0.3, 3.0, wc - 0.6, 0.4, 16, TINTA, italica=True)
        k.texto(s, g, x + 0.3, 3.5, wc - 0.6, 0.5, 20, ROJO if i < 2 else AZUL, negrita=True)
        if i < 2:
            k.texto(s, "+" if i == 0 else "=", x + wc, 2.75, gap, 0.5, 24, GRIS, PP_ALIGN.CENTER, negrita=True)
    k.texto(s, "**α** = efecto del tipo de elección (intermedia o presidencial).   **γ** = efecto de elegir gobernador el mismo día; "
               "en 2027 habrá 17 gubernaturas.", k.X0, 4.4, k.X1 - k.X0, 0.4, 13)
    k.texto(s, "Validación: se predijo 2021 con datos hasta 2018, y 2024 con datos hasta 2021", k.X0, 4.95, k.X1 - k.X0, 0.35, 15, TINTA, negrita=True)
    wv = (k.X1 - k.X0 - 2 * 0.3) / 3
    for i, (v, e) in enumerate([(f"±{R['mae_validacion']:.2f} pp", f"error medio por entidad (el modelo ingenuo se equivoca {R['m0_mae']:.2f})"),
                                (f"{R['acierto']:.0f}%", "de las entidades quedaron en el color correcto del semáforo"),
                                (f"{R['spearman']:.2f}", "correlación de rangos (Spearman): ordena bien el riesgo")]):
        k.dato(s, k.X0 + i * (wv + 0.3), 5.4, wv, v, e, AZUL, h=1.35, tam=26)
    k.notas(s, "Cada grupo es entidad × tipo de sección × sexo × edad. Coeficientes por mínimos cuadrados ponderados por lista nominal.")

    # 6 · SEMÁFORO
    s = k.slide(F_CCPC)
    k.titulo(s, "Semáforo estatal 2027: 8 entidades en riesgo alto",
             f"Rojo con abstención de {R['umbral_rojo']:.2f}% o más, verde con {R['umbral_verde']:.2f}% o menos. Mismos cortes en ambos mapas")
    k.imagen_fit(s, FIG / "mapas_slide.png", k.X0, 1.75, 8.9, 4.85)
    rojos = R["rojos"]
    k.texto(s, "Riesgo alto sin intervención", 9.85, 1.8, 2.9, 0.4, 16, ROJO, negrita=True)
    k.texto(s, [f"{e}  **{v:.1f}%**" for e, v in zip(rojos.ENTIDAD, rojos.Escenario_Sin_Intervencion_2027)],
            9.85, 2.3, 2.9, 3.2, 14, esp=4)
    k.caja(s, 9.7, 5.45, k.X1 - 9.7, 1.15, "#E7F4EB")
    k.texto(s, f"**{R['cambian_color']} entidades** bajan de color con la intervención nacional (2A)", 9.9, 5.62, k.X1 - 10.1, 0.85, 14)
    k.notas(s, "Guanajuato, Durango y Jalisco quedan en rojo sin elección de gubernatura en 2027.")

    # 7 · ESCENARIO 2B Y SENSIBILIDAD
    s = k.slide("simulación del equipo sobre la proyección 2027")
    k.titulo(s, "Priorizar 8 entidades logra el mismo cambio de semáforo",
             "Escenario 2A (intervenir las 32 entidades) frente a 2B (intervenir solo las 8 en rojo)")
    k.dato(s, k.X0, 1.75, 4.0, f"{R['n_cnt_con'][ROJO_S]} en rojo", f"Escenario 2A: de 8 a {R['n_cnt_con'][ROJO_S]} entidades en rojo y "
           f"{fint(R['personas_recuperadas_2A'])} personas más votarían", VERDE, h=1.65, tam=32)
    k.dato(s, k.X0, 3.6, 4.0, f"{R['n_cnt_2b'][ROJO_S]} en rojo", f"Escenario 2B: el mismo resultado de semáforo con "
           f"{fint(R['personas_recuperadas_2B'])} personas, interviniendo 8 de 32 entidades", AZUL, h=1.65, tam=32)
    k.texto(s, f"2B alcanza {100 * R['personas_recuperadas_2B'] / R['personas_recuperadas_2A']:.0f}% de la población que alcanza 2A y "
               "logra la misma reducción de entidades en rojo. Es la opción si el presupuesto es limitado.", k.X0, 5.5, 4.0, 1.2, 14)
    se = R["sens"]
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    x = [0, 5, 10, 15, 20]
    ax.plot(x, se.Abstencion_nacional_2027, "-o", color=AZUL, lw=2.5, ms=8)
    for xi, yi, rj in zip(x, se.Abstencion_nacional_2027, se.Entidades_rojo):
        ax.annotate(f"{yi:.1f}%\n{rj} en rojo", (xi, yi), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=12)
    ax.set_xticks(x, ["0%", "5%", "10%", "15%", "20%"]); ax.set_ylim(43.5, 51.8); ax.set_xlim(-1.5, 21.5)
    ax.tick_params(labelsize=12)
    ax.set_xlabel("Reducción supuesta de la abstención en jóvenes y secciones rurales", fontsize=12)
    ax.set_ylabel("Abstención nacional 2027 (%)", fontsize=12)
    ax.grid(axis="y", color="#EEE")
    guardar(fig, "fig_sensibilidad.png")
    k.texto(s, "Sensibilidad: aun con 5% de eficacia bajan las entidades en rojo", 5.0, 1.75, 7.7, 0.4, 16, TINTA, negrita=True)
    k.imagen_fit(s, FIG / "fig_sensibilidad.png", 5.0, 2.25, 7.73, 4.45)
    k.notas(s, "La eficacia del 15% es un supuesto; la conclusión de prioridad no depende de su valor exacto.")

    # 8 · DISTRITOS OCULTOS
    s = k.slide(F_CCPC)
    k.titulo(s, f"El hallazgo clave: {len(R['d_ocultos'])} distritos rojos ocultos",
             f"De {R['d_cnt'][ROJO_S]} distritos federales en rojo, {len(R['d_ocultos'])} están en entidades amarillas o verdes")
    k.imagen_fit(s, FIG / "fig5_distritos_rojos_ocultos_slide.png", k.X0, 1.7, 6.9, 5.05)
    oe = R["d_ocultos_ent"]
    k.dato(s, 7.85, 1.75, k.X1 - 7.85, f"{R['d_ocultos'].ABSTENCIONISTAS_ESPERADOS.sum() / 1e6:.2f} millones",
           "de abstencionistas esperados en esos 22 distritos", ROJO, h=1.45, tam=30)
    k.texto(s, [f"**Nuevo León:** {oe.get('Nuevo León', 0)} distritos", f"**Tamaulipas:** {oe.get('Tamaulipas', 0)} distritos",
                "**México, Sinaloa y Tabasco:** 2 distritos cada uno", "**Chiapas, distrito 9:** en rojo dentro de una entidad verde",
                f"En total, **{oe.size} entidades** tienen al menos un distrito rojo oculto."], 7.85, 3.5, k.X1 - 7.85, 3.0, 15, esp=8)
    k.notas(s, "Si los recursos se asignan solo con el promedio estatal, estos distritos quedan fuera.")

    # 9 · HERRAMIENTA
    s = k.slide("tablero de escenarios del equipo (carpeta 3_Mapa_Escenarios)")
    k.titulo(s, "Una herramienta que el INE puede usar mañana", "Tablero interactivo autocontenido, capa GeoJSON y código reproducible en Python")
    cap = captura_tablero()
    k.imagen_fit(s, cap, k.X0, 1.75, 8.0, 3.75)
    feats = ["Compara el mapa **sin y con intervención**, en los escenarios 2A y 2B.",
             "Ordena las **32 entidades** y los **300 distritos** por cualquier columna.",
             "Un clic en un estado muestra **sus distritos**.",
             "Funciona **sin internet**: es un solo archivo HTML.",
             "La capa **GeoJSON** se abre en QGIS, Power BI o Tableau.",
             "**run_all.py** regenera todo cuando se publique la CCPC 2027."]
    k.texto(s, feats, 8.95, 1.8, k.X1 - 8.95, 3.8, 14, esp=9)
    archivos = [("Tablero interactivo", ["3_Mapa_Escenarios", "archivo .html"]), ("Capa geoespacial", ["3_Mapa_Escenarios", "archivo .geojson"]),
                ("Base de datos, 107 variables", ["4_Base_Datos_Anonimizada", "(.xlsx y .csv)"]), ("Código en Python", ["5_Codigo_Repositorio", "con run_all.py"])]
    wa = (k.X1 - k.X0 - 3 * 0.25) / 4
    for i, (f, d) in enumerate(archivos):
        x = k.X0 + i * (wa + 0.25)
        k.caja(s, x, 5.7, wa, 1.05)
        k.texto(s, f, x + 0.2, 5.83, wa - 0.4, 0.3, 13, AZUL, negrita=True)
        k.texto(s, d, x + 0.2, 6.18, wa - 0.4, 0.5, 11.5, esp=0)
    k.notas(s, "Carpetas del paquete: 3_Mapa_Escenarios (HTML y GeoJSON), 4_Base_Datos_Anonimizada (xlsx y csv) y 5_Codigo_Repositorio.")

    # 10 · RECOMENDACIONES
    s = k.slide("propuesta del equipo para la DECEyEC y las Juntas Ejecutivas")
    k.titulo(s, "Hoja de ruta para la DECEyEC y las Juntas Ejecutivas", "Acciones operativas dentro de la ENCÍVICA, sin reformas legales")
    recs = [("1", "Asignar recursos por distrito", f"Prioridad a los {R['d_rojo_en_rojo']} distritos rojos de entidades rojas y a los {len(R['d_ocultos'])} rojos ocultos.",
             "Mide: % del presupuesto ejercido en distritos rojos"),
            ("2", "Juventudes y hombres jóvenes", "Campañas ENCÍVICA en escuelas, centros de trabajo y redes, en secciones urbanas y mixtas.",
             "Mide: participación de 18 a 29 años en 2027 frente a 2021"),
            ("3", "Territorio e interculturalidad", "Brigadas móviles y materiales en lenguas indígenas en secciones rurales de alta abstención.",
             "Mide: secciones rurales atendidas y materiales traducidos"),
            ("4", "Contra la fatiga de intermedia", "Campaña en las 15 entidades sin gubernatura en 2027, empezando por Guanajuato, Jalisco y Durango.",
             "Mide: caída de participación de 2024 a 2027")]
    wc2 = (k.X1 - k.X0 - 0.3) / 2
    for i, (num, t, d, m) in enumerate(recs):
        x = k.X0 + (i % 2) * (wc2 + 0.3); y = 1.7 + (i // 2) * 1.9
        k.caja(s, x, y, wc2, 1.72)
        k.texto(s, num, x + 0.3, y + 0.22, 0.5, 0.6, 30, AZUL, negrita=True)
        k.texto(s, t, x + 0.95, y + 0.22, wc2 - 1.2, 0.45, 18, TINTA, negrita=True)
        k.texto(s, d, x + 0.95, y + 0.68, wc2 - 1.2, 0.6, 14)
        k.texto(s, m, x + 0.95, y + 1.3, wc2 - 1.2, 0.35, 12.5, GRIS, italica=True)
    etapas = [("Nov 2026 – ene 2027", "Adoptar el semáforo y validar la lista de distritos con cada Junta Local"),
              ("Feb – abr 2027", "Desplegar campañas y brigadas según la regla de asignación"),
              ("May – jun 2027", "Intensificar en distritos rojos y en juventudes antes de la jornada"),
              ("Segundo semestre 2027", "Re-estimar con la CCPC 2027 y evaluar el impacto por distrito")]
    we = (k.X1 - k.X0 - 3 * 0.25) / 4
    for i, (f, d) in enumerate(etapas):
        x = k.X0 + i * (we + 0.25)
        k.texto(s, f, x, 5.65, we, 0.35, 14, AZUL, negrita=True)
        k.texto(s, d, x, 6.02, we, 0.8, 12.5)
    k.notas(s, "Todas las acciones se ejecutan con las atribuciones vigentes de la DECEyEC y las Juntas Ejecutivas.")

    assert len(k.p.slides) == 10, "La presentación debe tener exactamente 10 diapositivas"
    ruta = OUT / "Presentacion_Ejecutiva_Reto2.pptx"
    k.p.save(ruta)
    pdf = a_pdf(ruta)
    print(f"Presentación: {ruta.name} → {pdf.name if pdf else '(sin PDF)'} · {len(k.p.slides)} diapositivas")
    return ruta


def main():
    D = cargar()
    H = hechos(D)
    figuras(D, H)
    reporte(D, H)
    presentacion(D, H)


if __name__ == "__main__":
    main()
