from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

from analisis_financiero import (
    ALGORITHM_DOCS,
    comparar_activos,
    estadisticas_riesgo,
    extraer_simbolos,
    matriz_correlacion,
    media_movil_simple,
    serie_ohlcv,
)


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"


def _parse_date_axis(fechas):
    return [mdates.datestr2num(fecha) for fecha in fechas]


def _pagina_texto(pdf, titulo, lineas):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.08, 0.94, titulo, fontsize=18, weight="bold")
    y = 0.89
    for linea in lineas:
        fig.text(0.08, y, linea, fontsize=10, wrap=True)
        y -= 0.03
        if y < 0.08:
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            fig = plt.figure(figsize=(8.27, 11.69))
            y = 0.94
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def generar_reporte_pdf(dataset, simbolo_a, simbolo_b, ruta_salida=None):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if ruta_salida is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida = REPORTS_DIR / f"reporte_financiero_{stamp}.pdf"
    else:
        ruta_salida = Path(ruta_salida)

    simbolos = extraer_simbolos(dataset)
    comparacion = comparar_activos(dataset, simbolo_a, simbolo_b)
    riesgos = estadisticas_riesgo(dataset)
    correlacion = matriz_correlacion(dataset)

    with PdfPages(ruta_salida) as pdf:
        _pagina_texto(
            pdf,
            "Reporte tecnico de analisis financiero",
            [
                f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Activos en dataset: {len(simbolos)}",
                f"Comparacion principal: {simbolo_a} vs {simbolo_b}",
                "Fuente: Yahoo Finance consultado mediante peticiones HTTP directas.",
                "Restricciones: no se usa yfinance, pandas_datareader, numpy, scipy ni pandas.",
                "Limpieza: duplicados eliminados, OHLC inconsistente descartado y precios faltantes alineados con forward fill trazable mediante *_Missing.",
                "Impacto: el forward fill conserva calendario comun, pero puede suavizar retornos en dias sin negociacion; por eso se reporta como imputacion.",
            ],
        )

        m = comparacion["metrics"]
        metric_lines = [
            f"Observaciones de precios alineados: {comparacion['observations_prices']}",
            f"Observaciones de retornos alineados: {comparacion['observations_returns']}",
            "",
            "--- Distancia Euclidiana ---",
            f"  Precios crudos:       {m['euclidean_prices']:.4f}",
            f"  Precios Z-norm:       {m['euclidean_prices_norm']:.4f}  (escala comparable)",
            f"  Retornos diarios:     {m['euclidean_returns']:.6f}",
            "",
            "--- Correlacion de Pearson ---",
            f"  Retornos:             {m['pearson_returns']:.6f}",
            "",
            "--- Dynamic Time Warping ---",
            f"  DTW completo O(n*m):  {m['dtw_returns']:.4f}",
            f"  DTW Sakoe-Chiba w={m['dtw_band_width']}: {m['dtw_returns_band']:.4f}  (O(n*w))",
            "",
            "--- Similitud Coseno ---",
            f"  Retornos:             {m['cosine_returns']:.6f}",
            "",
            "--- Complejidad por algoritmo ---",
        ]
        for nombre, doc in ALGORITHM_DOCS.items():
            metric_lines.append(f"  {nombre}: tiempo {doc['time']} | espacio {doc['space']}")
            metric_lines.append(f"    formula: {doc['formula']}")
            metric_lines.append(f"    pseudoc: {doc['pseudocode']}")
        _pagina_texto(pdf, "Metricas de similitud y complejidad", metric_lines)

        top_riesgo = ["Activo            | Volatilidad | Ret. anual | Sharpe | Categoria"]
        top_riesgo.append("-" * 65)
        for item in riesgos[:20]:
            top_riesgo.append(
                f"{item['symbol']:<18}| {item['annual_volatility']*100:>8.2f}%  "
                f"| {item['annual_return']*100:>8.2f}%  "
                f"| {item['sharpe_ratio']:>6.2f} "
                f"| {item['risk_category']}"
            )
        _pagina_texto(pdf, "Ranking de riesgo por volatilidad (Sharpe sin tasa libre de riesgo)", top_riesgo)

        fig, ax = plt.subplots(figsize=(11, 6))
        fechas = comparacion["prices"]["dates"][-500:]
        x = _parse_date_axis(fechas)
        ax.plot(x, comparacion["prices"][simbolo_a][-500:], label=simbolo_a)
        ax.plot(x, comparacion["prices"][simbolo_b][-500:], label=simbolo_b)
        ax.set_title("Precios de cierre")
        ax.grid(True, alpha=0.25)
        ax.legend()
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        fig.autofmt_xdate()
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

        # Candlestick chart with SMAs for symbol_a
        candle_serie = serie_ohlcv(dataset, simbolo_a)[-180:]
        if candle_serie:
            fechas_c = [mdates.datestr2num(item["fecha"]) for item in candle_serie]
            cierres_c = [item["close"] for item in candle_serie]
            sma20 = media_movil_simple(cierres_c, 20)
            sma50 = media_movil_simple(cierres_c, 50)
            fig_c, ax_c = plt.subplots(figsize=(11, 5))
            width = 0.65
            for x, item in zip(fechas_c, candle_serie):
                color = "#147a50" if item["close"] >= item["open"] else "#b42318"
                ax_c.vlines(x, item["low"], item["high"], color=color, linewidth=0.9)
                lower = min(item["open"], item["close"])
                height = abs(item["close"] - item["open"]) or 0.0001
                ax_c.add_patch(Rectangle((x - width / 2, lower), width, height, facecolor=color, edgecolor=color, alpha=0.85))
            ax_c.plot(fechas_c, [v if v is not None else float("nan") for v in sma20], color="#1d4ed8", linewidth=1.2, label="SMA 20")
            ax_c.plot(fechas_c, [v if v is not None else float("nan") for v in sma50], color="#d97706", linewidth=1.2, label="SMA 50")
            ax_c.set_title(f"Velas con medias moviles - {simbolo_a} (ultimos 180 dias)")
            ax_c.set_ylabel("Precio")
            ax_c.grid(True, alpha=0.22)
            ax_c.legend(loc="upper left")
            ax_c.xaxis_date()
            ax_c.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            fig_c.autofmt_xdate()
            pdf.savefig(fig_c, bbox_inches="tight")
            plt.close(fig_c)

        symbols = correlacion["symbols"]
        matrix = correlacion["matrix"]
        fig, ax = plt.subplots(figsize=(9, 9))
        im = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(symbols)))
        ax.set_yticks(range(len(symbols)))
        ax.set_xticklabels(symbols, rotation=75, ha="right", fontsize=6)
        ax.set_yticklabels(symbols, fontsize=6)
        ax.set_title("Mapa de calor de correlacion")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    return ruta_salida
