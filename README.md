# Dashboard bursatil y analisis de series

Aplicacion web Flask para descargar, limpiar y analizar series diarias OHLCV de
acciones colombianas, ADRs colombianos y ETFs globales. El proyecto evita
`yfinance`, `pandas_datareader`, `pandas`, `numpy` y funciones empaquetadas de
similitud; los algoritmos principales estan implementados con listas y bucles.

El dataset maestro actual contiene 28 activos y 1308 filas, con rango historico
de `2021-04-22` a `2026-04-30`.

El portafolio se divide en 14 activos colombianos y 14 activos globales para
comparar el movimiento local frente a referencias internacionales.

En la interfaz, los selectores y la lista rapida de activos ya aparecen
agrupados por ese criterio.

## Modulos

- `src/`: codigo fuente principal del backend.
- `static/modules/`: paginas web de cada modulo funcional.
- `modules/`: documentos de soporte por modulo.
- `static/modules/etl/`: pagina web del modulo ETL.
- `static/modules/similarity/`: pagina web del modulo de similitud.
- `static/modules/patterns/`: pagina web del modulo de patrones y riesgo.
- `static/modules/visualization/`: pagina web del modulo de visualizacion y PDF.
- `static/modules/docs/`: pagina web del modulo de documentacion.
- `src/extraccion_datos.py`: ETL reproducible desde Yahoo Finance mediante HTTP.
- `src/analisis_financiero.py`: retornos, Euclidiana, Pearson, DTW, coseno,
  ventanas deslizantes, volatilidad y matriz de correlacion.
- `src/visualizacion.py`: heatmap, velas, medias moviles y ranking de riesgo.
- `src/reporte_pdf.py`: reporte tecnico descargable.
- `api.py`: punto de entrada que levanta la app Flask.
- `static/`: landing page, CSS, JavaScript y paginas modulares.
- `docs/DOCUMENTACION_TECNICA.md`: arquitectura, formulas, complejidades y
  cobertura real del sistema.
- `data/processed/`: dataset maestro JSON y reporte ETL generados.
- `reports/`: PDFs generados por la aplicacion.

## Ejecucion

```powershell
cd "d:\Repositorios_UQ\proyecto-algoritmos\analizador"
py -3 -m pip install -r requirements.txt
py -3 api.py
```

Abrir:

```text
http://127.0.0.1:8000/
```

## Reconstruir el dataset

Desde consola:

```powershell
py -3 src/extraccion_datos.py
```

Desde el dashboard, usar el boton `Reconstruir ETL`.

El archivo generado por defecto es `data/processed/dataset_maestro.json`, aunque
el repositorio tambien mantiene `data/processed/dataset_maestro.csv` como
referencia del dataset maestro. Cada activo tiene columnas:

```text
<SIMBOLO>_Open
<SIMBOLO>_High
<SIMBOLO>_Low
<SIMBOLO>_Close
<SIMBOLO>_Volume
<SIMBOLO>_Missing
```

La app acepta ambos formatos. Si existe JSON se usa primero; si no, se carga el
CSV maestro legado.

## Rutas web

- `/`: redirige al modulo ETL.
- `/ui/etl`: ETL y dataset.
- `/ui/similarity`: similitud entre activos.
- `/ui/patterns`: patrones y riesgo.
- `/ui/visualization`: visualizacion y PDF.
- `/ui/docs`: documentacion y despliegue.

## Endpoints principales

- `GET /dataset/overview`: resumen del dataset maestro.
- `POST /dataset/build`: ejecuta ETL completo.
- `POST /similarity`: compara dos activos con Euclidiana, Pearson, DTW y coseno.
- `GET /risk`: volatilidad anualizada y categoria de riesgo.
- `GET /patterns`: frecuencia de patrones con ventana deslizante.
- `GET /correlation`: matriz de correlacion manual.
- `GET /plot/correlation.png`: heatmap.
- `GET /plot/candlestick.png?symbol=VOO`: velas con SMA.
- `GET /plot/returns.png?symbol_a=VOO&symbol_b=SPY`: comparacion de retornos.
- `GET /plot/series.png?symbol_a=VOO&symbol_b=SPY`: comparacion de precios.
- `GET /plot/risk.png`: barras de volatilidad.
- `GET /report.pdf?symbol_a=VOO&symbol_b=ECOPETROL.CL`: reporte PDF.

## Restricciones cumplidas

- Descarga por HTTP directo con `requests`.
- Parsing JSON y escritura manual del dataset maestro.
- Algoritmos de similitud implementados desde cero.
- Medias moviles, desviacion estandar y correlacion calculadas manualmente.
- Visualizacion con `matplotlib`.
- Reporte PDF reproducible.

## Despliegue en Render

Para que los archivos generados persistan entre reinicios, configura una ruta escribible en la variable de entorno `ANALIZADOR_DATA_DIR` y, si quieres separar reportes, `ANALIZADOR_REPORTS_DIR`.

Ejemplo para Render:

```text
ANALIZADOR_DATA_DIR=/opt/render/project/src/storage/data
ANALIZADOR_REPORTS_DIR=/opt/render/project/src/storage/reports
```

Si no configuras esas variables, la app intentara escribir en `data/processed/` y `reports/` en local, y si el entorno no permite escritura usara directorios temporales para no romper la ejecucion.
