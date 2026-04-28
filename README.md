# Dashboard bursatil y analisis de series

Aplicacion web Flask para descargar, limpiar y analizar series diarias OHLCV de
acciones colombianas, ADRs colombianos y ETFs globales. El proyecto evita
`yfinance`, `pandas_datareader`, `pandas`, `numpy` y funciones empaquetadas de
similitud; los algoritmos principales estan implementados con listas y bucles.

## Modulos

- `extraccion_datos.py`: ETL reproducible desde Yahoo Finance mediante HTTP.
- `analisis_financiero.py`: retornos, Euclidiana, Pearson, DTW, coseno,
  ventanas deslizantes, volatilidad y matriz de correlacion.
- `visualizacion.py`: heatmap, velas, medias moviles y ranking de riesgo.
- `reporte_pdf.py`: reporte tecnico descargable.
- `api.py`: aplicacion Flask y endpoints para la interfaz.
- `static/`: dashboard HTML, CSS y JavaScript.
- `DOCUMENTACION_TECNICA.md`: arquitectura, formulas y complejidades.

## Ejecucion

```powershell
cd "C:\Users\sebas\Desktop\Universidad\analisis\analizador"
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
py -3 extraccion_datos.py
```

Desde el dashboard, usar el boton `Reconstruir ETL`.

El archivo generado es `dataset_maestro.csv`. Cada activo tiene columnas:

```text
<SIMBOLO>_Open
<SIMBOLO>_High
<SIMBOLO>_Low
<SIMBOLO>_Close
<SIMBOLO>_Volume
<SIMBOLO>_Missing
```

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
