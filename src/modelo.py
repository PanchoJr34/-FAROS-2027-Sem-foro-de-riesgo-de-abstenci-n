"""
modelo.py — Modelo transparente de proyección de participación / abstención.

Idea central ("dos lentes" de memoria electoral)
-------------------------------------------------
Para cada celda c = entidad × tipo de sección × sexo × grupo de edad y elección objetivo t:

  Lente A — memoria del MISMO TIPO de elección (rezago 6 años: intermedia vs. intermedia):
      P̂ᴬ(c,t) = P(c,t-6) + αᴬ[tipo(t)] + γᴬ · ΔGob(e, t, t-6)

  Lente B — memoria RECIENTE (rezago 3 años: la elección inmediata anterior):
      P̂ᴮ(c,t) = P(c,t-3) + αᴮ[tipo(t)] + γᴮ · ΔGob(e, t, t-3)

  Proyección final:  P̂(c,t) = w · P̂ᴬ + (1-w) · P̂ᴮ          (w = 0.5, elegido por validación)
  Abstención:        Â(c,t) = 100 - P̂(c,t)

donde
  α[tipo]  = desplazamiento nacional típico al pasar a una elección intermedia o presidencial
             (captura el "efecto ciclo": la participación cae en intermedias),
  ΔGob     = cambio en la concurrencia de elección de GUBERNATURA en la entidad (+1, 0, -1),
  γ        = puntos de participación que aporta tener gubernatura concurrente.

Los parámetros (α, γ) se estiman por Mínimos Cuadrados Ordinarios ponderados por la lista nominal
con TODAS las transiciones históricas disponibles antes de la elección objetivo. Son 3 coeficientes
por lente: el modelo se explica en una línea y cada coeficiente tiene lectura sustantiva.

Las celdas se agregan a entidad ponderando por lista nominal, por lo que la composición por edad,
sexo y tipo de sección ("peso de la abstención juvenil/rural") entra de forma explícita.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import GOBERNATURA, INTERMEDIAS, LIMITES_PARTICIPACION, PESO_LENTE_MISMO_TIPO

CLAVE = ["EDOCVE", "TIPOSEC", "SEXO", "GRUPO_EDAD"]


def matrices(celdas: pd.DataFrame):
    """Convierte el panel largo a matrices celda × año de participación (%) y lista nominal."""
    c = celdas[celdas.SEXO.isin([0, 1])].copy()        # 'no binario' (105 registros en 2024) solo en totales
    c["P"] = 100 * c.SV / (c.SV + c.NV)
    P = c.pivot_table(index=CLAVE, columns="AELEC", values="P")
    L = c.pivot_table(index=CLAVE, columns="AELEC", values="LN")
    return P, L


def gob(idx: pd.MultiIndex, anio: int) -> np.ndarray:
    ent = idx.get_level_values("EDOCVE")
    return np.isin(ent, GOBERNATURA[anio]).astype(float)


def _diseno(idx, t, rezago):
    inter = float(t in INTERMEDIAS)
    n = len(idx)
    return np.column_stack([np.full(n, inter), np.full(n, 1 - inter), gob(idx, t) - gob(idx, t - rezago)])


def ajustar_lente(P, L, objetivo: int, rezago: int):
    """Estima (α_intermedia, α_presidencial, γ_gob) con transiciones observadas antes de `objetivo`."""
    anios_obs = [a for a in P.columns if a < objetivo and (a - rezago) in P.columns]
    X, y, w = [], [], []
    for t in anios_obs:
        yt = (P[t] - P[t - rezago]).to_numpy()
        m = ~np.isnan(yt)
        X.append(_diseno(P.index, t, rezago)[m]); y.append(yt[m]); w.append(np.sqrt(L[t].to_numpy()[m]))
    X, y, w = np.vstack(X), np.concatenate(y), np.concatenate(w)
    beta, *_ = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)
    return pd.Series(beta, index=["alfa_intermedia", "alfa_presidencial", "gamma_gubernatura"]), anios_obs


def proyectar(P, L, objetivo: int, peso=PESO_LENTE_MISMO_TIPO):
    """Proyecta la participación por celda para `objetivo`. P puede incluir años ya proyectados."""
    out, coefs = {}, {}
    for nombre, rezago in (("A_mismo_tipo", 6), ("B_reciente", 3)):
        b, usados = ajustar_lente(P, L, objetivo, rezago)
        out[nombre] = P[objetivo - rezago].to_numpy() + _diseno(P.index, objetivo, rezago) @ b.to_numpy()
        coefs[nombre] = b.round(3).to_dict() | {"transiciones": usados}
    p = peso * out["A_mismo_tipo"] + (1 - peso) * out["B_reciente"]
    p = np.clip(p, *LIMITES_PARTICIPACION)
    return pd.Series(p, index=P.index), coefs


def agregar(part: pd.Series, ln: pd.Series, por="EDOCVE"):
    """Participación agregada (%) ponderada por lista nominal."""
    df = pd.DataFrame({"p": part * ln, "w": ln})
    g = df.groupby(level=por).sum()
    return g.p / g.w


def semaforo(abst: pd.Series, q_rojo=None, q_verde=None):
    """Clasifica por cuartiles; si se pasan umbrales, los usa fijos (para comparar escenarios)."""
    q_rojo = abst.quantile(0.75) if q_rojo is None else q_rojo
    q_verde = abst.quantile(0.25) if q_verde is None else q_verde
    s = np.where(abst >= q_rojo, "Riesgo Alto (Rojo)",
                 np.where(abst <= q_verde, "Riesgo Bajo (Verde)", "Riesgo Medio (Amarillo)"))
    return pd.Series(s, index=abst.index), q_rojo, q_verde
