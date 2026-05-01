import csv
import math
from pathlib import Path

from src.paths import PROJECT_ROOT


BASE_DIR = PROJECT_ROOT


def cargar_dataset(ruta_archivo):
    ruta = Path(ruta_archivo)
    if not ruta.is_absolute():
        ruta = BASE_DIR / ruta
    dataset = []
    with ruta.open(mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            dataset.append(fila)
    return dataset


def extraer_simbolos(dataset):
    if not dataset:
        return []
    simbolos = set()
    for columna in dataset[0].keys():
        if columna.endswith("_Close"):
            simbolos.add(columna[:-6])
    return sorted(simbolos)


def _to_float(value):
    try:
        if value in (None, ""):
            return None
        number = float(value)
        if number != number:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _col(simbolo, campo):
    return f"{simbolo}_{campo}"


def serie_campo(dataset, simbolo, campo="Close"):
    serie = []
    columna = _col(simbolo, campo)
    for fila in dataset:
        valor = _to_float(fila.get(columna))
        if valor is not None:
            serie.append({"fecha": fila.get("Fecha"), "valor": valor})
    return serie


def serie_ohlcv(dataset, simbolo):
    serie = []
    for fila in dataset:
        close_value = _to_float(fila.get(_col(simbolo, "Close")))
        if close_value is None:
            continue
        open_value = _to_float(fila.get(_col(simbolo, "Open"))) or close_value
        high_value = _to_float(fila.get(_col(simbolo, "High"))) or max(open_value, close_value)
        low_value = _to_float(fila.get(_col(simbolo, "Low"))) or min(open_value, close_value)
        volume_value = _to_float(fila.get(_col(simbolo, "Volume"))) or 0.0
        serie.append(
            {
                "fecha": fila.get("Fecha"),
                "open": open_value,
                "high": max(high_value, open_value, close_value),
                "low": min(low_value, open_value, close_value),
                "close": close_value,
                "volume": volume_value,
            }
        )
    return serie


def alinear_series(dataset, simbolo_a, simbolo_b, campo="Close"):
    col_a = _col(simbolo_a, campo)
    col_b = _col(simbolo_b, campo)
    fechas, a, b = [], [], []
    for fila in dataset:
        valor_a = _to_float(fila.get(col_a))
        valor_b = _to_float(fila.get(col_b))
        if valor_a is not None and valor_b is not None:
            fechas.append(fila.get("Fecha"))
            a.append(valor_a)
            b.append(valor_b)
    return fechas, a, b


def retornos_desde_precios(precios):
    retornos = []
    for i in range(1, len(precios)):
        anterior = precios[i - 1]
        actual = precios[i]
        if anterior is None or actual is None or anterior == 0:
            continue
        retornos.append((actual - anterior) / anterior)
    return retornos


def alinear_retornos(dataset, simbolo_a, simbolo_b):
    fechas, precios_a, precios_b = alinear_series(dataset, simbolo_a, simbolo_b, "Close")
    fechas_retorno, ret_a, ret_b = [], [], []
    for i in range(1, len(fechas)):
        if precios_a[i - 1] == 0 or precios_b[i - 1] == 0:
            continue
        fechas_retorno.append(fechas[i])
        ret_a.append((precios_a[i] - precios_a[i - 1]) / precios_a[i - 1])
        ret_b.append((precios_b[i] - precios_b[i - 1]) / precios_b[i - 1])
    return fechas_retorno, ret_a, ret_b


def distancia_euclidiana(vector_a, vector_b):
    n = min(len(vector_a), len(vector_b))
    suma = 0.0
    for i in range(n):
        diferencia = vector_a[i] - vector_b[i]
        suma += diferencia * diferencia
    return math.sqrt(suma)


def media(vector):
    if not vector:
        return 0.0
    return sum(vector) / len(vector)


def desviacion_estandar_muestral(vector):
    n = len(vector)
    if n < 2:
        return 0.0
    promedio = media(vector)
    suma = 0.0
    for valor in vector:
        diferencia = valor - promedio
        suma += diferencia * diferencia
    return math.sqrt(suma / (n - 1))


def normalizar_zscore(vector):
    """Estandariza: z_i = (x_i - mu) / sigma. Permite comparar series en escalas distintas."""
    m = media(vector)
    s = desviacion_estandar_muestral(vector)
    if s == 0:
        return [0.0] * len(vector)
    return [(x - m) / s for x in vector]


def correlacion_pearson(vector_a, vector_b):
    n = min(len(vector_a), len(vector_b))
    if n < 2:
        return 0.0
    a = vector_a[:n]
    b = vector_b[:n]
    media_a = media(a)
    media_b = media(b)
    covarianza = 0.0
    suma_a = 0.0
    suma_b = 0.0
    for i in range(n):
        da = a[i] - media_a
        db = b[i] - media_b
        covarianza += da * db
        suma_a += da * da
        suma_b += db * db
    denominador = math.sqrt(suma_a * suma_b)
    if denominador == 0:
        return 0.0
    return covarianza / denominador


def similitud_coseno(vector_a, vector_b):
    n = min(len(vector_a), len(vector_b))
    producto = 0.0
    norma_a = 0.0
    norma_b = 0.0
    for i in range(n):
        producto += vector_a[i] * vector_b[i]
        norma_a += vector_a[i] * vector_a[i]
        norma_b += vector_b[i] * vector_b[i]
    denominador = math.sqrt(norma_a) * math.sqrt(norma_b)
    if denominador == 0:
        return 0.0
    return producto / denominador


def distancia_dtw(vector_a, vector_b, banda=None):
    n = len(vector_a)
    m = len(vector_b)
    if n == 0 or m == 0:
        return {"distance": 0.0, "path": [], "matrix_shape": [n, m], "banda": banda}

    # Banda Sakoe-Chiba: solo calcula celdas donde |i-j| <= w.
    # Sin banda (None) se usa la matriz completa -> O(n*m).
    # Con banda w -> O(n*w), aceleracion proporcional al ancho de banda.
    w = banda if banda is not None else max(n, m)
    infinito = float("inf")
    matriz = [[infinito] * (m + 1) for _ in range(n + 1)]
    matriz[0][0] = 0.0

    for i in range(1, n + 1):
        j_inicio = max(1, i - w)
        j_fin = min(m, i + w) + 1
        for j in range(j_inicio, j_fin):
            costo = abs(vector_a[i - 1] - vector_b[j - 1])
            matriz[i][j] = costo + min(
                matriz[i - 1][j],
                matriz[i][j - 1],
                matriz[i - 1][j - 1],
            )

    i, j = n, m
    ruta = []
    while i > 0 and j > 0:
        ruta.append([i - 1, j - 1])
        opciones = [
            (matriz[i - 1][j - 1], i - 1, j - 1),
            (matriz[i - 1][j], i - 1, j),
            (matriz[i][j - 1], i, j - 1),
        ]
        _, i, j = min(opciones, key=lambda item: item[0])

    while i > 0:
        ruta.append([i - 1, 0])
        i -= 1
    while j > 0:
        ruta.append([0, j - 1])
        j -= 1
    ruta.reverse()

    return {
        "distance": matriz[n][m],
        "path": ruta,
        "matrix_shape": [n, m],
        "path_length": len(ruta),
        "banda": banda,
    }


def comparar_activos(dataset, simbolo_a, simbolo_b, dtw_banda=100):
    fechas, precios_a, precios_b = alinear_series(dataset, simbolo_a, simbolo_b, "Close")
    fechas_ret, ret_a, ret_b = alinear_retornos(dataset, simbolo_a, simbolo_b)
    # Z-normalizar precios para distancia euclidiana comparable entre escalas
    precios_a_norm = normalizar_zscore(precios_a)
    precios_b_norm = normalizar_zscore(precios_b)
    dtw_full = distancia_dtw(ret_a, ret_b)
    dtw_band = distancia_dtw(ret_a, ret_b, banda=dtw_banda)
    return {
        "symbols": [simbolo_a, simbolo_b],
        "observations_prices": len(fechas),
        "observations_returns": len(fechas_ret),
        "prices": {
            "dates": fechas,
            simbolo_a: precios_a,
            simbolo_b: precios_b,
        },
        "returns": {
            "dates": fechas_ret,
            simbolo_a: ret_a,
            simbolo_b: ret_b,
        },
        "metrics": {
            "euclidean_prices": distancia_euclidiana(precios_a, precios_b),
            "euclidean_prices_norm": distancia_euclidiana(precios_a_norm, precios_b_norm),
            "euclidean_returns": distancia_euclidiana(ret_a, ret_b),
            "pearson_returns": correlacion_pearson(ret_a, ret_b),
            "dtw_returns": dtw_full["distance"],
            "dtw_returns_band": dtw_band["distance"],
            "dtw_band_width": dtw_banda,
            "dtw_path_length": dtw_full.get("path_length", 0),
            "cosine_returns": similitud_coseno(ret_a, ret_b),
        },
    }


def media_movil_simple(valores, ventana):
    # Index-based sliding window: O(n) time, O(1) extra space.
    # Avoids list.pop(0) which is O(n) and would make the overall loop O(n^2).
    resultado = []
    suma = 0.0
    for i, valor in enumerate(valores):
        suma += valor
        if i >= ventana:
            suma -= valores[i - ventana]
        if i >= ventana - 1:
            resultado.append(suma / ventana)
        else:
            resultado.append(None)
    return resultado


def contar_patrones(retornos, k=3, umbral_rebote=0.03):
    positivos = 0
    rebotes = 0
    n = len(retornos)

    for i in range(0, n - k + 1):
        cumple = True
        for j in range(k):
            if retornos[i + j] <= 0:
                cumple = False
                break
        if cumple:
            positivos += 1

    for i in range(0, n - k):
        negativos = True
        for j in range(k):
            if retornos[i + j] >= 0:
                negativos = False
                break
        if negativos and retornos[i + k] >= umbral_rebote:
            rebotes += 1

    return {
        "positive_streak_k": positivos,
        "negative_then_strong_rebound": rebotes,
        "k": k,
        "rebound_threshold": umbral_rebote,
    }


def estadisticas_riesgo(dataset):
    resultados = []
    for simbolo in extraer_simbolos(dataset):
        precios = [item["valor"] for item in serie_campo(dataset, simbolo, "Close")]
        retornos = retornos_desde_precios(precios)
        media_diaria = media(retornos)
        desviacion_diaria = desviacion_estandar_muestral(retornos)
        volatilidad_anual = desviacion_diaria * math.sqrt(252)
        if volatilidad_anual < 0.10:
            categoria = "conservador"
        elif volatilidad_anual <= 0.20:
            categoria = "moderado"
        else:
            categoria = "agresivo"
        annual_return = media_diaria * 252
        # Sharpe simplificado (sin tasa libre de riesgo): retorno_anual / volatilidad_anual
        sharpe_ratio = annual_return / volatilidad_anual if volatilidad_anual > 0 else 0.0
        resultados.append(
            {
                "symbol": simbolo,
                "mean_daily_return": media_diaria,
                "std_daily_return": desviacion_diaria,
                "annual_volatility": volatilidad_anual,
                "annual_return": annual_return,
                "sharpe_ratio": sharpe_ratio,
                "risk_category": categoria,
                "observations": len(retornos),
            }
        )
    resultados.sort(key=lambda item: item["annual_volatility"], reverse=True)
    return resultados


def matriz_correlacion(dataset):
    simbolos = extraer_simbolos(dataset)
    retornos_por_simbolo = {}
    min_len = None
    for simbolo in simbolos:
        precios = [item["valor"] for item in serie_campo(dataset, simbolo, "Close")]
        retornos = retornos_desde_precios(precios)
        retornos_por_simbolo[simbolo] = retornos
        min_len = len(retornos) if min_len is None else min(min_len, len(retornos))

    if min_len is None:
        min_len = 0

    matriz = []
    for simbolo_i in simbolos:
        fila = []
        for simbolo_j in simbolos:
            fila.append(
                correlacion_pearson(
                    retornos_por_simbolo[simbolo_i][-min_len:] if min_len else [],
                    retornos_por_simbolo[simbolo_j][-min_len:] if min_len else [],
                )
            )
        matriz.append(fila)
    return {"symbols": simbolos, "matrix": matriz}


ALGORITHM_DOCS = {
    "euclidean": {
        "formula": "d_E(P,Q) = sqrt( sum_{i=0}^{n-1} (p_i - q_i)^2 )",
        "formula_norm": "Normalizado Z: z_i = (x_i - mu) / sigma antes de calcular",
        "time": "O(n)",
        "space": "O(1)",
        "pseudocode": "suma=0; for i in range(n): suma+=(a[i]-b[i])^2; return sqrt(suma)",
        "use": "Precios crudos, precios Z-normalizados (comparacion entre escalas) y retornos.",
    },
    "pearson": {
        "formula": "r_xy = cov(X,Y) / (sigma_X * sigma_Y)",
        "formula_expanded": "= sum((x_i-x̄)(y_i-ȳ)) / sqrt(sum(x_i-x̄)^2 * sum(y_i-ȳ)^2)",
        "time": "O(n)",
        "space": "O(1)",
        "pseudocode": "calcular medias; acumular cov, ss_a, ss_b en un bucle; return cov/sqrt(ss_a*ss_b)",
        "use": "r=1: perfecta. r=0: sin relacion. r=-1: inversa. Sobre retornos diarios.",
    },
    "dtw": {
        "formula": "D(i,j) = |p_i - q_j| + min(D(i-1,j), D(i,j-1), D(i-1,j-1))",
        "formula_band": "Sakoe-Chiba: calcular solo si |i-j| <= w => O(n*w)",
        "time": "O(n*m) sin banda | O(n*w) con banda Sakoe-Chiba",
        "space": "O(n*m)",
        "pseudocode": "init D=inf; D[0][0]=0; DP dentro de banda; backtrack desde (n,m)",
        "use": "Alinea series con distorsion temporal. Banda reduce complejidad de O(n^2) a O(n*w).",
    },
    "cosine": {
        "formula": "cos(P,Q) = (P · Q) / (||P|| * ||Q||)",
        "formula_expanded": "= sum(p_i*q_i) / (sqrt(sum(p_i^2)) * sqrt(sum(q_i^2)))",
        "time": "O(n)",
        "space": "O(1)",
        "pseudocode": "dot=0; na=0; nb=0; for i: dot+=a*b; na+=a^2; nb+=b^2; return dot/sqrt(na*nb)",
        "use": "Valores ~ 1: misma direccion. ~ -1: opuesta. Insensible a escala de magnitud.",
    },
}

PATTERN_DOCS = {
    "positive_streak": {
        "name": "Racha alcista (P1)",
        "formal": "P1(i,k): ∀j ∈ [i, i+k−1]  →  r_j > 0",
        "description": "k dias consecutivos con retorno positivo. Detecta impulsos alcistas sostenidos.",
        "complexity": "O(n·k)",
    },
    "negative_rebound": {
        "name": "Rebote tras caida (P2)",
        "formal": "P2(i,k,θ): (∀j ∈ [i, i+k−1] → r_j < 0)  ∧  r_{i+k} ≥ θ",
        "description": "k dias negativos seguidos de rebote >= θ. Modela recuperaciones post-correccion.",
        "complexity": "O(n·k)",
    },
}
