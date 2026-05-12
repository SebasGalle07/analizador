# Guia de sustentacion del proyecto

## 1. Objetivo de este documento

Esta guia sirve para explicar el proyecto de punta a punta en una sustentacion.
La idea es que puedas responder:

1. Que hace cada parte.
2. Donde esta implementada.
3. Como se relaciona con el resto del sistema.
4. Que ejemplo mostrar en pantalla o hacer a mano para demostrar que funciona.

La version verificada del proyecto ya cubre el enunciado completo con:

- ETL automatizado.
- Similitud entre series de tiempo.
- Patrones y riesgo.
- Visualizacion y PDF.
- Despliegue y documentacion tecnica.

Los numeros reales que debes usar en la sustentacion son:

- 28 activos.
- 1308 filas.
- Rango historico de `2021-04-22` a `2026-04-30`.

No conviene mencionar cifras aproximadas si ya tienes estas verificadas.

## 2. Idea central del proyecto

Puedes resumirlo asi:

> Este proyecto construye un dashboard bursatil que descarga datos historicos desde Yahoo Finance por HTTP directo, limpia y unifica las series, compara activos con algoritmos clasicos, detecta patrones de comportamiento, calcula riesgo, genera graficas y exporta un reporte PDF.

Si te piden una version mas corta:

> El sistema convierte datos financieros historicos en analisis comparativos, patrones, riesgo y visualizaciones, todo desde una aplicacion Flask.

## 3. Mapa del repositorio

Esta es la lectura mas util para sustentar porque conecta carpeta, archivo, funcion y resultado.

| Ruta | Que hace | Como se relaciona | Que mostrar |
| --- | --- | --- | --- |
| `src/extraccion_datos.py` | Descarga, limpia y unifica el dataset maestro | Alimenta todo el sistema con datos reales | ETL, reporte JSON, dataset maestro |
| `src/analisis_financiero.py` | Algoritmos de similitud, patrones, riesgo y correlacion | Consume el dataset maestro y produce metricas | Similarity, patterns, risk, correlation |
| `src/visualizacion.py` | Genera PNG de graficas tecnicas | Toma resultados del analisis y los vuelve visuales | Heatmap, velas, series, retornos, riesgo |
| `src/reporte_pdf.py` | Compone el PDF tecnico | Junta analisis + graficas + resumen para entregar evidencia | Boton de reporte y archivo PDF |
| `src/api.py` | Expone la app Flask y los endpoints | Es el puente entre frontend y backend | Rutas `/ui/*`, `/dataset/*`, `/plot/*`, `/report.pdf` |
| `src/paths.py` | Manejo de rutas de datos y reportes | Permite correr local o en despliegue | Variables de entorno y directorios |
| `static/app.js` | Logica del frontend y consumo de API | Hace que la UI consulte el backend | Actualizar, cambiar simbolos, descargar PDF |
| `static/modules/etl/index.html` | Pantalla del requerimiento 1 | Muestra el dataset y la trazabilidad ETL | Tabla, estadisticas, vista previa |
| `static/modules/similarity/index.html` | Pantalla del requerimiento 2 | Muestra la comparacion entre dos activos | Metric cards + graficas |
| `static/modules/patterns/index.html` | Pantalla del requerimiento 3 | Muestra patrones y riesgo | Patrones + ranking |
| `static/modules/visualization/index.html` | Pantalla del requerimiento 4 | Muestra graficas y PDF | Candlestick + heatmap |
| `static/modules/docs/index.html` | Pantalla del requerimiento 5 | Muestra documentacion y formulas | Guia tecnica + formulas |
| `data/processed/dataset_maestro.json` o `.csv` | Dataset maestro final | Insumo principal de todos los analisis | Verificable en ETL |
| `data/processed/dataset_maestro_report.json` | Reporte de ETL | Evidencia de limpieza, cobertura y validacion | Estadisticas por activo |
| `reports/*.pdf` | Reportes tecnicos generados | Entrega consolidada del analisis | PDF descargable |
| `docs/DOCUMENTACION_TECNICA.md` | Documento tecnico formal | Explica arquitectura y complejidad | Soporte academico |
| `docs/HOJA_DE_RUTA_COMPLETA.md` | Estado y cierre del proyecto | Resume cumplimiento de requerimientos | Contexto de avance |
| `Procfile` | Arranque de despliegue | Permite que la app corra en hosting | `gunicorn src.api:app` |
| `requirements.txt` | Dependencias minimas | Reproducibilidad del entorno | Flask, requests, matplotlib, gunicorn |

## 4. Flujo completo del sistema

Este es el orden logico del proyecto:

1. El servidor Flask arranca desde `src/api.py`.
2. La pagina principal redirige a `/ui/etl`.
3. El usuario puede reconstruir el dataset con `POST /dataset/build`.
4. El ETL llama a `src/extraccion_datos.py`.
5. El dataset consolidado queda en `data/processed/`.
6. La pantalla de similitud llama a `POST /similarity`.
7. La pantalla de patrones llama a `/patterns` y `/risk`.
8. La pantalla de visualizacion llama a `/plot/correlation.png`, `/plot/candlestick.png`, `/plot/returns.png`, `/plot/series.png` y `/plot/risk.png`.
9. El PDF se descarga desde `/report.pdf`.
10. La documentacion se ve en `/ui/docs`.

Si quieres explicarlo en una sola frase:

> El backend construye el dataset, el analisis procesa las series y el frontend solo consume esos resultados y los presenta.

## 5. Como esta conectado cada requerimiento

### 5.1 Requerimiento 1: ETL

#### Que hace

- Descarga datos diarios historicos.
- Limpia valores invalidos.
- Unifica calendarios bursatiles.
- Marca faltantes.
- Construye el dataset maestro final.

#### Donde esta

- `src/extraccion_datos.py`
- `src/api.py` en `POST /dataset/build` y `GET /dataset/overview`
- `static/modules/etl/index.html`
- `data/processed/dataset_maestro.json`
- `data/processed/dataset_maestro_report.json`

#### Funciones clave para nombrar

- `descargar_yahoo_finance()`
- `limpiar_registros()`
- `unificar_portafolio()`
- `validar_requerimientos_etl()`
- `construir_dataset_maestro()`

#### Que decir en la sustentacion

- La descarga es por HTTP directo a Yahoo Finance.
- No se usa `yfinance` ni `pandas_datareader`.
- El dataset real cumple el minimo de 20 activos y 5 anos.
- La limpieza descarta datos invalidos y conserva trazabilidad con `*_Missing`.
- El forward fill evita perder fechas al comparar activos con calendarios distintos.

#### Que mostrar en pantalla

1. Abrir `/ui/etl`.
2. Mostrar el resumen con filas, activos y rango historico.
3. Mostrar el bloque de estadisticas por activo.
4. Hacer clic en `Reconstruir ETL` si quieres demostrar el flujo completo.
5. Mostrar la vista previa del dataset.

#### Ejemplo manual recomendado

Haz el ejemplo sobre una sola serie de precios y una sola fila:

- Escoge un activo como `VOO` o `ECOPETROL.CL`.
- Muestra una fila con `Fecha`, `Open`, `High`, `Low`, `Close`, `Volume`.
- Explica que si una fecha no existe para un activo, la app alinea por calendario union.
- Explica que si falta un precio, el sistema puede usar forward fill y marcar la columna `*_Missing`.

Si el profesor pregunta por la calidad de datos:

> La idea no es inventar datos, sino conservar continuidad temporal para poder comparar activos distintos sin romper las series.

### 5.2 Requerimiento 2: Similitud de series de tiempo

#### Que hace

- Compara dos activos.
- Calcula distancia euclidiana.
- Calcula correlacion de Pearson.
- Calcula DTW.
- Calcula similitud coseno.
- Grafica precios y retornos.

#### Donde esta

- `src/analisis_financiero.py`
- `src/api.py` en `POST /similarity`
- `src/visualizacion.py`
- `static/modules/similarity/index.html`

#### Funciones clave

- `alinear_series()`
- `alinear_retornos()`
- `distancia_euclidiana()`
- `correlacion_pearson()`
- `similitud_coseno()`
- `distancia_dtw()`
- `comparar_activos()`

#### Que decir en la sustentacion

- Euclidiana mide separacion entre vectores.
- Pearson mide relacion lineal.
- DTW permite comparar series con desfases temporales.
- Coseno mide si las series apuntan en la misma direccion.
- Todo se calcula sobre series alineadas y retornos diarios.

#### Que mostrar en pantalla

1. Abrir `/ui/similarity`.
2. Elegir dos activos.
3. Cambiar la banda DTW.
4. Mostrar las tarjetas con las metricas.
5. Mostrar las graficas de series y retornos.

#### Ejemplo manual recomendado

Haz el ejemplo a mano con una ventana pequena de 5 dias.

Recomendacion practica:

- Usa dos activos faciles de interpretar, por ejemplo `VOO` y `SPY`.
- Toma los primeros 5 cierres alineados y escribelos en la pizarra o diapositiva.
- Calcula sobre ese recorte:
  - Euclidiana: diferencia punto a punto.
  - Pearson: media, desviaciones y covarianza.
  - Coseno: producto punto y normas.
  - DTW: matriz de costo con camino minimo.

Si quieres una frase sencilla para explicar DTW:

> DTW no exige que las dos series avancen exactamente al mismo ritmo, por eso sirve cuando una se mueve con retraso o aceleracion frente a la otra.

#### Formula que conviene mencionar

- Euclidiana: `sqrt(sum((x_i - y_i)^2))`
- Pearson: `cov(X,Y) / (sigma_X * sigma_Y)`
- Coseno: `(X . Y) / (||X|| * ||Y||)`
- DTW: `D(i,j) = |x_i - y_j| + min(D(i-1,j), D(i,j-1), D(i-1,j-1))`

### 5.3 Requerimiento 3: Patrones y volatilidad

#### Que hace

- Busca patrones con ventana deslizante.
- Cuenta rachas alcistas.
- Cuenta rebotes despues de caidas.
- Cuenta consolidaciones de baja volatilidad.
- Calcula volatilidad anualizada.
- Clasifica riesgo.
- Ordena activos por riesgo.

#### Donde esta

- `src/analisis_financiero.py`
- `src/api.py` en `/patterns`, `/risk`
- `static/modules/patterns/index.html`

#### Funciones clave

- `contar_patrones()`
- `estadisticas_riesgo()`
- `max_drawdown()`
- `retornos_desde_precios()`
- `desviacion_estandar_muestral()`
- `media_movil_simple()`

#### Que decir en la sustentacion

- Los patrones se detectan con una ventana `k`.
- La racha alcista exige `k` retornos positivos seguidos.
- El rebote exige `k` retornos negativos seguidos y luego un retorno positivo suficientemente fuerte.
- La consolidacion de baja volatilidad exige retornos pequenos dentro de un umbral.
- El riesgo usa desviacion estandar diaria anualizada con `sqrt(252)`.
- El ranking se ordena por volatilidad anualizada de mayor a menor.

#### Que mostrar en pantalla

1. Abrir `/ui/patterns`.
2. Seleccionar un activo.
3. Cambiar `k` y el umbral de rebote.
4. Mostrar las formulas de patrones.
5. Mostrar el ranking de riesgo.

#### Ejemplo manual recomendado

Haz el ejemplo con una secuencia pequena de retornos, por ejemplo 5 o 6 dias.

Ejemplo de trabajo:

- Para P1, muestra tres retornos positivos seguidos.
- Para P2, muestra tres retornos negativos y luego un rebote.
- Para P3, muestra retornos cercanos a cero.

Si el profesor pregunta por volatilidad:

> Primero calculo la desviacion estandar de los retornos diarios y luego la anualizo para poder comparar activos en la misma escala.

Si pregunta por drawdown:

> Mido la caida maxima desde un pico hasta el minimo posterior.

### 5.4 Requerimiento 4: Visualizacion y PDF

#### Que hace

- Grafica el mapa de calor de correlacion.
- Grafica velas japonesas con SMA.
- Grafica series de precios.
- Grafica retornos.
- Grafica barras de riesgo.
- Genera un PDF tecnico completo.

#### Donde esta

- `src/visualizacion.py`
- `src/reporte_pdf.py`
- `src/api.py` en `/plot/*` y `/report.pdf`
- `static/modules/visualization/index.html`

#### Funciones clave

- `generar_heatmap_correlacion()`
- `generar_grafico_velas()`
- `generar_grafico_series()`
- `generar_grafico_retornos()`
- `generar_barras_riesgo()`
- `generar_reporte_pdf()`

#### Que decir en la sustentacion

- El heatmap resume la correlacion de retornos entre todos los activos.
- Las velas muestran OHLC y dos medias moviles.
- El PDF consolida resultados numericos y graficos.
- El PDF sirve como evidencia formal de todo el analisis.

#### Que mostrar en pantalla

1. Abrir `/ui/visualization`.
2. Elegir un activo y mostrar velas.
3. Mostrar el heatmap.
4. Descarga el PDF.
5. Si quieres, abre el PDF y muestra que incluye comparacion, riesgo y correlacion.

#### Ejemplo manual recomendado

Haz dos ejemplos pequenos:

- Para velas, usa un dia con `Open`, `High`, `Low`, `Close` y explica cuerpo y mecha.
- Para SMA, usa una ventana simple de 3 valores en el papel y explica que la app usa ventanas mayores como 20 y 50.

No intentes calcular todo el heatmap a mano. Mejor explica:

> Un coeficiente cercano a 1 significa que dos activos se mueven parecido; cercano a -1 significa que se mueven de forma opuesta.

### 5.5 Requerimiento 5: Despliegue y documentacion tecnica

#### Que hace

- Hace correr la aplicacion como web app.
- Define rutas de arranque y de datos.
- Expone la documentacion tecnica.
- Permite que el proyecto se pueda reproducir.

#### Donde esta

- `src/api.py`
- `src/paths.py`
- `Procfile`
- `requirements.txt`
- `docs/DOCUMENTACION_TECNICA.md`
- `docs/HOJA_DE_RUTA_COMPLETA.md`
- `static/modules/docs/index.html`

#### Funciones y piezas clave

- `page_docs()` en `src/api.py`
- `get_runtime_processed_dir()` en `src/paths.py`
- `get_runtime_reports_dir()` en `src/paths.py`
- `HOST=0.0.0.0` y `PORT` en `src/api.py`
- `web: gunicorn src.api:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120` en `Procfile`

#### Que decir en la sustentacion

- La app tiene ruta de documentacion funcional.
- El arranque en despliegue usa `PORT`.
- Los directorios de datos y reportes pueden configurarse con variables de entorno.
- Hay documentacion tecnica, hoja de ruta y README.

#### Que mostrar en pantalla

1. Abrir `/ui/docs`.
2. Mostrar la arquitectura y formulas.
3. Mostrar el `Procfile` o explicar su contenido.
4. Mostrar el README si te piden instrucciones de ejecucion.

#### Ejemplo manual recomendado

Aqui no necesitas cuentas manuales, sino explicar la infraestructura:

- que archivo arranca la app,
- donde se guardan datos,
- que variable controla el puerto,
- y como se hace el despliegue.

## 6. Preguntas tipicas del profesor y respuesta corta

### 6.1 De donde sacaron los datos?

> De Yahoo Finance mediante peticiones HTTP directas desde `src/extraccion_datos.py`.

### 6.2 Por que no usaron `yfinance`?

> Porque el enunciado restringe librerias de alto nivel que escondan la descarga principal.

### 6.3 Como manejaron datos faltantes?

> Se limpiaron registros invalidos, se unificaron calendarios y los faltantes se marcaron con `*_Missing`; en el alineamiento se usa forward fill cuando aplica.

### 6.4 Por que esos cuatro algoritmos de similitud?

> Porque cubren distancia, relacion lineal, alineacion temporal y similitud de direccion, que son enfoques complementarios.

### 6.5 Para que sirve DTW?

> Para comparar series que no van al mismo ritmo o que tienen desfases.

### 6.6 Como calculan el riesgo?

> Con desviacion estandar de retornos diarios, anualizada con `sqrt(252)`, y luego clasificada por umbrales.

### 6.7 Que evidencia queda de la sustentacion?

> El dataset maestro, el reporte ETL, las graficas PNG, el PDF tecnico y la documentacion del proyecto.

## 7. Orden recomendado para sustentar

Este orden funciona bien porque sigue la logica del sistema:

1. Presenta el problema y la idea general.
2. Abre `/ui/etl` y explica el origen del dataset.
3. Abre `/ui/similarity` y compara dos activos.
4. Abre `/ui/patterns` y explica patrones y riesgo.
5. Abre `/ui/visualization` y muestra heatmap, velas y PDF.
6. Abre `/ui/docs` y cierras con la arquitectura y despliegue.

## 8. Ejemplos manuales que si vale la pena hacer

Si tienes poco tiempo, estos son los que mas rinden en sustentacion:

1. Un ejemplo de 5 precios para Euclidiana, Pearson, coseno y DTW.
2. Un ejemplo de 5 o 6 retornos para patrones P1, P2 y P3.
3. Un ejemplo de 3 o 5 retornos para explicar volatilidad anualizada.
4. Un ejemplo de una vela para explicar OHLC.
5. Una interpretacion de una correlacion alta y una baja.

## 9. Lo que no debes olvidar decir

- El proyecto usa 28 activos y supera el minimo exigido.
- El horizonte historico supera 5 anos.
- La descarga principal no usa librerias prohibidas.
- Los algoritmos estan implementados en forma explicita.
- La documentacion ya esta alineada con el codigo real.
- La pagina de documentacion ya tiene ruta funcional.

## 10. Cierre sugerido para la sustentacion

Puedes cerrar asi:

> Este proyecto cumple el enunciado porque automatiza la extraccion, analiza similitud y patrones con algoritmos clasicos, visualiza resultados y los entrega en un PDF tecnico. Todo el flujo es reproducible, esta documentado y se puede ejecutar desde la aplicacion web.

