# Dashboard bursatil y analisis de series

Aplicacion web Flask para descargar, limpiar y analizar series diarias OHLCV de
acciones colombianas, ADRs colombianos y ETFs globales. El proyecto evita
`yfinance`, `pandas_datareader`, `pandas`, `numpy` y funciones empaquetadas de
similitud; los algoritmos principales estan implementados con listas y bucles.

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
- `docs/DOCUMENTACION_TECNICA.md`: arquitectura, formulas y complejidades.
- `data/processed/`: dataset maestro y reporte ETL generados.
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

El archivo generado es `data/processed/dataset_maestro.csv`. Cada activo tiene columnas:

```text
<SIMBOLO>_Open
<SIMBOLO>_High
<SIMBOLO>_Low
<SIMBOLO>_Close
<SIMBOLO>_Volume
<SIMBOLO>_Missing
```

## Rutas web

- `/`: redirige al modulo ETL.
- `/ui/etl`: ETL y dataset.
- `/ui/similarity`: similitud entre activos.
- `/ui/patterns`: patrones y riesgo.
- `/ui/visualization`: visualizacion y PDF.
- `/ui/docs`: documentacion y despliegue.

## Endpoints principales

- `GET /dataset/overview`: resumen del CSV.
- `POST /dataset/build`: ejecuta ETL completo.
- `POST /similarity`: compara dos activos con Euclidiana, Pearson, DTW y coseno.
- `GET /risk`: volatilidad anualizada y categoria de riesgo.
- `GET /patterns`: frecuencia de patrones con ventana deslizante.
- `GET /correlation`: matriz de correlacion manual.
- `GET /plot/correlation.png`: heatmap.
- `GET /plot/candlestick.png?symbol=VOO`: velas con SMA.
- `GET /report.pdf?symbol_a=VOO&symbol_b=ECOPETROL.CL`: reporte PDF.

## Restricciones cumplidas

- Descarga por HTTP directo con `requests`.
- Parsing JSON y escritura CSV manual.
- Algoritmos de similitud implementados desde cero.
- Medias moviles, desviacion estandar y correlacion calculadas manualmente.
- Visualizacion con `matplotlib`.
- Reporte PDF reproducible.
