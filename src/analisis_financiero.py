import json
import csv
import math
from pathlib import Path

from src.estructuras_datos import (
    ConjuntoManual,
    ListaDinamica,
    TablaHashSimple,
    claves_diccionario,
    crear_matriz,
    mayor_de_dos,
    mayor_de_tres,
    menor_de_dos,
    menor_de_tres,
    obtener_valor,
    ordenar_por_seleccion,
    sumatoria,
    ultimos_elementos,
)
from src.paths import PROJECT_ROOT


BASE_DIR = PROJECT_ROOT


def cargar_dataset(ruta_archivo):
    ruta = Path(ruta_archivo)
    if not ruta.is_absolute():
        ruta = BASE_DIR / ruta
    if ruta.suffix.lower() == ".json":
        with ruta.open(mode="r", encoding="utf-8") as archivo:
            contenido = json.load(archivo)
        if isinstance(contenido, list):
            datos = ListaDinamica()
            for fila in contenido:
                datos.agregar(fila)
            return datos.a_lista()
        if isinstance(contenido, dict):
            for clave in ("dataset", "rows", "data", "items"):
                valor = obtener_valor(contenido, clave)
                if isinstance(valor, list):
                    datos = ListaDinamica()
                    for fila in valor:
                        datos.agregar(fila)
                    return datos.a_lista()
        raise ValueError(f"Formato JSON invalido para {ruta.name}")

    dataset = ListaDinamica()
    with ruta.open(mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            dataset.agregar(fila)
    return dataset.a_lista()


def extraer_simbolos(dataset):
    if not dataset:
        return []
    simbolos = ConjuntoManual()
    for columna in claves_diccionario(dataset[0]):
        if columna.endswith("_Close"):
            simbolos.agregar(_quitar_sufijo_close(columna))
    return ordenar_por_seleccion(simbolos.a_lista(), lambda a, b: a < b)


def _quitar_sufijo_close(columna):
    limite = len(columna) - 6
    simbolo = ""
    i = 0
    while i < limite:
        simbolo += columna[i]
        i += 1
    return simbolo


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
    serie = ListaDinamica()
    columna = _col(simbolo, campo)
    for fila in dataset:
        valor = _to_float(obtener_valor(fila, columna))
        if valor is not None:
            serie.agregar({"fecha": obtener_valor(fila, "Fecha"), "valor": valor})
    return serie.a_lista()


def serie_ohlcv(dataset, simbolo):
    serie = ListaDinamica()
    for fila in dataset:
        close_value = _to_float(obtener_valor(fila, _col(simbolo, "Close")))
        if close_value is None:
            continue
        open_value = _to_float(obtener_valor(fila, _col(simbolo, "Open"))) or close_value
        high_value = _to_float(obtener_valor(fila, _col(simbolo, "High"))) or mayor_de_dos(open_value, close_value)
        low_value = _to_float(obtener_valor(fila, _col(simbolo, "Low"))) or menor_de_dos(open_value, close_value)
        volume_value = _to_float(obtener_valor(fila, _col(simbolo, "Volume"))) or 0.0
        serie.agregar(
            {
                "fecha": obtener_valor(fila, "Fecha"),
                "open": open_value,
                "high": mayor_de_tres(high_value, open_value, close_value),
                "low": menor_de_tres(low_value, open_value, close_value),
                "close": close_value,
                "volume": volume_value,
            }
        )
    return serie.a_lista()


def alinear_series(dataset, simbolo_a, simbolo_b, campo="Close"):
    col_a = _col(simbolo_a, campo)
    col_b = _col(simbolo_b, campo)
    fechas = ListaDinamica()
    a = ListaDinamica()
    b = ListaDinamica()
    for fila in dataset:
        valor_a = _to_float(obtener_valor(fila, col_a))
        valor_b = _to_float(obtener_valor(fila, col_b))
        if valor_a is not None and valor_b is not None:
            fechas.agregar(obtener_valor(fila, "Fecha"))
            a.agregar(valor_a)
            b.agregar(valor_b)
    return fechas.a_lista(), a.a_lista(), b.a_lista()


def retornos_desde_precios(precios):
    retornos = ListaDinamica()
    for i in range(1, len(precios)):
        anterior = precios[i - 1]
        actual = precios[i]
        if anterior is None or actual is None or anterior == 0:
            continue
        retornos.agregar((actual - anterior) / anterior)
    return retornos.a_lista()


def alinear_retornos(dataset, simbolo_a, simbolo_b):
    fechas, precios_a, precios_b = alinear_series(dataset, simbolo_a, simbolo_b, "Close")
    fechas_retorno = ListaDinamica()
    ret_a = ListaDinamica()
    ret_b = ListaDinamica()
    for i in range(1, len(fechas)):
        if precios_a[i - 1] == 0 or precios_b[i - 1] == 0:
            continue
        fechas_retorno.agregar(fechas[i])
        ret_a.agregar((precios_a[i] - precios_a[i - 1]) / precios_a[i - 1])
        ret_b.agregar((precios_b[i] - precios_b[i - 1]) / precios_b[i - 1])
    return fechas_retorno.a_lista(), ret_a.a_lista(), ret_b.a_lista()


def distancia_euclidiana(vector_a, vector_b):
    n = menor_de_dos(len(vector_a), len(vector_b))
    suma = 0.0
    for i in range(n):
        diferencia = vector_a[i] - vector_b[i]
        suma += diferencia * diferencia
    return math.sqrt(suma)


def media(vector):
    if not vector:
        return 0.0
    return sumatoria(vector) / len(vector)


def media_hasta(vector, limite):
    if limite <= 0:
        return 0.0
    suma = 0.0
    i = 0
    while i < limite:
        suma += vector[i]
        i += 1
    return suma / limite


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
    resultado = ListaDinamica(len(vector) if len(vector) > 0 else 1)
    if s == 0:
        i = 0
        while i < len(vector):
            resultado.agregar(0.0)
            i += 1
        return resultado.a_lista()
    for x in vector:
        resultado.agregar((x - m) / s)
    return resultado.a_lista()


def correlacion_pearson(vector_a, vector_b):
    n = menor_de_dos(len(vector_a), len(vector_b))
    if n < 2:
        return 0.0
    media_a = media_hasta(vector_a, n)
    media_b = media_hasta(vector_b, n)
    covarianza = 0.0
    suma_a = 0.0
    suma_b = 0.0
    for i in range(n):
        da = vector_a[i] - media_a
        db = vector_b[i] - media_b
        covarianza += da * db
        suma_a += da * da
        suma_b += db * db
    denominador = math.sqrt(suma_a * suma_b)
    if denominador == 0:
        return 0.0
    return covarianza / denominador


def similitud_coseno(vector_a, vector_b):
    n = menor_de_dos(len(vector_a), len(vector_b))
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
    w = banda if banda is not None else mayor_de_dos(n, m)
    infinito = float("inf")
    matriz = crear_matriz(n + 1, m + 1, infinito)
    matriz[0][0] = 0.0

    for i in range(1, n + 1):
        j_inicio = mayor_de_dos(1, i - w)
        j_fin = menor_de_dos(m, i + w) + 1
        for j in range(j_inicio, j_fin):
            costo = abs(vector_a[i - 1] - vector_b[j - 1])
            matriz[i][j] = costo + menor_de_tres(
                matriz[i - 1][j],
                matriz[i][j - 1],
                matriz[i - 1][j - 1],
            )

    i, j = n, m
    ruta = ListaDinamica()
    while i > 0 and j > 0:
        ruta.agregar([i - 1, j - 1])
        mejor_costo = matriz[i - 1][j - 1]
        mejor_i = i - 1
        mejor_j = j - 1
        if matriz[i - 1][j] < mejor_costo:
            mejor_costo = matriz[i - 1][j]
            mejor_i = i - 1
            mejor_j = j
        if matriz[i][j - 1] < mejor_costo:
            mejor_i = i
            mejor_j = j - 1
        i = mejor_i
        j = mejor_j

    while i > 0:
        ruta.agregar([i - 1, 0])
        i -= 1
    while j > 0:
        ruta.agregar([0, j - 1])
        j -= 1
    ruta.invertir_en_sitio()
    ruta_final = ruta.a_lista()

    return {
        "distance": matriz[n][m],
        "path": ruta_final,
        "matrix_shape": [n, m],
        "path_length": len(ruta_final),
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
            "dtw_path_length": obtener_valor(dtw_full, "path_length", 0),
            "cosine_returns": similitud_coseno(ret_a, ret_b),
        },
    }


def media_movil_simple(valores, ventana):
    # Index-based sliding window: O(n) time, O(1) extra space.
    # Evita desplazamientos completos de la ventana en cada iteracion.
    resultado = ListaDinamica(len(valores) if len(valores) > 0 else 1)
    suma = 0.0
    i = 0
    while i < len(valores):
        valor = valores[i]
        suma += valor
        if i >= ventana:
            suma -= valores[i - ventana]
        if i >= ventana - 1:
            resultado.agregar(suma / ventana)
        else:
            resultado.agregar(None)
        i += 1
    return resultado.a_lista()


def max_drawdown(precios):
    if not precios:
        return 0.0
    pico = precios[0]
    peor = 0.0
    for precio in precios:
        if precio > pico:
            pico = precio
        if pico > 0:
            drawdown = (pico - precio) / pico
            if drawdown > peor:
                peor = drawdown
    return peor


def contar_patrones(retornos, k=3, umbral_rebote=0.03):
    positivos = 0
    rebotes = 0
    consolidaciones = 0
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

    for i in range(0, n - k + 1):
        estable = True
        for j in range(k):
            if abs(retornos[i + j]) > umbral_rebote:
                estable = False
                break
        if estable:
            consolidaciones += 1

    return {
        "positive_streak_k": positivos,
        "negative_then_strong_rebound": rebotes,
        "low_volatility_consolidation": consolidaciones,
        "k": k,
        "rebound_threshold": umbral_rebote,
    }


def estadisticas_riesgo(dataset):
    resultados = ListaDinamica()
    for simbolo in extraer_simbolos(dataset):
        precios_tmp = ListaDinamica()
        for item in serie_campo(dataset, simbolo, "Close"):
            precios_tmp.agregar(item["valor"])
        precios = precios_tmp.a_lista()
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
        drawdown = max_drawdown(precios)
        resultados.agregar(
            {
                "symbol": simbolo,
                "mean_daily_return": media_diaria,
                "std_daily_return": desviacion_diaria,
                "annual_volatility": volatilidad_anual,
                "annual_return": annual_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": drawdown,
                "risk_category": categoria,
                "observations": len(retornos),
            }
        )
    resultados = resultados.a_lista()
    n = len(resultados)
    for i in range(n - 1):
        max_idx = i
        for j in range(i + 1, n):
            # Orden descendente por volatilidad
            if resultados[j]["annual_volatility"] > resultados[max_idx]["annual_volatility"]:
                max_idx = j
        if max_idx != i:
            resultados[i], resultados[max_idx] = resultados[max_idx], resultados[i]
    return resultados


def matriz_correlacion(dataset):
    simbolos = extraer_simbolos(dataset)
    retornos_por_simbolo = TablaHashSimple()
    min_len = None
    for simbolo in simbolos:
        precios_tmp = ListaDinamica()
        for item in serie_campo(dataset, simbolo, "Close"):
            precios_tmp.agregar(item["valor"])
        precios = precios_tmp.a_lista()
        retornos = retornos_desde_precios(precios)
        retornos_por_simbolo.poner(simbolo, retornos)
        min_len = len(retornos) if min_len is None else menor_de_dos(min_len, len(retornos))

    if min_len is None:
        min_len = 0

    matriz = ListaDinamica()
    for simbolo_i in simbolos:
        fila = ListaDinamica()
        for simbolo_j in simbolos:
            retornos_i = retornos_por_simbolo.obtener(simbolo_i, [])
            retornos_j = retornos_por_simbolo.obtener(simbolo_j, [])
            fila.agregar(
                correlacion_pearson(
                    ultimos_elementos(retornos_i, min_len) if min_len else [],
                    ultimos_elementos(retornos_j, min_len) if min_len else [],
                )
            )
        matriz.agregar(fila.a_lista())
    return {"symbols": simbolos, "matrix": matriz.a_lista()}


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
        "formal": "P1(i,k): for all j in [i, i+k-1], r_j > 0",
        "description": "k days in a row with positive return. Detects sustained upward momentum.",
        "complexity": "O(n*k)",
    },
    "negative_rebound": {
        "name": "Rebound after drop (P2)",
        "formal": "P2(i,k,theta): (for all j in [i, i+k-1], r_j < 0) and r_(i+k) >= theta",
        "description": "k negative days followed by a rebound >= theta. Models post-correction recovery.",
        "complexity": "O(n*k)",
    },
    "low_volatility_consolidation": {
        "name": "Low-volatility consolidation (P3)",
        "formal": "P3(i,k,theta): for all j in [i, i+k-1], |r_j| <= theta",
        "description": "k days with small movements. Detects sideways or consolidation periods.",
        "complexity": "O(n*k)",
    },
}
