import json
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory

from analisis_financiero import (
    ALGORITHM_DOCS,
    PATTERN_DOCS,
    cargar_dataset,
    comparar_activos,
    contar_patrones,
    estadisticas_riesgo,
    extraer_simbolos,
    matriz_correlacion,
    retornos_desde_precios,
    serie_campo,
)
from extraccion_datos import DEFAULT_SYMBOLS, construir_dataset_maestro
from reporte_pdf import generar_reporte_pdf
from visualizacion import (
    generar_barras_riesgo,
    generar_grafico_retornos,
    generar_grafico_series,
    generar_grafico_velas,
    generar_heatmap_correlacion,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATASET_CANDIDATES = ("dataset_maestro.csv",)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")


def _json_error(message, status_code=400):
    response = jsonify({"detail": message})
    response.status_code = status_code
    return response


def resolve_dataset_path(ruta_archivo=None):
    if ruta_archivo:
        path = Path(ruta_archivo)
        if not path.is_absolute():
            path = BASE_DIR / ruta_archivo
        if path.exists():
            return path
        return None

    for candidate in DATASET_CANDIDATES:
        path = BASE_DIR / candidate
        if path.exists():
            return path
    return None


def load_dataset_or_error():
    ruta = request.args.get("ruta_archivo")
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        ruta = payload.get("ruta_archivo", ruta)

    dataset_path = resolve_dataset_path(ruta)
    if not dataset_path:
        return None, None, _json_error("No se encontro dataset_maestro.csv. Reconstruya el dataset.", 404)
    try:
        dataset = cargar_dataset(dataset_path)
        return dataset, dataset_path, None
    except Exception as error:
        return None, None, _json_error(f"No se pudo cargar el dataset: {error}", 500)


def dataset_overview_payload(dataset, dataset_path, preview_rows=5):
    simbolos = extraer_simbolos(dataset)
    fechas = [fila["Fecha"] for fila in dataset if fila.get("Fecha")]
    payload = {
        "source_file": dataset_path.name,
        "source_path": str(dataset_path),
        "rows": len(dataset),
        "columns": len(dataset[0]) if dataset else 0,
        "symbols": simbolos,
        "symbol_count": len(simbolos),
        "date_min": min(fechas) if fechas else None,
        "date_max": max(fechas) if fechas else None,
        "preview": dataset[:preview_rows],
    }
    # Incluir reporte ETL si fue guardado junto al CSV
    report_path = dataset_path.parent / (dataset_path.stem + "_report.json")
    if report_path.exists():
        try:
            with report_path.open("r", encoding="utf-8") as f:
                payload["etl_report"] = json.load(f)
        except Exception:
            pass
    return payload


@app.get("/")
def home():
    return redirect("/ui/etl", code=302)


@app.get("/ui/etl")
def page_etl():
    return send_from_directory(STATIC_DIR / "modules" / "etl", "index.html")


@app.get("/ui/similarity")
def page_similarity():
    return send_from_directory(STATIC_DIR / "modules" / "similarity", "index.html")


@app.get("/ui/patterns")
def page_patterns():
    return send_from_directory(STATIC_DIR / "modules" / "patterns", "index.html")


@app.get("/ui/visualization")
def page_visualization():
    return send_from_directory(STATIC_DIR / "modules" / "visualization", "index.html")


@app.get("/ui/docs")
def page_docs():
    return send_from_directory(STATIC_DIR / "modules" / "docs", "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "framework": "Flask"})


@app.get("/algorithm-docs")
def algorithm_docs():
    return jsonify(ALGORITHM_DOCS)


@app.get("/pattern-docs")
def pattern_docs():
    return jsonify(PATTERN_DOCS)


@app.get("/dataset/overview")
def dataset_overview():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    return jsonify(dataset_overview_payload(dataset, dataset_path))


@app.post("/dataset/build")
def build_dataset():
    payload = request.get_json(silent=True) or {}
    simbolos = payload.get("simbolos") or DEFAULT_SYMBOLS
    years = int(payload.get("years", 5))
    interval = payload.get("interval", "1d")
    timeout = int(payload.get("timeout", 15))
    pausa = float(payload.get("pausa_segundos", 0.35))
    nombre = payload.get("nombre_archivo", "dataset_maestro.csv")

    dataset, reporte = construir_dataset_maestro(
        simbolos=simbolos,
        years=years,
        interval=interval,
        timeout=timeout,
        pausa_segundos=pausa,
        guardar_csv=True,
        nombre_archivo=nombre,
    )
    if not dataset:
        return _json_error("No se pudo construir el dataset.", 502)
    return jsonify({"rows": len(dataset), "report": reporte, "preview": dataset[:3]})


@app.post("/similarity")
def similarity():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    simbolo_a = payload.get("symbol_a")
    simbolo_b = payload.get("symbol_b")
    simbolos = extraer_simbolos(dataset)
    if simbolo_a not in simbolos or simbolo_b not in simbolos:
        return _json_error(f"Seleccione dos activos validos. Disponibles: {', '.join(simbolos)}")
    comparacion = comparar_activos(dataset, simbolo_a, simbolo_b)
    # Keep API responses light; full images are served by plotting endpoints.
    comparacion["prices"]["dates"] = comparacion["prices"]["dates"][-250:]
    comparacion["prices"][simbolo_a] = comparacion["prices"][simbolo_a][-250:]
    comparacion["prices"][simbolo_b] = comparacion["prices"][simbolo_b][-250:]
    comparacion["returns"]["dates"] = comparacion["returns"]["dates"][-250:]
    comparacion["returns"][simbolo_a] = comparacion["returns"][simbolo_a][-250:]
    comparacion["returns"][simbolo_b] = comparacion["returns"][simbolo_b][-250:]
    return jsonify(comparacion)


@app.get("/risk")
def risk():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    return jsonify({"items": estadisticas_riesgo(dataset)})


@app.get("/patterns")
def patterns():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    simbolo = request.args.get("symbol")
    k = int(request.args.get("k", 3))
    threshold = float(request.args.get("threshold", 0.03))
    simbolos = extraer_simbolos(dataset)
    if simbolo not in simbolos:
        return _json_error(f"Simbolo invalido. Disponibles: {', '.join(simbolos)}")
    precios = [item["valor"] for item in serie_campo(dataset, simbolo, "Close")]
    retornos = retornos_desde_precios(precios)
    return jsonify({"symbol": simbolo, "patterns": contar_patrones(retornos, k=k, umbral_rebote=threshold)})


@app.get("/correlation")
def correlation():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    return jsonify(matriz_correlacion(dataset))


@app.get("/plot/correlation.png")
def plot_correlation():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    return send_file(
        __import__("io").BytesIO(generar_heatmap_correlacion(dataset)),
        mimetype="image/png",
        download_name="correlacion.png",
    )


@app.get("/plot/candlestick.png")
def plot_candlestick():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    simbolo = request.args.get("symbol")
    short_window = int(request.args.get("short_window", 20))
    long_window = int(request.args.get("long_window", 50))
    if simbolo not in extraer_simbolos(dataset):
        return _json_error("Simbolo invalido.")
    try:
        png = generar_grafico_velas(dataset, simbolo, short_window, long_window)
    except Exception as error:
        return _json_error(str(error), 500)
    return send_file(__import__("io").BytesIO(png), mimetype="image/png", download_name=f"velas_{simbolo}.png")


@app.get("/plot/returns.png")
def plot_returns():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    simbolo_a = request.args.get("symbol_a")
    simbolo_b = request.args.get("symbol_b")
    simbolos = extraer_simbolos(dataset)
    if simbolo_a not in simbolos or simbolo_b not in simbolos:
        return _json_error("Simbolos invalidos.")
    png = generar_grafico_retornos(comparar_activos(dataset, simbolo_a, simbolo_b))
    return send_file(__import__("io").BytesIO(png), mimetype="image/png", download_name="retornos.png")


@app.get("/plot/series.png")
def plot_series():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    simbolo_a = request.args.get("symbol_a")
    simbolo_b = request.args.get("symbol_b")
    if simbolo_a not in extraer_simbolos(dataset) or simbolo_b not in extraer_simbolos(dataset):
        return _json_error("Simbolos invalidos.")
    png = generar_grafico_series(comparar_activos(dataset, simbolo_a, simbolo_b))
    return send_file(__import__("io").BytesIO(png), mimetype="image/png", download_name="series.png")


@app.get("/plot/risk.png")
def plot_risk():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    png = generar_barras_riesgo(estadisticas_riesgo(dataset))
    return send_file(__import__("io").BytesIO(png), mimetype="image/png", download_name="riesgo.png")


@app.get("/report.pdf")
def report_pdf():
    dataset, _, error = load_dataset_or_error()
    if error:
        return error
    simbolos = extraer_simbolos(dataset)
    symbol_a = request.args.get("symbol_a") or (simbolos[0] if simbolos else None)
    symbol_b = request.args.get("symbol_b") or (simbolos[1] if len(simbolos) > 1 else symbol_a)
    if symbol_a not in simbolos or symbol_b not in simbolos:
        return _json_error("Simbolos invalidos para reporte.")
    ruta = generar_reporte_pdf(dataset, symbol_a, symbol_b)
    return send_file(ruta, mimetype="application/pdf", as_attachment=True, download_name=ruta.name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
