"""
03_validacion_modelo.py — Validación retrospectiva ("backtesting") del modelo.

Pregunta: si en 2018 hubiéramos usado este método para anticipar 2021, y en 2021 para anticipar
2024, ¿qué tan cerca habríamos estado? Cada prueba usa SOLO información anterior a la elección
objetivo (sin "ver el futuro").

Compara 6 especificaciones, de la más ingenua a la elegida:
  M0  Ingenuo mismo tipo      : P(t) = P(t-6)
  M1  Ingenuo reciente        : P(t) = P(t-3)
  M2  Lente A sin gubernatura : P(t-6) + α_tipo
  M3  Lente A                 : P(t-6) + α_tipo + γ·ΔGob
  M4  Lente B                 : P(t-3) + α_tipo + γ·ΔGob
  M5  Modelo final (A+B)/2    : promedio de M3 y M4   <-- elegido

Métricas a nivel ENTIDAD (lo que usa el semáforo):
  MAE (pp)            error absoluto medio de la abstención
  Acierto semáforo    % de entidades con el mismo color (cuartiles) que el observado
  Rojos detectados    entidades rojas observadas que el modelo también marcó en rojo
  Spearman            correlación de rangos (¿ordena bien el riesgo?)

Salidas: outputs/validacion_backtest.csv, outputs/coeficientes_modelo.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import OUT, RAW  # noqa: E402
from modelo import _diseno, agregar, ajustar_lente, matrices, proyectar, semaforo  # noqa: E402


def lente(P, L, t, rezago, con_gob=True):
    b, _ = ajustar_lente(P, L, t, rezago)
    X = _diseno(P.index, t, rezago)
    if not con_gob:
        X = X.copy(); X[:, 2] = 0
        # re-estimación sin la variable de gubernatura
        anios = [a for a in P.columns if a < t and (a - rezago) in P.columns]
        Xs, ys, ws = [], [], []
        for a in anios:
            y = (P[a] - P[a - rezago]).to_numpy(); m = ~np.isnan(y)
            Xs.append(_diseno(P.index, a, rezago)[m][:, :2]); ys.append(y[m]); ws.append(np.sqrt(L[a].to_numpy()[m]))
        Xs, ys, ws = np.vstack(Xs), np.concatenate(ys), np.concatenate(ws)
        b2, *_ = np.linalg.lstsq(Xs * ws[:, None], ys * ws, rcond=None)
        return P[t - rezago].to_numpy() + X[:, :2] @ b2
    return P[t - rezago].to_numpy() + X @ b.to_numpy()


def metricas(pred, P, L, t):
    ln = L[t]
    a_hat = 100 - agregar(pd.Series(pred, index=P.index).fillna(P[t]), ln)
    a_obs = 100 - agregar(P[t], ln)
    s_hat, _, _ = semaforo(a_hat)
    s_obs, _, _ = semaforo(a_obs)
    rojo = "Riesgo Alto (Rojo)"
    return {
        "MAE_pp": round(float(np.mean(np.abs(a_hat - a_obs))), 2),
        "Acierto_semaforo_%": round(100 * float((s_hat == s_obs).mean()), 1),
        "Rojos_detectados": f"{int(((s_hat == rojo) & (s_obs == rojo)).sum())}/{int((s_obs == rojo).sum())}",
        "Spearman": round(float(a_hat.corr(a_obs, method="spearman")), 2),
    }


def main():
    c = pd.read_csv(RAW / "ccpc_agregado_entidad.csv", encoding="utf-8-sig")
    P, L = matrices(c)
    filas = []
    for t in (2021, 2024):
        modelos = {
            "M0 Ingenuo mismo tipo (t-6)": P[t - 6].to_numpy(),
            "M1 Ingenuo reciente (t-3)": P[t - 3].to_numpy(),
            "M2 Lente A sin gubernatura": lente(P, L, t, 6, con_gob=False),
            "M3 Lente A (mismo tipo + gubernatura)": lente(P, L, t, 6),
            "M4 Lente B (reciente + gubernatura)": lente(P, L, t, 3),
            "M5 MODELO FINAL (A+B)/2": proyectar(P[[a for a in P.columns if a < t]].join(P[[t]]), L, t)[0].to_numpy(),
        }
        for nombre, pred in modelos.items():
            filas.append({"Eleccion_objetivo": t, "Modelo": nombre} | metricas(pred, P, L, t))
    v = pd.DataFrame(filas)
    prom = v.groupby("Modelo", sort=False)[["MAE_pp", "Acierto_semaforo_%", "Spearman"]].mean().round(2)
    print(v.to_string(index=False))
    print("\nPromedio 2021-2024:\n", prom.to_string())
    v.to_csv(OUT / "validacion_backtest.csv", index=False, encoding="utf-8-sig")

    # Coeficientes del modelo que se usa para proyectar 2027 (toda la historia 2009-2024)
    _, coefs = proyectar(P, L, 2027)
    filas = []
    for lente_n, d in coefs.items():
        for k, val in d.items():
            if k != "transiciones":
                filas.append({"Lente": lente_n, "Coeficiente": k, "Valor_pp": val,
                              "Transiciones_usadas": " ".join(f"{a - (6 if 'A' in lente_n else 3)}→{a}" for a in d["transiciones"])})
    cf = pd.DataFrame(filas)
    cf.to_csv(OUT / "coeficientes_modelo.csv", index=False, encoding="utf-8-sig")
    print("\nCoeficientes para proyectar 2027:\n", cf.to_string(index=False))


if __name__ == "__main__":
    main()
