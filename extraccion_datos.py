import csv
import time
from datetime import datetime, timedelta

import requests

DEFAULT_SYMBOLS = [
    "VOO",
    "EC",
    "AAPL",
    "MSFT",
    "TSLA",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "NFLX",
    "JPM",
    "V",
    "WMT",
    "JNJ",
    "BAC",
    "PG",
    "XOM",
    "DIS",
    "HD",
    "MA",
]


def _safe_round(value, digits=4):
    if value is None:
        return None
    return round(value, digits)


def descargar_yahoo_finance(simbolo, years=5, interval="1d", timeout=10):
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=years * 365)

    periodo_1 = int(fecha_inicio.timestamp())
    periodo_2 = int(fecha_fin.timestamp())

    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{simbolo}"
    parametros = {
        "period1": periodo_1,
        "period2": periodo_2,
        "interval": interval,
    }
    cabeceras = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        respuesta = requests.get(
            url,
            params=parametros,
            headers=cabeceras,
            timeout=timeout,
        )
        respuesta.raise_for_status()
        datos_json = respuesta.json()

        resultados = datos_json.get("chart", {}).get("result") or []
        if not resultados:
            error = datos_json.get("chart", {}).get("error")
            raise ValueError(f"Respuesta sin datos para {simbolo}: {error}")

        resultado = resultados[0]
        tiempos = resultado.get("timestamp") or []
        cotizaciones = (resultado.get("indicators", {}).get("quote") or [{}])[0]

        aperturas = cotizaciones.get("open") or []
        altos = cotizaciones.get("high") or []
        bajos = cotizaciones.get("low") or []
        cierres = cotizaciones.get("close") or []
        volumenes = cotizaciones.get("volume") or []

        total_registros = min(
            len(tiempos),
            len(aperturas),
            len(altos),
            len(bajos),
            len(cierres),
            len(volumenes),
        )

        datos_crudos = []
        for i in range(total_registros):
            if cierres[i] is None:
                continue

            fecha_legible = datetime.fromtimestamp(tiempos[i]).strftime("%Y-%m-%d")
            registro = {
                "Fecha": fecha_legible,
                "Open": _safe_round(aperturas[i]),
                "High": _safe_round(altos[i]),
                "Low": _safe_round(bajos[i]),
                "Close": _safe_round(cierres[i]),
                "Volume": volumenes[i] if volumenes[i] is not None else 0,
            }
            datos_crudos.append(registro)

        return datos_crudos
    except Exception as error:
        print(f"Error extrayendo {simbolo}: {error}")
        return []


def limpiar_fechas_duplicadas(datos):
    registros_unicos = {}
    for registro in datos:
        registros_unicos[registro["Fecha"]] = registro

    datos_limpios = sorted(registros_unicos.values(), key=lambda item: item["Fecha"])
    print(
        f"   -> Limpieza: De {len(datos)} registros crudos, "
        f"quedaron {len(datos_limpios)} unicos."
    )
    return datos_limpios


def unificar_portafolio(datos_por_activo):
    print("\nIniciando unificacion y correccion de valores faltantes...")

    fechas_todas = set()
    indices_por_activo = {}

    for simbolo, datos in datos_por_activo.items():
        indice_fechas = {registro["Fecha"]: registro for registro in datos}
        indices_por_activo[simbolo] = indice_fechas
        fechas_todas.update(indice_fechas.keys())

    calendario_ordenado = sorted(fechas_todas)
    dataset_unificado = []

    ultimo_precio_conocido = {simbolo: None for simbolo in datos_por_activo}

    for fecha in calendario_ordenado:
        fila_maestra = {"Fecha": fecha}

        for simbolo, indice_fechas in indices_por_activo.items():
            registro = indice_fechas.get(fecha)

            if registro:
                precio = registro["Close"]
                volumen = registro["Volume"]
                fila_maestra[f"{simbolo}_Close"] = precio
                fila_maestra[f"{simbolo}_Volume"] = volumen
                ultimo_precio_conocido[simbolo] = precio
            else:
                fila_maestra[f"{simbolo}_Close"] = ultimo_precio_conocido[simbolo]
                fila_maestra[f"{simbolo}_Volume"] = 0

        dataset_unificado.append(fila_maestra)

    return dataset_unificado


def guardar_en_csv(dataset, nombre_archivo="dataset_maestro.csv"):
    if not dataset:
        return

    columnas = list(dataset[0].keys())

    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(dataset)

    print(f"\n[OK] Dataset guardado exitosamente en: {nombre_archivo}")


def construir_dataset_maestro(
    simbolos=None,
    years=5,
    interval="1d",
    timeout=10,
    pausa_segundos=2,
    guardar_csv=True,
    nombre_archivo="dataset_maestro.csv",
):
    simbolos = simbolos or DEFAULT_SYMBOLS
    datos_memoria = {}

    print("=== INICIANDO PROCESO ETL ===")

    for simbolo in simbolos:
        print(f"Descargando: {simbolo}...")
        datos = descargar_yahoo_finance(
            simbolo=simbolo,
            years=years,
            interval=interval,
            timeout=timeout,
        )

        if datos:
            datos_limpios = limpiar_fechas_duplicadas(datos)
            datos_memoria[simbolo] = datos_limpios

        if pausa_segundos > 0:
            time.sleep(pausa_segundos)

    if not datos_memoria:
        return []

    dataset_final = unificar_portafolio(datos_memoria)

    if guardar_csv:
        guardar_en_csv(dataset_final, nombre_archivo=nombre_archivo)

    return dataset_final


if __name__ == "__main__":
    construir_dataset_maestro()
