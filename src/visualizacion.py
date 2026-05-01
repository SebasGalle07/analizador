import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from src.analisis_financiero import (
    matriz_correlacion,
    media_movil_simple,
    serie_ohlcv,
)


def _fig_to_png_bytes(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def _parse_date_axis(fechas):
    return [mdates.datestr2num(fecha) for fecha in fechas]


def generar_heatmap_correlacion(dataset):
    data = matriz_correlacion(dataset)
    simbolos = data["symbols"]
    matriz = data["matrix"]

    size = max(7, min(16, len(simbolos) * 0.55))
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(matriz, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(simbolos)))
    ax.set_yticks(range(len(simbolos)))
    ax.set_xticklabels(simbolos, rotation=75, ha="right", fontsize=7)
    ax.set_yticklabels(simbolos, fontsize=7)
    ax.set_title("Matriz de correlacion de retornos", fontsize=12, pad=12)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    if len(simbolos) <= 24:
        for i in range(len(simbolos)):
            for j in range(len(simbolos)):
                ax.text(j, i, f"{matriz[i][j]:.2f}", ha="center", va="center", fontsize=5)

    return _fig_to_png_bytes(fig)


def generar_grafico_velas(dataset, simbolo, ventana_corta=20, ventana_larga=50, limite=180):
    serie = serie_ohlcv(dataset, simbolo)[-limite:]
    if not serie:
        raise ValueError(f"No hay datos para {simbolo}")

    fechas = [mdates.datestr2num(item["fecha"]) for item in serie]
    cierres = [item["close"] for item in serie]
    sma_corta = media_movil_simple(cierres, max(1, int(ventana_corta)))
    sma_larga = media_movil_simple(cierres, max(1, int(ventana_larga)))

    fig, ax = plt.subplots(figsize=(12, 5.8))
    width = 0.65
    for x, item in zip(fechas, serie):
        color = "#147a50" if item["close"] >= item["open"] else "#b42318"
        ax.vlines(x, item["low"], item["high"], color=color, linewidth=1.1)
        lower = min(item["open"], item["close"])
        height = abs(item["close"] - item["open"]) or 0.0001
        ax.add_patch(Rectangle((x - width / 2, lower), width, height, facecolor=color, edgecolor=color, alpha=0.85))

    ax.plot(fechas, [v if v is not None else float("nan") for v in sma_corta], color="#1d4ed8", linewidth=1.3, label=f"SMA {ventana_corta}")
    ax.plot(fechas, [v if v is not None else float("nan") for v in sma_larga], color="#d97706", linewidth=1.3, label=f"SMA {ventana_larga}")
    ax.set_title(f"Velas y medias moviles - {simbolo}", fontsize=12)
    ax.set_ylabel("Precio")
    ax.grid(True, alpha=0.22)
    ax.legend(loc="upper left")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    return _fig_to_png_bytes(fig)


def generar_grafico_series(comparacion, max_points=500):
    fechas = comparacion["prices"]["dates"]
    simbolo_a, simbolo_b = comparacion["symbols"]
    valores_a = comparacion["prices"][simbolo_a]
    valores_b = comparacion["prices"][simbolo_b]

    if len(fechas) > max_points:
        fechas = fechas[-max_points:]
        valores_a = valores_a[-max_points:]
        valores_b = valores_b[-max_points:]

    x = _parse_date_axis(fechas)
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.plot(x, valores_a, label=simbolo_a, linewidth=1.3)
    ax.plot(x, valores_b, label=simbolo_b, linewidth=1.3)
    ax.set_title("Comparacion de precios de cierre")
    ax.set_ylabel("Precio")
    ax.grid(True, alpha=0.22)
    ax.legend(loc="upper left")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    fig.autofmt_xdate()
    return _fig_to_png_bytes(fig)


def generar_grafico_retornos(comparacion, max_points=500):
    fechas = comparacion["returns"]["dates"]
    simbolo_a, simbolo_b = comparacion["symbols"]
    ret_a = comparacion["returns"][simbolo_a]
    ret_b = comparacion["returns"][simbolo_b]

    if len(fechas) > max_points:
        fechas = fechas[-max_points:]
        ret_a = ret_a[-max_points:]
        ret_b = ret_b[-max_points:]

    x = _parse_date_axis(fechas)
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot(x, [r * 100 for r in ret_a], label=simbolo_a, linewidth=0.9, alpha=0.85)
    ax.plot(x, [r * 100 for r in ret_b], label=simbolo_b, linewidth=0.9, alpha=0.85)
    ax.axhline(0, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.set_title("Retornos diarios (%)")
    ax.set_ylabel("Retorno (%)")
    ax.grid(True, alpha=0.22)
    ax.legend(loc="upper left")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=60, labelsize=7)
    fig.autofmt_xdate()
    return _fig_to_png_bytes(fig)


def generar_barras_riesgo(riesgos):
    top = riesgos[:20]
    simbolos = [item["symbol"] for item in top]
    valores = [item["annual_volatility"] * 100 for item in top]
    colores = [
        "#b42318" if item["risk_category"] == "agresivo" else "#d97706" if item["risk_category"] == "moderado" else "#147a50"
        for item in top
    ]

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(simbolos, valores, color=colores)
    ax.set_title("Activos ordenados por volatilidad anualizada")
    ax.set_ylabel("Volatilidad anual (%)")
    ax.tick_params(axis="x", rotation=60, labelsize=8)
    ax.grid(True, axis="y", alpha=0.2)
    return _fig_to_png_bytes(fig)
