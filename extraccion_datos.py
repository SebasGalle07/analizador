import csv
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent

# Yahoo Finance symbols queried through explicit HTTP requests. The first block
# contains Colombian/BVC names available in Yahoo and the second block contains
# global ETFs. If a source temporarily rejects one symbol, the ETL continues with
# the remaining assets and reports the failure.
DEFAULT_SYMBOLS = [
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

PRICE_FIELDS = ("Open", "High", "Low", "Close")
ALL_FIELDS = ("Open", "High", "Low", "Close", "Volume")


def normalizar_simbolo(simbolo):
    return simbolo.strip().upper()


def nombre_columna(simbolo, campo):
    return f"{normalizar_simbolo(simbolo)}_{campo}"


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
        return max(number, 0)
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
    chart = payload.get("chart", {})
    resultados = chart.get("result") or []
    if not resultados:
        raise RuntimeError(f"Yahoo no retorno datos para {simbolo}: {chart.get('error')}")

    resultado = resultados[0]
    tiempos = resultado.get("timestamp") or []
    quote = (resultado.get("indicators", {}).get("quote") or [{}])[0]
    aperturas = quote.get("open") or []
    maximos = quote.get("high") or []
    minimos = quote.get("low") or []
    cierres = quote.get("close") or []
    volumenes = quote.get("volume") or []

    total = min(
        len(tiempos),
        len(aperturas),
        len(maximos),
        len(minimos),
        len(cierres),
        len(volumenes),
    )
    registros = []
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
            high_value = max(open_value, close_value)
        if low_value is None:
            low_value = min(open_value, close_value)
        if high_value < low_value:
            high_value, low_value = low_value, high_value

        fecha = datetime.fromtimestamp(tiempos[i]).strftime("%Y-%m-%d")
        registros.append(
            {
                "Fecha": fecha,
                "Open": open_value,
                "High": high_value,
                "Low": low_value,
                "Close": close_value,
                "Volume": _safe_volume(volumenes[i]),
            }
        )

    return registros


def limpiar_registros(datos):
    """Remove duplicates and inconsistent OHLC rows.

    Invalid rows are discarded because negative or zero prices would corrupt
    returns, volatility and similarity metrics. Duplicate dates keep the last
    observed record from the source.
    """
    unicos = {}
    descartados = 0
    for registro in datos:
        precios = [registro.get(campo) for campo in PRICE_FIELDS]
        if any(_safe_float(valor) is None for valor in precios):
            descartados += 1
            continue
        if registro["High"] < max(registro["Open"], registro["Close"], registro["Low"]):
            descartados += 1
            continue
        if registro["Low"] > min(registro["Open"], registro["Close"], registro["High"]):
            descartados += 1
            continue
        unicos[registro["Fecha"]] = registro

    limpios = sorted(unicos.values(), key=lambda item: item["Fecha"])
    return limpios, {"crudos": len(datos), "limpios": len(limpios), "descartados": descartados}


def unificar_portafolio(datos_por_activo):
    """Align all assets on the union calendar and forward-fill missing prices."""
    fechas = set()
    indices = {}
    for simbolo, datos in datos_por_activo.items():
        indice = {registro["Fecha"]: registro for registro in datos}
        indices[simbolo] = indice
        fechas.update(indice.keys())

    calendario = sorted(fechas)
    ultimos = {simbolo: {campo: None for campo in PRICE_FIELDS} for simbolo in datos_por_activo}
    dataset = []
    missing_counts = {simbolo: 0 for simbolo in datos_por_activo}

    for fecha in calendario:
        fila = {"Fecha": fecha}
        for simbolo in datos_por_activo:
            registro = indices[simbolo].get(fecha)
            missing = registro is None

            if registro:
                for campo in PRICE_FIELDS:
                    ultimos[simbolo][campo] = registro[campo]
                    fila[nombre_columna(simbolo, campo)] = _round_or_blank(registro[campo])
                fila[nombre_columna(simbolo, "Volume")] = registro["Volume"]
            else:
                missing_counts[simbolo] += 1
                for campo in PRICE_FIELDS:
                    fila[nombre_columna(simbolo, campo)] = _round_or_blank(ultimos[simbolo][campo])
                fila[nombre_columna(simbolo, "Volume")] = 0

            fila[nombre_columna(simbolo, "Missing")] = "1" if missing else "0"
        dataset.append(fila)

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
        "faltantes_por_activo": missing_counts,
    }
    return dataset, limpieza


def guardar_reporte_json(reporte, nombre_base="dataset_maestro"):
    """Persiste el reporte del ETL junto al CSV para que el dashboard lo muestre."""
    ruta = BASE_DIR / f"{nombre_base}_report.json"
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(reporte, archivo, ensure_ascii=False, indent=2, default=str)
    return ruta


def guardar_en_csv(dataset, nombre_archivo="dataset_maestro.csv"):
    if not dataset:
        return None
    ruta = Path(nombre_archivo)
    if not ruta.is_absolute():
        ruta = BASE_DIR / ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)

    columnas = list(dataset[0].keys())
    with ruta.open(mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(dataset)
    return ruta


def construir_dataset_maestro(
    simbolos=None,
    years=5,
    interval="1d",
    timeout=15,
    pausa_segundos=0.35,
    guardar_csv=True,
    nombre_archivo="dataset_maestro.csv",
):
    simbolos = [normalizar_simbolo(s) for s in (simbolos or DEFAULT_SYMBOLS)]
    datos_memoria = {}
    reporte = {"activos": {}, "errores": {}, "limpieza": {}}

    for simbolo in simbolos:
        try:
            datos = descargar_yahoo_finance(simbolo, years=years, interval=interval, timeout=timeout)
            limpios, resumen = limpiar_registros(datos)
            if limpios:
                datos_memoria[simbolo] = limpios
                reporte["activos"][simbolo] = resumen
            else:
                reporte["errores"][simbolo] = "Sin registros validos despues de limpieza"
        except Exception as error:
            reporte["errores"][simbolo] = str(error)

        if pausa_segundos > 0:
            time.sleep(pausa_segundos)

    if not datos_memoria:
        return [], reporte

    dataset, limpieza = unificar_portafolio(datos_memoria)
    reporte["limpieza"] = limpieza
    reporte["simbolos_descargados"] = list(datos_memoria.keys())
    reporte["filas"] = len(dataset)

    if guardar_csv:
        ruta = guardar_en_csv(dataset, nombre_archivo=nombre_archivo)
        reporte["archivo"] = str(ruta)
        nombre_base = Path(nombre_archivo).stem
        guardar_reporte_json(reporte, nombre_base)

    return dataset, reporte


if __name__ == "__main__":
    dataset, reporte = construir_dataset_maestro()
    print(f"Filas generadas: {len(dataset)}")
    print(f"Activos descargados: {len(reporte.get('simbolos_descargados', []))}")
    if reporte.get("errores"):
        print("Errores:")
        for simbolo, error in reporte["errores"].items():
            print(f"  {simbolo}: {error}")
