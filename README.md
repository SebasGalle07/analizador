# Proyecto de Analisis de Algoritmos

## Descripcion general

Este proyecto fue desarrollado para la asignatura **Analisis de Algoritmos**. Su finalidad es construir un dataset financiero real y utilizarlo para evaluar el comportamiento de varios algoritmos de ordenamiento implementados manualmente.

El sistema descarga informacion historica de varios activos bursatiles desde Yahoo Finance, limpia y unifica esos datos en un archivo CSV maestro, y despues usa ese CSV para ejecutar diferentes algoritmos de ordenamiento, medir sus tiempos y visualizar los resultados.

## Objetivo del proyecto

El objetivo academico no es solo programar algoritmos, sino observar como se comportan sobre un conjunto de datos real. Esto permite comparar teoria y practica con un escenario mas cercano a una aplicacion real.

El proyecto permite:

- descargar datos historicos financieros;
- limpiar duplicados por fecha;
- consolidar multiples activos en un solo dataset;
- guardar el resultado en CSV;
- ejecutar algoritmos de ordenamiento sobre ese dataset;
- comparar tiempos de ejecucion;
- obtener los dias con mayor volumen para un simbolo especifico;
- visualizar resultados desde una interfaz web.

## Estructura del proyecto

```text
analizador/
|-- .gitignore
|-- README.md
|-- api.py
|-- extraccion_datos.py
|-- ordenamiento.py
|-- requirements.txt
|-- dataset_maestro.csv
|-- static/
|   |-- index.html
|   |-- styles.css
|   |-- app.js
```

## Funcion de cada archivo

### `extraccion_datos.py`

Este archivo implementa el proceso ETL:

- **Extraccion**: consulta Yahoo Finance para obtener precios historicos.
- **Transformacion**: elimina fechas duplicadas y unifica varios activos.
- **Carga**: guarda el resultado final en `dataset_maestro.csv`.

### `ordenamiento.py`

Este archivo contiene:

- lectura del dataset CSV;
- funciones auxiliares para obtener precio de cierre y volumen por simbolo;
- implementacion manual de varios algoritmos de ordenamiento;
- benchmark de tiempos;
- logica para extraer los dias con mayor volumen.

### `api.py`

Expone el proyecto mediante `FastAPI`. Permite:

- consultar el estado del sistema;
- listar algoritmos disponibles;
- obtener un resumen del dataset;
- ejecutar el analisis para un simbolo;
- servir la interfaz web.

### `static/`

Contiene la interfaz grafica web:

- `index.html`: estructura de la pagina;
- `styles.css`: apariencia visual;
- `app.js`: conexion con la API y render de resultados.

## Flujo de funcionamiento paso a paso

### 1. Extraccion de datos

El proyecto consulta Yahoo Finance usando peticiones HTTP para descargar datos historicos de varios simbolos financieros. Por defecto, se trabaja con 20 activos:

- VOO
- EC
- AAPL
- MSFT
- TSLA
- AMZN
- GOOGL
- META
- NVDA
- NFLX
- JPM
- V
- WMT
- JNJ
- BAC
- PG
- XOM
- DIS
- HD
- MA

Para cada simbolo se obtienen campos como:

- fecha;
- precio de apertura;
- precio maximo;
- precio minimo;
- precio de cierre;
- volumen.

### 2. Limpieza de duplicados

Despues de descargar los datos, el sistema elimina registros repetidos por fecha. Esto garantiza que por cada fecha exista un unico registro por activo.

### 3. Unificacion del portafolio

Los datos de todos los simbolos se integran en una sola tabla maestra. Cada fila representa una fecha y cada activo aporta dos columnas principales:

- `<SIMBOLO>_Close`
- `<SIMBOLO>_Volume`

Si un activo no tiene informacion en una fecha, se usa el ultimo precio conocido y se asigna volumen `0`.

### 4. Generacion del CSV maestro

El dataset consolidado se guarda como `dataset_maestro.csv`. Este archivo sirve como base reproducible del proyecto y evita tener que consultar nuevamente la fuente de datos cada vez.

### 5. Carga del dataset para analisis

El archivo `ordenamiento.py` lee el CSV y transforma cada fila en un registro que puede ser procesado por los algoritmos.

### 6. Criterio de ordenamiento

Los algoritmos ordenan usando este criterio:

1. primero por fecha;
2. en caso de empate, por precio de cierre del simbolo seleccionado.

Esto permite conservar un orden cronologico y a la vez tener un criterio secundario de comparacion.

### 7. Medicion de tiempos

Cada algoritmo es ejecutado y cronometrado en milisegundos. De esta manera se puede comparar empiricamente su desempeno sobre el mismo dataset.

### 8. Extraccion del top de volumen

El sistema tambien identifica los `N` dias con mayor volumen para un simbolo especifico y luego los ordena cronologicamente para su presentacion final.

### 9. Visualizacion en interfaz web

La interfaz web permite:

- ver estadisticas del dataset;
- seleccionar un simbolo;
- elegir algoritmos a comparar;
- ejecutar el benchmark;
- ver el top de volumen;
- inspeccionar una vista previa del CSV.

## Algoritmos implementados

En `ordenamiento.py` se implementaron manualmente los siguientes algoritmos:

- Selection Sort
- Comb Sort
- Tim Sort
- Quick Sort
- Heap Sort
- Tree Sort
- Bucket Sort
- Radix Sort
- Pigeonhole Sort
- Gnome Sort
- Binary Insertion Sort
- Bitonic Sort

## Tecnologias utilizadas

- Python
- requests
- csv
- FastAPI
- HTML
- CSS
- JavaScript

## Como ejecutar el proyecto

## Opcion 1: Scripts por consola

### Paso 1. Entrar a la carpeta del proyecto

En PowerShell:

```powershell
cd "C:\Users\sebas\Desktop\Universidad\analisis\analizador"
```

En Git Bash:

```bash
cd "/c/Users/sebas/Desktop/Universidad/analisis/analizador"
```

### Paso 2. Instalar dependencias

```powershell
py -3 -m pip install -r requirements.txt
```

### Paso 3. Construir o actualizar el dataset

```powershell
py -3 extraccion_datos.py
```

Este paso descarga los datos, los limpia, los unifica y genera `dataset_maestro.csv`.

### Paso 4. Ejecutar el benchmark de algoritmos

```powershell
py -3 ordenamiento.py
```

Esto carga el CSV y ejecuta los algoritmos mostrando sus tiempos.

## Opcion 2: API e interfaz web

### Paso 1. Entrar a la carpeta

```powershell
cd "C:\Users\sebas\Desktop\Universidad\analisis\analizador"
```

### Paso 2. Instalar dependencias

```powershell
py -3 -m pip install -r requirements.txt
```

### Paso 3. Levantar el servidor

```powershell
py -3 -m uvicorn api:app --reload
```

### Paso 4. Abrir en el navegador

Interfaz principal:

```text
http://127.0.0.1:8000/
```

Documentacion tecnica:

```text
http://127.0.0.1:8000/docs
```

## Que hace la interfaz

La interfaz grafica muestra:

- nombre del archivo fuente;
- rango de fechas del dataset;
- cantidad de filas, columnas y simbolos;
- lista de simbolos disponibles;
- benchmark de algoritmos;
- top de dias con mayor volumen;
- vista previa del CSV.

## Explicacion academica para el profesor

Este proyecto demuestra varias ideas importantes de Analisis de Algoritmos:

- implementacion manual de algoritmos de ordenamiento;
- comparacion de tiempos de ejecucion en un mismo entorno;
- aplicacion sobre datos reales y no solo listas artificiales;
- separacion entre construccion del dataset y analisis posterior;
- visualizacion clara de resultados para facilitar la interpretacion.

En otras palabras, el proyecto no solo presenta codigo de ordenamiento, sino un flujo completo de trabajo:

1. adquisicion de datos;
2. limpieza;
3. estructuracion;
4. ordenamiento;
5. medicion;
6. visualizacion.

## Conclusiones

El valor principal del proyecto es que permite estudiar algoritmos de ordenamiento sobre un dataset financiero real. Esto lo convierte en una evidencia practica de como los algoritmos responden frente a datos concretos, manteniendo un enfoque academico y reproducible.
