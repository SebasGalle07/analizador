# Modulo ETL

## Proposito

Construir y explicar el dataset maestro con datos historicos de activos financieros.

## Archivos relacionados

- `src/extraccion_datos.py`
- `api.py`
- `static/modules/etl/index.html`
- `data/processed/dataset_maestro.csv`
- `data/processed/dataset_maestro_report.json`

## Entradas

- Lista de simbolos.
- Años historicos a descargar.
- Intervalo diario.

## Salidas

- CSV maestro consolidado.
- Reporte JSON de limpieza.
- Vista previa de datos y estadisticas ETL.

## Evidencia para sustentar

- Descarga via HTTP directo.
- Limpieza de OHLC.
- Unificacion por calendario comun.
- Marcado de faltantes con `*_Missing`.
