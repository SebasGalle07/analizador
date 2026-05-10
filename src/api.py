import json
import logging
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, request, send_file, send_from_directory

from src.analisis_financiero import (
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
from src.extraccion_datos import (
    COLOMBIA_SYMBOLS,
    DEFAULT_SYMBOLS,
    GLOBAL_SYMBOLS,
    construir_dataset_maestro,
)
from src.paths import PROJECT_ROOT, STATIC_DIR
from src.reporte_pdf import generar_reporte_pdf
from src.visualizacion import (
    generar_barras_riesgo,
    generar_grafico_retornos,
    generar_grafico_series,
    generar_grafico_velas,
    generar_heatmap_correlacion,
)
from src.paths import get_runtime_processed_dir


RUNTIME_PROCESSED_DIR = get_runtime_processed_dir()
DATASET_CACHE = {}
JSON_CACHE = {}
PNG_CACHE = {}
MAX_CACHE_ENTRIES = 32
DATASET_CANDIDATES = (
    RUNTIME_PROCESSED_DIR / "dataset_maestro.json",
    RUNTIME_PROCESSED_DIR / "dataset_maestro.csv",
    PROJECT_ROOT / "data/processed/dataset_maestro.json",
    PROJECT_ROOT / "data/processed/dataset_maestro.csv",
    PROJECT_ROOT / "dataset_maestro.json",
    PROJECT_ROOT / "dataset_maestro.csv",
)

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
app.logger.setLevel(logging.INFO)


def _json_error(message, status_code=400):
    response = jsonify({"detail": message})
    response.status_code = status_code
    return response


def _cache_get(cache, key):
    return cache.get(key)


def _cache_set(cache, key, value):
    if key in cache:
        cache[key] = value
        return value
    if len(cache) >= MAX_CACHE_ENTRIES:
        cache.pop(next(iter(cache)))
    cache[key] = value
    return value


def _trim_similarity_payload(comparacion):
    # Keep API responses light; full images are served by plotting endpoints.
    comparacion["prices"]["dates"] = comparacion["prices"]["dates"][-250:]
    simbolo_a, simbolo_b = comparacion["symbols"]
    comparacion["prices"][simbolo_a] = comparacion["prices"][simbolo_a][-250:]
    comparacion["prices"][simbolo_b] = comparacion["prices"][simbolo_b][-250:]
    comparacion["returns"]["dates"] = comparacion["returns"]["dates"][-250:]
    comparacion["returns"][simbolo_a] = comparacion["returns"][simbolo_a][-250:]
    comparacion["returns"][simbolo_b] = comparacion["returns"][simbolo_b][-250:]
    return comparacion


def _dataset_fingerprint(path):
    stat = path.stat()
    return f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}"


def _load_dataset_cached(path):
    fingerprint = _dataset_fingerprint(path)
    cached = _cache_get(DATASET_CACHE, fingerprint)
    if cached is not None:
        return cached, fingerprint
    dataset = cargar_dataset(path)
    _cache_set(DATASET_CACHE, fingerprint, dataset)
    return dataset, fingerprint


def _expand_dataset_candidates(path):
    if path.suffix.lower() in {".json", ".csv"}:
        return [path]
    return [path.with_suffix(".json"), path.with_suffix(".csv"), path]


def resolve_dataset_path(ruta_archivo=None):
    if ruta_archivo:
        original_path = Path(ruta_archivo)
        is_relative = not original_path.is_absolute()
        path = original_path if not is_relative else PROJECT_ROOT / ruta_archivo
        search_paths = list(_expand_dataset_candidates(path))
        if is_relative:
            if len(original_path.parts) == 1:
                search_paths.extend(_expand_dataset_candidates(RUNTIME_PROCESSED_DIR / original_path.name))
            elif original_path.parts[:2] == ("data", "processed"):
                search_paths.extend(_expand_dataset_candidates(RUNTIME_PROCESSED_DIR / original_path.name))
        for candidate in search_paths:
            if candidate.exists():
                return candidate
        return None

    for candidate in DATASET_CANDIDATES:
        for expanded in _expand_dataset_candidates(Path(candidate)):
            if expanded.exists():
                return expanded
    return None


def load_dataset_or_error():
    ruta = request.args.get("ruta_archivo")
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        ruta = payload.get("ruta_archivo", ruta)

    dataset_path = resolve_dataset_path(ruta)
    if not dataset_path:
        return None, None, _json_error("No se encontro el dataset maestro. Reconstruya el dataset.", 404)
    try:
        dataset, _ = _load_dataset_cached(dataset_path)
        return dataset, dataset_path, None
    except Exception as error:
        return None, None, _json_error(f"No se pudo cargar el dataset: {error}", 500)


def dataset_overview_payload(dataset, dataset_path, preview_rows=5):
    stat = dataset_path.stat()
    version = f"{stat.st_mtime_ns}-{stat.st_size}"
    simbolos = extraer_simbolos(dataset)
    fechas = [fila["Fecha"] for fila in dataset if fila.get("Fecha")]
    symbol_groups = [
        {"label": "Activos colombianos", "symbols": COLOMBIA_SYMBOLS},
        {"label": "Activos globales", "symbols": GLOBAL_SYMBOLS},
    ]
    payload = {
        "source_file": dataset_path.name,
        "source_path": str(dataset_path),
        "dataset_version": version,
        "rows": len(dataset),
        "columns": len(dataset[0]) if dataset else 0,
        "symbols": simbolos,
        "symbol_count": len(simbolos),
        "symbol_groups": symbol_groups,
        "date_min": min(fechas) if fechas else None,
        "date_max": max(fechas) if fechas else None,
        "preview": dataset[:preview_rows],
    }
    # Incluir reporte ETL si fue guardado junto al CSV
    report_path = dataset_path.parent / (dataset_path.stem + "_report.json")
    if report_path.exists():
        try:
            with report_path.open("r", encoding="utf-8") as f:
                etl_report = json.load(f)
                payload["etl_report"] = etl_report
                payload["etl_summary"] = {
                    "source": etl_report.get("fuente"),
                    "years_requested": etl_report.get("years_solicitados"),
                    "assets_requested": etl_report.get("activos_solicitados"),
                    "assets_downloaded": etl_report.get("activos_descargados"),
                    "final_range": etl_report.get("rango_final"),
                    "warnings": etl_report.get("advertencias", []),
                }
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


def _json_response_cache(key, builder):
    cached = _cache_get(JSON_CACHE, key)
    if cached is not None:
        return jsonify(cached)
    data = builder()
    _cache_set(JSON_CACHE, key, data)
    return jsonify(data)


def _png_response_cache(key, builder, download_name):
    cached = _cache_get(PNG_CACHE, key)
    if cached is None:
        cached = builder()
        _cache_set(PNG_CACHE, key, cached)
    response = send_file(
        __import__("io").BytesIO(cached),
        mimetype="image/png",
        download_name=download_name,
    )
    response.headers["Cache-Control"] = "public, max-age=86400, immutable"
    return response


@app.post("/dataset/build")
def build_dataset():
    payload = request.get_json(silent=True) or {}
    simbolos = payload.get("simbolos") or DEFAULT_SYMBOLS
    years = int(payload.get("years", 5))
    interval = payload.get("interval", "1d")
    timeout = int(payload.get("timeout", 15))
    pausa = float(payload.get("pausa_segundos", 0.35))
    nombre = payload.get("nombre_archivo")
    if not nombre:
        nombre = str(RUNTIME_PROCESSED_DIR / "dataset_maestro.json")
    else:
        nombre_path = Path(nombre)
        if nombre_path.suffix.lower() not in {".json", ".csv"}:
            nombre_path = nombre_path.with_suffix(".json")
        if not nombre_path.is_absolute():
            if len(nombre_path.parts) == 1:
                nombre = str(RUNTIME_PROCESSED_DIR / nombre_path)
            elif nombre_path.parts[:2] == ("data", "processed"):
                nombre = str(RUNTIME_PROCESSED_DIR / nombre_path.name)
            else:
                nombre = str(PROJECT_ROOT / nombre_path)

    app.logger.info(
        "API | ETL solicitado | simbolos=%s | anos=%s | intervalo=%s",
        len(simbolos),
        years,
        interval,
    )

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
        app.logger.error("API | ETL fallido | no se construyo dataset")
        return _json_error("No se pudo construir el dataset.", 502)

    DATASET_CACHE.clear()
    JSON_CACHE.clear()
    PNG_CACHE.clear()

    resumen = reporte.get("validacion", {})
    app.logger.info(
        "API | ETL completado | activos=%s | filas=%s | rango=%s..%s",
        reporte.get("activos_descargados", 0),
        len(dataset),
        (resumen.get("rango_final") or {}).get("inicio"),
        (resumen.get("rango_final") or {}).get("fin"),
    )
    return jsonify({"rows": len(dataset), "report": reporte, "preview": dataset[:3]})


@app.post("/similarity")
def similarity():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    payload = request.get_json(silent=True) or {}
    simbolo_a = payload.get("symbol_a")
    simbolo_b = payload.get("symbol_b")
    try:
        dtw_banda = int(payload.get("dtw_banda", 100))
    except (TypeError, ValueError):
        return _json_error("La banda DTW debe ser un numero entero valido.")
    if dtw_banda < 1:
        return _json_error("La banda DTW debe ser mayor o igual a 1.")
    simbolos = extraer_simbolos(dataset)
    if simbolo_a not in simbolos or simbolo_b not in simbolos:
        return _json_error(f"Seleccione dos activos validos. Disponibles: {', '.join(simbolos)}")
    if simbolo_a == simbolo_b:
        return _json_error("Seleccione dos activos diferentes para comparar.")
    dataset_key = _dataset_fingerprint(dataset_path)
    cache_key = ("similarity", dataset_key, simbolo_a, simbolo_b, dtw_banda)
    return _json_response_cache(
        cache_key,
        lambda: _trim_similarity_payload(comparar_activos(dataset, simbolo_a, simbolo_b, dtw_banda=dtw_banda)),
    )


@app.get("/risk")
def risk():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    cache_key = ("risk", _dataset_fingerprint(dataset_path))
    return _json_response_cache(cache_key, lambda: {"items": estadisticas_riesgo(dataset)})


@app.get("/patterns")
def patterns():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    simbolo = request.args.get("symbol")
    try:
        k = int(request.args.get("k", 3))
        threshold = float(request.args.get("threshold", 0.03))
    except (TypeError, ValueError):
        return _json_error("Los parametros k y threshold deben ser numericos validos.")
    if k < 2:
        return _json_error("k debe ser mayor o igual a 2.")
    if threshold <= 0 or threshold >= 1:
        return _json_error("threshold debe estar entre 0 y 1.")
    simbolos = extraer_simbolos(dataset)
    if simbolo not in simbolos:
        return _json_error(f"Simbolo invalido. Disponibles: {', '.join(simbolos)}")
    dataset_key = _dataset_fingerprint(dataset_path)
    cache_key = ("patterns", dataset_key, simbolo, k, threshold)
    return _json_response_cache(
        cache_key,
        lambda: {
            "symbol": simbolo,
            "patterns": contar_patrones(
                retornos_desde_precios([item["valor"] for item in serie_campo(dataset, simbolo, "Close")]),
                k=k,
                umbral_rebote=threshold,
            ),
        },
    )


@app.get("/correlation")
def correlation():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    cache_key = ("correlation", _dataset_fingerprint(dataset_path))
    return _json_response_cache(cache_key, lambda: matriz_correlacion(dataset))


@app.get("/plot/correlation.png")
def plot_correlation():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    cache_key = ("plot_correlation", _dataset_fingerprint(dataset_path))
    return _png_response_cache(cache_key, lambda: generar_heatmap_correlacion(dataset), "correlacion.png")


@app.get("/plot/candlestick.png")
def plot_candlestick():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    simbolo = request.args.get("symbol")
    short_window = int(request.args.get("short_window", 20))
    long_window = int(request.args.get("long_window", 50))
    if simbolo not in extraer_simbolos(dataset):
        return _json_error("Simbolo invalido.")
    try:
        cache_key = ("plot_candlestick", _dataset_fingerprint(dataset_path), simbolo, short_window, long_window)
        return _png_response_cache(
            cache_key,
            lambda: generar_grafico_velas(dataset, simbolo, short_window, long_window),
            f"velas_{simbolo}.png",
        )
    except Exception as error:
        return _json_error(str(error), 500)


@app.get("/plot/returns.png")
def plot_returns():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    simbolo_a = request.args.get("symbol_a")
    simbolo_b = request.args.get("symbol_b")
    simbolos = extraer_simbolos(dataset)
    if simbolo_a not in simbolos or simbolo_b not in simbolos:
        return _json_error("Simbolos invalidos.")
    cache_key = ("plot_returns", _dataset_fingerprint(dataset_path), simbolo_a, simbolo_b)
    return _png_response_cache(
        cache_key,
        lambda: generar_grafico_retornos(comparar_activos(dataset, simbolo_a, simbolo_b)),
        "retornos.png",
    )


@app.get("/plot/series.png")
def plot_series():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    simbolo_a = request.args.get("symbol_a")
    simbolo_b = request.args.get("symbol_b")
    if simbolo_a not in extraer_simbolos(dataset) or simbolo_b not in extraer_simbolos(dataset):
        return _json_error("Simbolos invalidos.")
    cache_key = ("plot_series", _dataset_fingerprint(dataset_path), simbolo_a, simbolo_b)
    return _png_response_cache(
        cache_key,
        lambda: generar_grafico_series(comparar_activos(dataset, simbolo_a, simbolo_b)),
        "series.png",
    )


@app.get("/plot/risk.png")
def plot_risk():
    dataset, dataset_path, error = load_dataset_or_error()
    if error:
        return error
    cache_key = ("plot_risk", _dataset_fingerprint(dataset_path))
    return _png_response_cache(
        cache_key,
        lambda: generar_barras_riesgo(estadisticas_riesgo(dataset)),
        "riesgo.png",
    )


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
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug, use_reloader=False)
