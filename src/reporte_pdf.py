from datetime import datetime
from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from src.analisis_financiero import (
    ALGORITHM_DOCS,
    comparar_activos,
    estadisticas_riesgo,
    extraer_simbolos,
    matriz_correlacion,
    media_movil_simple,
    serie_ohlcv,
)
from src.paths import REPORTS_DIR


PAGE_W = 8.27
PAGE_H = 11.69
LEFT = 0.08
RIGHT = 0.92
TOP = 0.95
ACCENT = "#1d4ed8"
ACCENT_2 = "#0f766e"
TEXT = "#0f172a"
MUTED = "#475569"
SOFT = "#e2e8f0"
SOFT_BG = "#f8fafc"


def _safe_token(value):
    token = []
    for ch in str(value):
        token.append(ch if ch.isalnum() else "_")
    cleaned = "".join(token).strip("_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.upper() or "X"


def _page_canvas(title, subtitle=None, page_no=None):
    fig = plt.figure(figsize=(PAGE_W, PAGE_H))
    fig.patch.set_facecolor("white")
    fig.text(LEFT, TOP, title, fontsize=18, weight="bold", color=TEXT)
    if subtitle:
        fig.text(LEFT, 0.92, subtitle, fontsize=10, color=MUTED)
    if page_no is not None:
        fig.text(RIGHT, TOP, f"{page_no:02d}", fontsize=11, color=MUTED, ha="right")
    fig.add_artist(
        Line2D([LEFT, RIGHT], [0.905, 0.905], transform=fig.transFigure, color=ACCENT, linewidth=2.2)
    )
    fig.add_artist(
        Line2D([LEFT, RIGHT], [0.055, 0.055], transform=fig.transFigure, color=SOFT, linewidth=1.0)
    )
    return fig


def _page_footer(fig, text):
    fig.text(LEFT, 0.03, text, fontsize=8, color=MUTED)


def _wrap_text(line, width=90):
    if not line:
        return [""]
    prefix = ""
    body = line
    if line.startswith("- "):
        prefix = "- "
        body = line[2:]
    wrapped = textwrap.wrap(body, width=width) or [""]
    if prefix:
        wrapped[0] = prefix + wrapped[0]
        for idx in range(1, len(wrapped)):
            wrapped[idx] = "  " + wrapped[idx]
    return wrapped


def _add_text_block(fig, lines, start_y=0.87, fontsize=10, line_gap=0.027, color=TEXT, width=94):
    y = start_y
    for line in lines:
        for wrapped in _wrap_text(line, width=width):
            fig.text(LEFT, y, wrapped, fontsize=fontsize, color=color)
            y -= line_gap
        if not line:
            y -= line_gap * 0.35
    return y


def _add_cards(fig, cards, left=LEFT, top=0.82, card_w=0.26, card_h=0.09, gap=0.03):
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    for idx, card in enumerate(cards):
        row = idx // 3
        col = idx % 3
        x = left + col * (card_w + gap)
        y = top - row * (card_h + 0.03)
        rect = Rectangle(
            (x, y - card_h),
            card_w,
            card_h,
            transform=fig.transFigure,
            facecolor=SOFT_BG,
            edgecolor=SOFT,
            linewidth=1.0,
            zorder=0,
        )
        fig.patches.append(rect)
        fig.text(x + 0.015, y - 0.028, card["label"], fontsize=8, color=MUTED, weight="bold")
        fig.text(x + 0.015, y - 0.055, card["value"], fontsize=13, color=TEXT, weight="bold")
        if card.get("detail"):
            fig.text(x + 0.015, y - 0.076, card["detail"], fontsize=7.5, color=card.get("color", ACCENT))


def _algorithm_cards(fig, docs, start_y=0.82):
    card_h = 0.100
    gap = 0.015
    left = LEFT
    right = RIGHT
    width = right - left
    y = start_y
    for name, doc in docs.items():
        display_names = {
            "euclidean": "Distancia euclidiana",
            "pearson": "Correlacion de Pearson",
            "dtw": "Dynamic Time Warping",
            "cosine": "Similitud coseno",
        }
        label = display_names.get(name, name.replace("_", " ").title())
        rect = Rectangle(
            (left, y - card_h),
            width,
            card_h,
            transform=fig.transFigure,
            facecolor=SOFT_BG,
            edgecolor=SOFT,
            linewidth=1.0,
            zorder=0,
        )
        fig.patches.append(rect)
        fig.text(left + 0.015, y - 0.028, label, fontsize=11.5, weight="bold", color=TEXT)
        fig.text(
            left + 0.015,
            y - 0.055,
            f"Tiempo {doc['time']} | Espacio {doc['space']}",
            fontsize=8.5,
            color=MUTED,
        )
        formula_box = Rectangle(
            (left + 0.015, y - 0.086),
            width - 0.03,
            0.028,
            transform=fig.transFigure,
            facecolor="#eff6ff",
            edgecolor="#bfdbfe",
            linewidth=0.8,
            zorder=0,
        )
        fig.patches.append(formula_box)
        fig.text(
            left + 0.022,
            y - 0.079,
            f"Formula: {doc['formula']}",
            fontsize=8.7,
            color=TEXT,
            family="monospace",
        )
        fig.text(left + 0.015, y - 0.105, doc["use"], fontsize=8.1, color=ACCENT_2)
        y -= card_h + gap


def _table_page(pdf, title, subtitle, headers, rows, page_no):
    fig = _page_canvas(title, subtitle, page_no)
    ax = fig.add_axes([0.06, 0.16, 0.88, 0.68])
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.3)
    table.scale(1.0, 1.35)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(SOFT)
        if row == 0:
            cell.set_facecolor("#dbeafe")
            cell.set_text_props(weight="bold", color=TEXT)
        else:
            cell.set_facecolor("white")
            cell.set_text_props(color=TEXT)
    _page_footer(fig, "Reporte financiero generado automaticamente desde la API Flask.")
    pdf.savefig(fig)
    plt.close(fig)


def _chart_page(pdf, title, subtitle, figures, page_no):
    fig = _page_canvas(title, subtitle, page_no)
    for axis, chart in figures:
        axis.set_facecolor("white")
        axis.grid(True, alpha=0.18)
        chart(axis)
    _page_footer(fig, "Las graficas se generan con matplotlib y se almacenan en reports/.")
    pdf.savefig(fig)
    plt.close(fig)


def _parse_date_axis(fechas):
    return [mdates.datestr2num(fecha) for fecha in fechas]


def _price_chart(ax, comparacion, simbolo_a, simbolo_b):
    fechas = comparacion["prices"]["dates"][-500:]
    x = _parse_date_axis(fechas)
    ax.plot(x, comparacion["prices"][simbolo_a][-500:], label=simbolo_a, color=ACCENT)
    ax.plot(x, comparacion["prices"][simbolo_b][-500:], label=simbolo_b, color=ACCENT_2)
    ax.set_title("Precios de cierre alineados", loc="left", fontsize=13, weight="bold", color=TEXT)
    ax.set_ylabel("Precio")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.legend(loc="upper left", frameon=False)


def _candle_chart(ax, dataset, simbolo_a):
    candle_serie = serie_ohlcv(dataset, simbolo_a)[-180:]
    if not candle_serie:
        ax.text(0.5, 0.5, "No hay datos suficientes para velas.", ha="center", va="center", color=MUTED)
        ax.axis("off")
        return
    fechas_c = [mdates.datestr2num(item["fecha"]) for item in candle_serie]
    cierres_c = [item["close"] for item in candle_serie]
    sma20 = media_movil_simple(cierres_c, 20)
    sma50 = media_movil_simple(cierres_c, 50)
    width = 0.65
    for x, item in zip(fechas_c, candle_serie):
        color = "#147a50" if item["close"] >= item["open"] else "#b42318"
        ax.vlines(x, item["low"], item["high"], color=color, linewidth=0.9)
        lower = min(item["open"], item["close"])
        height = abs(item["close"] - item["open"]) or 0.0001
        ax.add_patch(
            Rectangle(
                (x - width / 2, lower),
                width,
                height,
                facecolor=color,
                edgecolor=color,
                alpha=0.85,
            )
        )
    ax.plot(fechas_c, [v if v is not None else float("nan") for v in sma20], color=ACCENT, linewidth=1.2, label="SMA 20")
    ax.plot(fechas_c, [v if v is not None else float("nan") for v in sma50], color="#d97706", linewidth=1.2, label="SMA 50")
    ax.set_title(f"Velas con medias moviles - {simbolo_a}", loc="left", fontsize=13, weight="bold", color=TEXT)
    ax.set_ylabel("Precio")
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=45, labelsize=7)
    ax.legend(loc="upper left", frameon=False)


def _heatmap_chart(ax, correlacion):
    symbols = correlacion["symbols"]
    matrix = correlacion["matrix"]
    n = len(symbols)

    masked = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(float("nan") if j > i else matrix[i][j])
        masked.append(row)

    cmap = plt.cm.coolwarm.copy()
    cmap.set_bad(color="#f1f5f9")
    im = ax.imshow(masked, cmap=cmap, vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(symbols, rotation=70, ha="right", fontsize=6)
    ax.set_yticklabels(symbols, fontsize=6)
    ax.set_title("Mapa de calor de correlacion", loc="left", fontsize=13, weight="bold", color=TEXT)

    for k in range(n + 1):
        ax.axhline(k - 0.5, color="white", linewidth=0.5)
        ax.axvline(k - 0.5, color="white", linewidth=0.5)

    for i in range(n):
        for j in range(i + 1):
            val = matrix[i][j]
            if i != j and abs(val) >= 0.6:
                txt_color = "white" if abs(val) >= 0.75 else TEXT
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=5, color=txt_color)

    return im


def generar_reporte_pdf(dataset, simbolo_a, simbolo_b, ruta_salida=None):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if ruta_salida is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida = REPORTS_DIR / (
            f"reporte_financiero_{_safe_token(simbolo_a)}_{_safe_token(simbolo_b)}_{stamp}.pdf"
        )
    else:
        ruta_salida = Path(ruta_salida)

    simbolos = extraer_simbolos(dataset)
    comparacion = comparar_activos(dataset, simbolo_a, simbolo_b)
    riesgos = estadisticas_riesgo(dataset)
    correlacion = matriz_correlacion(dataset)

    m = comparacion["metrics"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with PdfPages(ruta_salida) as pdf:
        info = pdf.infodict()
        info["Title"] = "Reporte tecnico de analisis financiero"
        info["Author"] = "Codex"
        info["Subject"] = "Similitud, riesgo y visualizacion bursatil"
        info["Keywords"] = "Flask, PDF, analisis financiero, similitud, riesgo"

        cover = _page_canvas(
            "Reporte tecnico de analisis financiero",
            "Resumen formal de similitud, riesgo y correlacion sobre el dataset maestro.",
            1,
        )
        _add_cards(
            cover,
            [
                {"label": "Generado", "value": generated_at, "detail": "Fecha y hora de emision"},
                {"label": "Activos", "value": str(len(simbolos)), "detail": "Incluidos en el dataset"},
                {"label": "Comparacion", "value": f"{simbolo_a} vs {simbolo_b}", "detail": "Par principal del reporte"},
                {"label": "Observaciones", "value": str(comparacion["observations_prices"]), "detail": "Precios alineados"},
                {"label": "Retornos", "value": str(comparacion["observations_returns"]), "detail": "Base de similitud"},
                {"label": "Riesgo", "value": riesgos[0]["risk_category"] if riesgos else "-", "detail": "Mayor volatilidad relativa"},
            ],
            top=0.82,
        )
        cover_lines = [
            "Fuente de datos: Yahoo Finance mediante peticiones HTTP directas.",
            "Restricciones: no se usa yfinance, pandas_datareader, pandas, numpy ni scipy.",
            "El reporte resume el flujo ETL -> analisis -> visualizacion -> exportacion PDF.",
            "",
            "Contenido principal:",
            "- Metricas de similitud sobre precios y retornos.",
            "- Ranking de riesgo por volatilidad anualizada.",
            "- Grafico comparativo de precios y velas con medias moviles.",
            "- Mapa de calor de correlacion entre todos los activos.",
        ]
        _add_text_block(cover, cover_lines, start_y=0.58, fontsize=10, line_gap=0.03, color=TEXT, width=92)
        _page_footer(cover, "Documento reproducible generado automaticamente por la aplicacion.")
        pdf.savefig(cover)
        plt.close(cover)

        metric_lines = [
            f"Activos en dataset: {len(simbolos)}",
            f"Comparacion principal: {simbolo_a} vs {simbolo_b}",
            "",
            "Interpretacion rapida:",
            f"- Euclidiana precios: {m['euclidean_prices']:.4f}",
            f"- Euclidiana Z-norm: {m['euclidean_prices_norm']:.4f}",
            f"- Euclidiana retornos: {m['euclidean_returns']:.6f}",
            f"- Pearson retornos: {m['pearson_returns']:.6f}",
            f"- DTW completo: {m['dtw_returns']:.4f}",
            f"- DTW banda w={m['dtw_band_width']}: {m['dtw_returns_band']:.4f}",
            f"- Coseno retornos: {m['cosine_returns']:.6f}",
            "",
            "Complejidad por algoritmo:",
        ]
        metrics = _page_canvas("Metricas de similitud y complejidad", "Definiciones, formulas y costo computacional por metodo.", 2)
        _add_text_block(metrics, metric_lines, start_y=0.86, fontsize=9.8, line_gap=0.026, color=TEXT, width=92)
        _algorithm_cards(metrics, ALGORITHM_DOCS, start_y=0.52)
        _page_footer(metrics, "Las metricas se calculan sobre series alineadas y retornos diarios.")
        pdf.savefig(metrics)
        plt.close(metrics)

        risk_rows = []
        for item in riesgos[:15]:
            risk_rows.append(
                [
                    item["symbol"],
                    f"{item['annual_volatility'] * 100:.2f}%",
                    f"{item['annual_return'] * 100:.2f}%",
                    f"{item['sharpe_ratio']:.2f}",
                    item["risk_category"],
                ]
            )
        _table_page(
            pdf,
            "Ranking de riesgo por volatilidad",
            "Volatilidad anualizada, retorno anual estimado y Sharpe simplificado.",
            ["Activo", "Volatilidad", "Ret. anual", "Sharpe", "Categoria"],
            risk_rows,
            3,
        )

        charts_fig = plt.figure(figsize=(PAGE_W, PAGE_H))
        charts_fig.patch.set_facecolor("white")
        charts_fig.text(LEFT, TOP, "Series y velas", fontsize=18, weight="bold", color=TEXT)
        charts_fig.text(LEFT, 0.92, "Vista comparativa de precios y comportamiento tecnico del activo principal.", fontsize=10, color=MUTED)
        charts_fig.add_artist(
            Line2D([LEFT, RIGHT], [0.905, 0.905], transform=charts_fig.transFigure, color=ACCENT, linewidth=2.2)
        )
        charts_fig.add_artist(
            Line2D([LEFT, RIGHT], [0.055, 0.055], transform=charts_fig.transFigure, color=SOFT, linewidth=1.0)
        )
        ax_price = charts_fig.add_axes([0.08, 0.54, 0.84, 0.28])
        ax_candle = charts_fig.add_axes([0.08, 0.16, 0.84, 0.28])
        _price_chart(ax_price, comparacion, simbolo_a, simbolo_b)
        _candle_chart(ax_candle, dataset, simbolo_a)
        charts_fig.text(LEFT, 0.03, "El activo de velas corresponde al primer simbolo de la comparacion.", fontsize=8, color=MUTED)
        pdf.savefig(charts_fig)
        plt.close(charts_fig)

        heatmap_fig = plt.figure(figsize=(PAGE_W, PAGE_H))
        heatmap_fig.patch.set_facecolor("white")
        heatmap_fig.text(LEFT, TOP, "Mapa de correlacion", fontsize=18, weight="bold", color=TEXT)
        heatmap_fig.text(LEFT, 0.92, "Correlacion Pearson entre retornos diarios de todos los activos disponibles.", fontsize=10, color=MUTED)
        heatmap_fig.add_artist(
            Line2D([LEFT, RIGHT], [0.905, 0.905], transform=heatmap_fig.transFigure, color=ACCENT, linewidth=2.2)
        )
        heatmap_fig.add_artist(
            Line2D([LEFT, RIGHT], [0.055, 0.055], transform=heatmap_fig.transFigure, color=SOFT, linewidth=1.0)
        )
        ax_heat = heatmap_fig.add_axes([0.14, 0.14, 0.70, 0.70])
        im = _heatmap_chart(ax_heat, correlacion)
        cax = heatmap_fig.add_axes([0.86, 0.16, 0.025, 0.62])
        heatmap_fig.colorbar(im, cax=cax)
        heatmap_fig.text(LEFT, 0.08, "Valores cercanos a 1 indican co-movimiento fuerte; cercanos a -1, relacion inversa.", fontsize=8, color=MUTED)
        pdf.savefig(heatmap_fig)
        plt.close(heatmap_fig)

    return ruta_salida
