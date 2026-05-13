import csv
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

from src.estructuras_datos import (
    ConjuntoManual,
    ListaDinamica,
    TablaHashSimple,
    asegurar_lista_en_diccionario,
    claves_diccionario,
    concatenar_iterables,
    mayor_de_dos,
    mayor_de_tres,
    menor_de_dos,
    menor_de_tres,
    menor_de_varios,
    obtener_valor,
    ordenar_por_seleccion,
    pares_diccionario,
)
from src.paths import PROCESSED_DIR, get_runtime_processed_dir


BASE_DIR = get_runtime_processed_dir()
LOGGER = logging.getLogger(__name__)

# Yahoo Finance symbols queried through explicit HTTP requests. The portfolio is
# intentionally balanced: half Colombian assets and half global reference assets.
# If a source temporarily rejects one symbol, the ETL continues with the
# remaining assets and reports the failure.
COLOMBIA_SYMBOLS = [
    "ECOPETROL.CL",
    "ISA.CL",
    "GEB.CL",
    "GRUPOARGOS.CL",
    "CEMARGOS.CL",
    "NUTRESA.CL",
    "BVC.CL",
    "EXITO.CL",
    "BOGOTA.CL",
    "GRUPOSURA.CL",
    "EC",
    "CIB",
    "AVAL",
    "TGLS",
]

GLOBAL_SYMBOLS = [
    "VOO",
    "SPY",
    "QQQ",
    "IWM",
    "EFA",
    "EEM",
    "GLD",
    "TLT",
    "BND",
    "VNQ",
    "XLE",
    "XLK",
    "XLF",
    "DIA",
]

DEFAULT_SYMBOLS = concatenar_iterables(COLOMBIA_SYMBOLS, GLOBAL_SYMBOLS)

SYMBOL_NAMES = {
    "ECOPETROL.CL": "Ecopetrol S.A.",
    "ISA.CL": "Interconexion Electrica S.A. E.S.P.",
    "GEB.CL": "Grupo Energia Bogota S.A. E.S.P.",
    "GRUPOARGOS.CL": "Grupo Argos S.A.",
    "CEMARGOS.CL": "Cementos Argos S.A.",
    "NUTRESA.CL": "Grupo Nutresa S.A.",
    "BVC.CL": "Bolsa de Valores de Colombia S.A.",
    "EXITO.CL": "Grupo Exito S.A.",
    "BOGOTA.CL": "Banco de Bogota S.A.",
    "GRUPOSURA.CL": "Grupo Sura S.A.",
    "EC": "Ecopetrol ADR",
    "CIB": "Bancolombia ADR",
    "AVAL": "Grupo Aval ADR",
    "TGLS": "Tecnoglass Inc.",
    "VOO": "Vanguard S&P 500 ETF",
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust",
    "IWM": "iShares Russell 2000 ETF",
    "EFA": "iShares MSCI EAFE ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "GLD": "SPDR Gold Shares",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "BND": "Vanguard Total Bond Market ETF",
    "VNQ": "Vanguard Real Estate ETF",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLK": "Technology Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "DIA": "SPDR Dow Jones Industrial Average ETF Trust",
}

PRICE_FIELDS = ("Open", "High", "Low", "Close")
ALL_FIELDS = ("Open", "High", "Low", "Close", "Volume")


def normalizar_simbolo(simbolo):
    return simbolo.strip().upper()


def nombre_columna(simbolo, campo):
    return f"{normalizar_simbolo(simbolo)}_{campo}"


def nombre_activo(simbolo):
    simbolo = normalizar_simbolo(simbolo)
    return obtener_valor(SYMBOL_NAMES, simbolo, simbolo)


def _safe_float(value):
    try:
        if value is None:
            return None
        number = float(value)
        if number != number or number <= 0:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _safe_volume(value):
    try:
        if value is None:
            return 0
        number = int(float(value))
        return mayor_de_dos(number, 0)
    except (TypeError, ValueError):
        return 0


def _round_or_blank(value, digits=6):
    if value is None:
        return ""
    return round(value, digits)


def descargar_yahoo_finance(simbolo, years=5, interval="1d", timeout=15, max_reintentos=3):
    """Download daily OHLCV bars from Yahoo Finance using direct HTTP.

    No yfinance or pandas_datareader are used. The function manually builds the
    query, validates the response shape and parses the JSON arrays.
    Retries up to max_reintentos times with exponential backoff on 429 or network errors.
    """
    simbolo = normalizar_simbolo(simbolo)
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=years * 365 + 10)

    periodo_1 = int(fecha_inicio.timestamp())
    periodo_2 = int(fecha_fin.timestamp())
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{simbolo}"
    parametros = {"period1": periodo_1, "period2": periodo_2, "interval": interval}
    cabeceras = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/122 Safari/537.36"
        )
    }

    respuesta = None
    for intento in range(max_reintentos):
        try:
            r = requests.get(url, params=parametros, headers=cabeceras, timeout=timeout)
            if r.status_code == 429:
                time.sleep(2 ** intento)
                continue
            respuesta = r
            break
        except requests.RequestException as exc:
            if intento == max_reintentos - 1:
                raise RuntimeError(f"Error de red al descargar {simbolo}: {exc}")
            time.sleep(2 ** intento)

    if respuesta is None:
        raise RuntimeError(f"Maximo de reintentos ({max_reintentos}) alcanzado para {simbolo}")
    if respuesta.status_code != 200:
        raise RuntimeError(f"HTTP {respuesta.status_code} al descargar {simbolo}")

    payload = respuesta.json()
    chart = obtener_valor(payload, "chart", {})
    resultados = obtener_valor(chart, "result") or []
    if not resultados:
        raise RuntimeError(f"Yahoo no retorno datos para {simbolo}: {obtener_valor(chart, 'error')}")

    resultado = resultados[0]
    tiempos = obtener_valor(resultado, "timestamp") or []
    indicadores = obtener_valor(resultado, "indicators", {})
    quotes = obtener_valor(indicadores, "quote") or [{}]
    quote = quotes[0]
    aperturas = obtener_valor(quote, "open") or []
    maximos = obtener_valor(quote, "high") or []
    minimos = obtener_valor(quote, "low") or []
    cierres = obtener_valor(quote, "close") or []
    volumenes = obtener_valor(quote, "volume") or []

    total = menor_de_varios(
        [
            len(tiempos),
            len(aperturas),
            len(maximos),
            len(minimos),
            len(cierres),
            len(volumenes),
        ]
    )
    registros = ListaDinamica(total if total > 0 else 1)
    for i in range(total):
        open_value = _safe_float(aperturas[i])
        high_value = _safe_float(maximos[i])
        low_value = _safe_float(minimos[i])
        close_value = _safe_float(cierres[i])

        if close_value is None:
            continue
        if open_value is None:
            open_value = close_value
        if high_value is None:
            high_value = mayor_de_dos(open_value, close_value)
        if low_value is None:
            low_value = menor_de_dos(open_value, close_value)
        if high_value < low_value:
            high_value, low_value = low_value, high_value

        fecha = datetime.fromtimestamp(tiempos[i]).strftime("%Y-%m-%d")
        registros.agregar(
            {
                "Fecha": fecha,
                "Open": open_value,
                "High": high_value,
                "Low": low_value,
                "Close": close_value,
                "Volume": _safe_volume(volumenes[i]),
            }
        )

    return registros.a_lista()


def limpiar_registros(datos):
    """Remove duplicates and inconsistent OHLC rows.

    Invalid rows are discarded because negative or zero prices would corrupt
    returns, volatility and similarity metrics. Duplicate dates keep the last
    observed record from the source.
    """
    unicos = TablaHashSimple()
    descartados = 0
    for registro in datos:
        precios_validos = True
        for campo in PRICE_FIELDS:
            if _safe_float(obtener_valor(registro, campo)) is None:
                precios_validos = False
                break
        if not precios_validos:
            descartados += 1
            continue
        if registro["High"] < mayor_de_tres(registro["Open"], registro["Close"], registro["Low"]):
            descartados += 1
            continue
        if registro["Low"] > menor_de_tres(registro["Open"], registro["Close"], registro["High"]):
            descartados += 1
            continue
        unicos.poner(registro["Fecha"], registro)

    limpios = ordenar_por_seleccion(unicos.valores(), lambda item_a, item_b: item_a["Fecha"] < item_b["Fecha"])
    return limpios, {"crudos": len(datos), "limpios": len(limpios), "descartados": descartados}


def unificar_portafolio(datos_por_activo):
    """Align all assets on the union calendar and forward-fill missing prices."""
    fechas = ConjuntoManual()
    indices = TablaHashSimple()
    pares_activos = datos_por_activo.pares() if isinstance(datos_por_activo, TablaHashSimple) else pares_diccionario(datos_por_activo)
    for simbolo, datos in pares_activos:
        indice = TablaHashSimple(len(datos) * 2 if len(datos) > 0 else 16)
        for registro in datos:
            indice.poner(registro["Fecha"], registro)
            fechas.agregar(registro["Fecha"])
        indices.poner(simbolo, indice)

    calendario = ordenar_por_seleccion(fechas.a_lista(), lambda fecha_a, fecha_b: fecha_a < fecha_b)
    ultimos = TablaHashSimple()
    missing_counts = TablaHashSimple()
    for simbolo, _ in pares_activos:
        ultimos_campos = {}
        for campo in PRICE_FIELDS:
            ultimos_campos[campo] = None
        ultimos.poner(simbolo, ultimos_campos)
        missing_counts.poner(simbolo, 0)
    dataset = ListaDinamica(len(calendario) if len(calendario) > 0 else 1)

    for fecha in calendario:
        fila = {"Fecha": fecha}
        for simbolo, _ in pares_activos:
            indice = indices.obtener(simbolo)
            registro = indice.obtener(fecha)
            missing = registro is None
            ultimos_campos = ultimos.obtener(simbolo)

            if registro:
                for campo in PRICE_FIELDS:
                    ultimos_campos[campo] = registro[campo]
                    fila[nombre_columna(simbolo, campo)] = _round_or_blank(registro[campo])
                fila[nombre_columna(simbolo, "Volume")] = registro["Volume"]
            else:
                missing_counts.poner(simbolo, missing_counts.obtener(simbolo, 0) + 1)
                for campo in PRICE_FIELDS:
                    fila[nombre_columna(simbolo, campo)] = _round_or_blank(ultimos_campos[campo])
                fila[nombre_columna(simbolo, "Volume")] = 0

            fila[nombre_columna(simbolo, "Missing")] = "1" if missing else "0"
        dataset.agregar(fila)

    limpieza = {
        "metodo_faltantes": (
            "Forward fill para precios en dias no operados y volumen 0; "
            "las columnas *_Missing conservan la trazabilidad del dato imputado."
        ),
        "impacto": (
            "El forward fill evita perder fechas al comparar calendarios distintos, "
            "pero reduce artificialmente retornos en dias imputados. Por eso las "
            "metricas de retornos ignoran pares sin precio previo real cuando aplica."
        ),
        "faltantes_por_activo": missing_counts.a_diccionario(),
    }
    return dataset.a_lista(), limpieza


def guardar_reporte_json(reporte, nombre_base="dataset_maestro", directorio=None):
    """Persiste el reporte del ETL junto al dataset maestro para que el dashboard lo muestre."""
    base_dir = Path(directorio) if directorio else get_runtime_processed_dir()
    base_dir.mkdir(parents=True, exist_ok=True)
    ruta = base_dir / f"{nombre_base}_report.json"
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(reporte, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def _resolver_ruta_salida(nombre_archivo, extension_por_defecto=".json"):
    ruta = Path(nombre_archivo)
    if ruta.suffix.lower() not in {".json", ".csv"}:
        ruta = ruta.with_suffix(extension_por_defecto)
    if not ruta.is_absolute():
        ruta = get_runtime_processed_dir() / ruta.name if len(ruta.parts) == 1 else PROCESSED_DIR.parent.parent / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def guardar_en_json(dataset, nombre_archivo="dataset_maestro.json"):
    if not dataset:
        return None
    ruta = _resolver_ruta_salida(nombre_archivo, ".json")
    with ruta.open(mode="w", encoding="utf-8") as archivo:
        json.dump(dataset, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def validar_requerimientos_etl(reporte, dataset, min_activos=20, min_years=5, strict=False):
    advertencias = ListaDinamica()
    errores = ListaDinamica()

    activos_descargados = len(obtener_valor(reporte, "simbolos_descargados", []))
    if activos_descargados < min_activos:
        mensaje = (
            f"Solo se descargaron {activos_descargados} activos; "
            f"el requerimiento pide al menos {min_activos}."
        )
        if strict:
            errores.agregar(mensaje)
        else:
            advertencias.agregar(mensaje)

    fecha_min = None
    fecha_max = None
    if dataset:
        fechas_tmp = ListaDinamica()
        for fila in dataset:
            fecha = obtener_valor(fila, "Fecha")
            if fecha:
                fechas_tmp.agregar(fecha)
        fechas = fechas_tmp.a_lista()
        if fechas:
            fecha_min = fechas[0]
            fecha_max = fechas[0]
            i = 1
            while i < len(fechas):
                if fechas[i] < fecha_min:
                    fecha_min = fechas[i]
                if fechas[i] > fecha_max:
                    fecha_max = fechas[i]
                i += 1
            try:
                inicio = datetime.strptime(fecha_min, "%Y-%m-%d")
                fin = datetime.strptime(fecha_max, "%Y-%m-%d")
                if (fin - inicio).days < (min_years * 365):
                    mensaje = (
                        f"El rango final cubre {fecha_min} a {fecha_max}, "
                        f"menos de {min_years} anos calendario completos."
                    )
                    if strict:
                        errores.agregar(mensaje)
                    else:
                        advertencias.agregar(mensaje)
            except ValueError:
                advertencias.agregar("No se pudo validar el rango final de fechas.")

    advertencias_lista = advertencias.a_lista()
    errores_lista = errores.a_lista()
    reporte["validacion"] = {
        "min_activos": min_activos,
        "min_years": min_years,
        "activos_descargados": activos_descargados,
        "rango_final": {"inicio": fecha_min, "fin": fecha_max},
        "cumple": len(errores_lista) == 0,
    }
    if advertencias_lista:
        lista_advertencias = asegurar_lista_en_diccionario(reporte, "advertencias")
        nueva_lista = ListaDinamica(len(lista_advertencias) + len(advertencias_lista))
        for mensaje_existente in lista_advertencias:
            nueva_lista.agregar(mensaje_existente)
        for mensaje in advertencias_lista:
            nueva_lista.agregar(mensaje)
        reporte["advertencias"] = nueva_lista.a_lista()
    if errores_lista:
        lista_errores = asegurar_lista_en_diccionario(reporte, "errores_validacion")
        nueva_lista = ListaDinamica(len(lista_errores) + len(errores_lista))
        for mensaje_existente in lista_errores:
            nueva_lista.agregar(mensaje_existente)
        for mensaje in errores_lista:
            nueva_lista.agregar(mensaje)
        reporte["errores_validacion"] = nueva_lista.a_lista()
    return advertencias_lista, errores_lista


def guardar_en_csv(dataset, nombre_archivo="dataset_maestro.csv"):
    if not dataset:
        return None
    ruta = _resolver_ruta_salida(nombre_archivo, ".csv")

    columnas = claves_diccionario(dataset[0])
    with ruta.open(mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(dataset)
    return ruta


def guardar_dataset(dataset, nombre_archivo="dataset_maestro.json"):
    ruta = Path(nombre_archivo)
    if ruta.suffix.lower() == ".csv":
        return guardar_en_csv(dataset, nombre_archivo=nombre_archivo)
    return guardar_en_json(dataset, nombre_archivo=nombre_archivo)


def construir_dataset_maestro(
    simbolos=None,
    years=5,
    interval="1d",
    timeout=15,
    pausa_segundos=0.35,
    guardar_csv=True,
    nombre_archivo="dataset_maestro.json",
    min_activos=20,
    min_years=5,
    strict_minimo=False,
):
    simbolos_normalizados = ListaDinamica()
    for s in (simbolos or DEFAULT_SYMBOLS):
        simbolos_normalizados.agregar(normalizar_simbolo(s))
    simbolos = simbolos_normalizados.a_lista()
    datos_memoria = TablaHashSimple()
    reporte = {
        "fuente": "Yahoo Finance (HTTP directo)",
        "years_solicitados": years,
        "intervalo": interval,
        "activos_solicitados": len(simbolos),
        "portafolio": {
            "colombia": len(COLOMBIA_SYMBOLS),
            "global": len(GLOBAL_SYMBOLS),
        },
        "activos": {},
        "errores": {},
        "limpieza": {},
        "advertencias": [],
    }

    LOGGER.info("ETL | inicio | solicitados=%s | anos=%s | intervalo=%s", len(simbolos), years, interval)

    total_simbolos = len(simbolos)
    index = 1
    for simbolo in simbolos:
        try:
            LOGGER.info("ETL | activo %s/%s | %s | descarga", index, total_simbolos, simbolo)
            datos = descargar_yahoo_finance(simbolo, years=years, interval=interval, timeout=timeout)
            limpios, resumen = limpiar_registros(datos)
            if limpios:
                datos_memoria.poner(simbolo, limpios)
                reporte["activos"][simbolo] = resumen
                LOGGER.info(
                    "ETL | activo %s/%s | %s | crudos=%s | limpios=%s | descartados=%s",
                    index,
                    total_simbolos,
                    simbolo,
                    resumen["crudos"],
                    resumen["limpios"],
                    resumen["descartados"],
                )
            else:
                reporte["errores"][simbolo] = "Sin registros validos despues de limpieza"
                LOGGER.warning("ETL | activo %s/%s | %s | sin registros validos", index, total_simbolos, simbolo)
        except Exception as error:
            reporte["errores"][simbolo] = str(error)
            LOGGER.warning("ETL | activo %s/%s | %s | error=%s", index, total_simbolos, simbolo, error)

        if pausa_segundos > 0:
            time.sleep(pausa_segundos)
        index += 1

    if datos_memoria.esta_vacia():
        LOGGER.error("ETL | error | no se obtuvieron activos validos")
        return [], reporte

    dataset, limpieza = unificar_portafolio(datos_memoria)
    reporte["limpieza"] = limpieza
    reporte["simbolos_descargados"] = datos_memoria.claves()
    reporte["filas"] = len(dataset)
    reporte["activos_descargados"] = len(reporte["simbolos_descargados"])
    if dataset:
        fechas_tmp = ListaDinamica()
        for fila in dataset:
            fecha = obtener_valor(fila, "Fecha")
            if fecha:
                fechas_tmp.agregar(fecha)
        fechas = fechas_tmp.a_lista()
        if fechas:
            fecha_min = fechas[0]
            fecha_max = fechas[0]
            i = 1
            while i < len(fechas):
                if fechas[i] < fecha_min:
                    fecha_min = fechas[i]
                if fechas[i] > fecha_max:
                    fecha_max = fechas[i]
                i += 1
            reporte["rango_final"] = {"inicio": fecha_min, "fin": fecha_max}

    advertencias, errores_validacion = validar_requerimientos_etl(
        reporte,
        dataset,
        min_activos=min_activos,
        min_years=min_years,
        strict=strict_minimo,
    )

    if guardar_csv:
        ruta = guardar_dataset(dataset, nombre_archivo=nombre_archivo)
        reporte["archivo"] = str(ruta)
        nombre_base = Path(nombre_archivo).stem
        guardar_reporte_json(reporte, nombre_base, directorio=ruta.parent if ruta else None)

    if errores_validacion:
        LOGGER.error("ETL | validacion | no cumple minimo | %s", " ; ".join(errores_validacion))
        if strict_minimo:
            raise RuntimeError("; ".join(errores_validacion))
    elif advertencias:
        LOGGER.warning("ETL | validacion | advertencias | %s", " ; ".join(advertencias))

    LOGGER.info(
        "ETL | fin | descargados=%s | filas=%s | rango=%s..%s",
        obtener_valor(reporte, "activos_descargados", 0),
        obtener_valor(reporte, "filas", 0),
        obtener_valor(obtener_valor(reporte, "rango_final") or {}, "inicio"),
        obtener_valor(obtener_valor(reporte, "rango_final") or {}, "fin"),
    )

    return dataset, reporte


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    dataset, reporte = construir_dataset_maestro()
    resumen = obtener_valor(reporte, "validacion", {})
    rango = obtener_valor(resumen, "rango_final") or {}
    LOGGER.info("ETL | resumen | filas=%s | activos=%s | rango=%s..%s", len(dataset), obtener_valor(reporte, "activos_descargados", 0), obtener_valor(rango, "inicio"), obtener_valor(rango, "fin"))
