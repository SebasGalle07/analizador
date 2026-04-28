# Documento tecnico

## Arquitectura

La aplicacion se divide en cuatro capas:

- `extraccion_datos.py`: ETL reproducible con peticiones HTTP directas a Yahoo Finance.
- `analisis_financiero.py`: algoritmos matematicos implementados desde cero.
- `visualizacion.py`: graficas con `matplotlib`.
- `api.py`: aplicacion web Flask y endpoints JSON/PNG/PDF.

Flujo de componentes:

```text
Usuario web
  -> Flask API
    -> ETL HTTP Yahoo Finance -> CSV maestro
    -> Analisis financiero manual -> metricas JSON
    -> Matplotlib -> PNG/PDF
```

## ETL

La descarga se realiza contra:

```text
https://query2.finance.yahoo.com/v8/finance/chart/{SIMBOLO}
```

El codigo construye manualmente `period1`, `period2`, `interval`, cabeceras HTTP,
manejo de errores de estado, parsing JSON y escritura CSV. No se usa `yfinance`,
`pandas_datareader`, `pandas`, `numpy` ni funciones que encapsulen la descarga.

El portafolio por defecto incluye acciones colombianas disponibles en Yahoo
Finance (`ECOPETROL.CL`, `ISA.CL`, `GEB.CL`, `GRUPOARGOS.CL`, entre otras),
ADRs colombianos (`EC`, `CIB`, `AVAL`, `TGLS`) y ETFs globales (`VOO`, `SPY`,
`QQQ`, `EEM`, `GLD`, `TLT`, etc.). El dataset resultante supera los 20 activos
y cubre minimo cinco anos si la fuente publica devuelve el historial completo.

Limpieza:

- Duplicados por fecha: se conserva el ultimo registro recibido.
- Precios nulos, negativos o cero: se descartan porque distorsionan retornos.
- OHLC inconsistente: se descarta si `High` queda por debajo de algun precio
  observado o `Low` por encima.
- Fechas faltantes por calendario bursatil: se alinean con calendario union.
  Los precios se imputan con forward fill, volumen queda en `0` y la columna
  `*_Missing` queda en `1`.

Impacto: el forward fill permite comparar activos con calendarios diferentes
sin perder fechas, pero puede suavizar retornos en dias no negociados. Por eso
la imputacion queda marcada y se documenta en el reporte.

## Algoritmos de similitud

Todos los algoritmos estan en `analisis_financiero.py` y usan listas y bucles.

### Distancia euclidiana

Formula:

```text
d(P,Q)=sqrt(sum((p_i-q_i)^2))
```

Se calcula sobre precios alineados y sobre retornos diarios. Recorre una vez
los vectores.

- Tiempo: `O(n)`
- Espacio: `O(1)`

Pseudocodigo:

```text
suma <- 0
para i desde 0 hasta n-1:
    diferencia <- P[i] - Q[i]
    suma <- suma + diferencia^2
retornar sqrt(suma)
```

### Correlacion de Pearson

Formula muestral equivalente:

```text
r_xy = sum((x_i-x_bar)(y_i-y_bar)) /
       sqrt(sum((x_i-x_bar)^2) sum((y_i-y_bar)^2))
```

Se aplica a retornos diarios. `r=1` indica relacion lineal perfecta, `r=0`
ausencia de relacion lineal y `r=-1` relacion inversa perfecta.

- Tiempo: `O(n)`
- Espacio: `O(1)`

Pseudocodigo:

```text
media_x <- promedio(X)
media_y <- promedio(Y)
num <- 0
sx <- 0
sy <- 0
para i desde 0 hasta n-1:
    dx <- X[i] - media_x
    dy <- Y[i] - media_y
    num <- num + dx * dy
    sx <- sx + dx^2
    sy <- sy + dy^2
retornar num / sqrt(sx * sy)
```

### Dynamic Time Warping

Recurrencia:

```text
D(i,j)=|p_i-q_j|+min(D(i-1,j), D(i,j-1), D(i-1,j-1))
```

La matriz de costos permite alineaciones one-to-many y many-to-one. Despues de
llenar la matriz se aplica backtracking desde `(n,m)` hasta `(0,0)` para
reconstruir la ruta.

- Tiempo: `O(n*m)`
- Espacio: `O(n*m)`

Pseudocodigo:

```text
crear matriz D de (n+1) x (m+1) con infinito
D[0][0] <- 0
para i desde 1 hasta n:
    para j desde 1 hasta m:
        costo <- abs(P[i-1] - Q[j-1])
        D[i][j] <- costo + min(D[i-1][j], D[i][j-1], D[i-1][j-1])
ruta <- []
i <- n; j <- m
mientras i > 0 y j > 0:
    agregar (i-1, j-1) a ruta
    mover a la celda previa con menor costo
retornar D[n][m] y ruta invertida
```

### Similitud coseno

Formula:

```text
cos(P,Q) = (P dot Q) / (||P|| ||Q||)
```

Se aplica a retornos diarios. Valores cercanos a `1` indican vectores con
direccion similar; valores cercanos a `-1` indican direcciones opuestas.

- Tiempo: `O(n)`
- Espacio: `O(1)`

Pseudocodigo:

```text
producto <- 0
norma_p <- 0
norma_q <- 0
para i desde 0 hasta n-1:
    producto <- producto + P[i] * Q[i]
    norma_p <- norma_p + P[i]^2
    norma_q <- norma_q + Q[i]^2
retornar producto / (sqrt(norma_p) * sqrt(norma_q))
```

## Patrones y volatilidad

El algoritmo de ventanas deslizantes recorre retornos y cuenta:

- `k` dias consecutivos con retorno positivo.
- `k` dias consecutivos con retorno negativo seguidos de un retorno mayor o
  igual al umbral de rebote.

Para cada activo se calcula media diaria, desviacion estandar muestral y
volatilidad anualizada:

```text
sigma_anual = sigma_diaria * sqrt(252)
```

Categorias:

- Conservador: volatilidad anual menor a 10%.
- Moderado: entre 10% y 20%.
- Agresivo: mayor a 20%.

## Visualizaciones

`visualizacion.py` genera:

- Mapa de calor de correlacion Pearson entre todos los activos.
- Grafico de velas con medias moviles simples calculadas manualmente.
- Grafico de comparacion de precios.
- Barras de volatilidad anualizada.

Se usa `matplotlib`, que esta permitido para visualizacion basica.

## Reporte PDF

`reporte_pdf.py` compila:

- Resumen del dataset y fuente.
- Metricas de similitud y complejidad.
- Ranking de riesgo.
- Grafico de precios.
- Mapa de calor de correlacion.

El endpoint es:

```text
GET /report.pdf?symbol_a=VOO&symbol_b=ECOPETROL.CL
```

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

Reconstruir dataset por consola:

```powershell
py -3 extraccion_datos.py
```

## Uso de IA

Se declara el uso de asistencia de IA generativa como apoyo para organizacion
del codigo, documentacion y revision de implementacion. Las formulas y
algoritmos quedan implementados explicitamente en el codigo fuente para que el
analisis sea verificable.

## Referencias academicas

- Euclidean distance: Deza, M. M. and Deza, E. (2009). Encyclopedia of
  Distances. Springer.
- Pearson correlation: Pearson, K. (1895). Notes on regression and inheritance
  in the case of two parents. Proceedings of the Royal Society of London.
- Dynamic Time Warping: Sakoe, H. and Chiba, S. (1978). Dynamic programming
  algorithm optimization for spoken word recognition. IEEE TASSP.
- Cosine similarity: Salton, G. and McGill, M. J. (1983). Introduction to
  Modern Information Retrieval.
- Volatility as standard deviation of returns: Hull, J. C. (2018). Options,
  Futures, and Other Derivatives.
