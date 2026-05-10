# Documento tecnico

## Resumen ejecutivo

Este proyecto implementa un dashboard bursatil en Flask para descargar, limpiar, unificar y analizar series diarias OHLCV de activos financieros.

El flujo real del sistema es:

```text
Yahoo Finance por HTTP directo
  -> ETL y dataset maestro
  -> Analisis de similitud, patrones, riesgo y correlacion
  -> Visualizaciones PNG
  -> Reporte tecnico PDF
  -> Exposicion web con Flask
```

El dataset maestro actual en `data/processed/dataset_maestro.csv` contiene:

- 1308 filas.
- 28 activos.
- Rango temporal de `2021-04-22` a `2026-04-30`.

Ese estado cumple la cobertura minima esperada para el proyecto: mas de 20 activos y mas de 5 anos historicos.

## Arquitectura

La aplicacion se organiza en capas simples:

- `src/extraccion_datos.py`: ETL reproducible con peticiones HTTP directas a Yahoo Finance.
- `src/analisis_financiero.py`: metricas y algoritmos implementados desde cero.
- `src/visualizacion.py`: graficas con `matplotlib`.
- `src/reporte_pdf.py`: composicion del reporte PDF.
- `src/api.py`: API Flask y endpoints.
- `src/paths.py`: rutas configurables y directorios de ejecucion.

## ETL y construccion del dataset

La descarga se realiza contra:

```text
https://query2.finance.yahoo.com/v8/finance/chart/{SIMBOLO}
```

La rutina de ETL construye manualmente:

- `period1` y `period2` como timestamps Unix.
- `interval=1d`.
- cabeceras HTTP.
- reintentos ante errores de red o `429`.
- parsing de la respuesta JSON.
- escritura del dataset en JSON o CSV.

No se usa `yfinance`, `pandas_datareader`, `pandas`, `numpy` ni una funcion que encapsule la descarga de datos en una sola llamada.

### Portafolio utilizado

El portafolio por defecto incluye 28 activos y se divide de forma equilibrada:

- 14 activos colombianos o relacionados con el mercado local.
- 14 activos globales o indices de referencia internacional.

Esta division ayuda a comparar el comportamiento de activos locales frente a
instrumentos internacionales mas liquidos y utilizados como referencia.

En la interfaz, los selectores y la nube de activos muestran esos dos grupos
separados para que la comparacion visual sea inmediata.

Ejemplos de la mitad colombiana:

- `ECOPETROL.CL`, `ISA.CL`, `GEB.CL`, `GRUPOARGOS.CL`, `CEMARGOS.CL`, `NUTRESA.CL`,
  `BVC.CL`, `EXITO.CL`, `BOGOTA.CL`, `GRUPOSURA.CL`, `EC`, `CIB`, `AVAL`, `TGLS`.

Ejemplos de la mitad global:

- `VOO`, `SPY`, `QQQ`, `IWM`, `EFA`, `EEM`, `GLD`, `TLT`, `BND`, `VNQ`, `XLE`,
  `XLK`, `XLF`, `DIA`.

### Limpieza

La limpieza aplica estas reglas:

- Se eliminan registros duplicados por fecha.
- Se descartan filas con precios nulos, negativos o cero.
- Se descartan filas con inconsistencia de OHLC.
- Se unifican calendarios bursatiles con un calendario union.
- Cuando falta una fecha para un activo, los precios se completan con forward fill, el volumen queda en `0` y la columna `*_Missing` marca imputacion.

### Impacto de la imputacion

El forward fill evita perder fechas al comparar activos con calendarios distintos, pero puede suavizar retornos en dias no negociados. Por eso:

- la imputacion queda marcada en el dataset,
- los calculos de similitud y riesgo trabajan sobre series alineadas,
- el reporte tecnico explicita esta limitacion.

## Similitud de series

Los algoritmos estan implementados en `src/analisis_financiero.py` con listas, bucles y operaciones elementales.

### Distancia euclidiana

Formula:

```text
d(P,Q) = sqrt(sum((p_i - q_i)^2))
```

Uso:

- compara precios alineados o retornos diarios,
- mide separacion global entre dos vectores.

Complejidad:

- Tiempo: `O(n)`
- Espacio: `O(1)`

### Correlacion de Pearson

Formula:

```text
r_xy = sum((x_i - x_bar)(y_i - y_bar)) / sqrt(sum((x_i - x_bar)^2) sum((y_i - y_bar)^2))
```

Uso:

- se aplica a retornos diarios,
- mide relacion lineal entre dos activos.

Complejidad:

- Tiempo: `O(n)`
- Espacio: `O(1)`

### Dynamic Time Warping

Recurrencia:

```text
D(i,j) = |p_i - q_j| + min(D(i-1,j), D(i,j-1), D(i-1,j-1))
```

Uso:

- compara series con desfases temporales,
- admite alineaciones one-to-many y many-to-one.

En el codigo existe una variante con banda Sakoe-Chiba para reducir costo de calculo.

Complejidad:

- Sin banda: `O(n*m)`
- Con banda: aproximadamente `O(n*w)`

### Similitud coseno

Formula:

```text
cos(P,Q) = (P dot Q) / (||P|| ||Q||)
```

Uso:

- se aplica a retornos diarios,
- captura si dos series se mueven en la misma direccion.

Complejidad:

- Tiempo: `O(n)`
- Espacio: `O(1)`

## Patrones y volatilidad

El proyecto implementa deteccion de patrones con ventana deslizante:

- rachas de retornos positivos,
- secuencias negativas seguidas de rebote,
- periodos de baja volatilidad.

### Volatilidad

La volatilidad anualizada se calcula con:

```text
sigma_anual = sigma_diaria * sqrt(252)
```

Categorias usadas:

- Conservador: menor a 10%.
- Moderado: entre 10% y 20%.
- Agresivo: mayor a 20%.

### Ranking de riesgo

Los activos se ordenan por volatilidad anualizada de forma descendente. Ademas se calcula:

- retorno anual estimado,
- Sharpe simplificado,
- max drawdown.

## Visualizaciones

`src/visualizacion.py` genera:

- mapa de calor de correlacion Pearson,
- velas japonesas con SMA,
- comparacion de precios,
- comparacion de retornos,
- barras de volatilidad anualizada.

La libreria usada es `matplotlib`, que permite graficos estaticos reproducibles.

## Reporte PDF

`src/reporte_pdf.py` compone un PDF tecnico con:

- resumen del dataset,
- metricas de similitud,
- ranking de riesgo,
- grafico de precios,
- mapa de calor de correlacion,
- secciones de formulas y complejidad.

El endpoint principal es:

```text
GET /report.pdf?symbol_a=VOO&symbol_b=ECOPETROL.CL
```

## API Flask

Rutas principales:

- `/ui/etl`
- `/ui/similarity`
- `/ui/patterns`
- `/ui/visualization`
- `/ui/docs`

Endpoints principales:

- `GET /dataset/overview`
- `POST /dataset/build`
- `POST /similarity`
- `GET /risk`
- `GET /patterns`
- `GET /correlation`
- `GET /plot/correlation.png`
- `GET /plot/candlestick.png`
- `GET /plot/returns.png`
- `GET /plot/series.png`
- `GET /plot/risk.png`
- `GET /report.pdf`

## Persistencia y despliegue

Los directorios de datos y reportes pueden configurarse con variables de entorno:

- `ANALIZADOR_DATA_DIR`
- `ANALIZADOR_REPORTS_DIR`

Si no estan definidas, el proyecto usa `data/processed/` y `reports/` en local. Si el entorno no permite escritura, cae a directorios temporales para evitar que la aplicacion se rompa.

El servidor web escucha por defecto en `0.0.0.0` y toma `PORT` del entorno,
para que plataformas como Render puedan detectar el puerto expuesto.

## Ejecucion local

```powershell
cd "d:\Repositorios_UQ\proyecto-algoritmos\analizador"
py -3 -m pip install -r requirements.txt
py -3 api.py
```

Abrir:

```text
http://127.0.0.1:8000/
```

Reconstruir el dataset:

```powershell
py -3 src/extraccion_datos.py
```

## Uso de IA

Se declara el uso de asistencia de IA generativa como apoyo para organizacion, redaccion y revision. La logica matematica y los algoritmos quedan implementados explicitamente en el codigo fuente.

## Referencias academicas

- Deza, M. M. and Deza, E. (2009). *Encyclopedia of Distances*.
- Pearson, K. (1895). *Notes on regression and inheritance in the case of two parents*.
- Sakoe, H. and Chiba, S. (1978). *Dynamic programming algorithm optimization for spoken word recognition*.
- Salton, G. and McGill, M. J. (1983). *Introduction to Modern Information Retrieval*.
- Hull, J. C. (2018). *Options, Futures, and Other Derivatives*.
