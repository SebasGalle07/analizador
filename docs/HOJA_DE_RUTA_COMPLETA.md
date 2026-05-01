# Hoja de ruta completa del proyecto

## Objetivo

Dejar la aplicacion lista para entrega academica y demostracion, cumpliendo los requerimientos del enunciado y cerrando cinco frentes de trabajo:

1. Organizar la aplicacion por modulos de acuerdo a los requerimientos.
2. Organizar la exportacion del reporte PDF.
3. Preparar el despliegue de la aplicacion.
4. Redactar un documento tecnico explicando graficos, formulas, teoria matematica e interaccion algoritimica.
5. Incorporar logs de la aplicacion en consola.

Esta hoja de ruta parte del estado actual del repositorio y propone el orden mas seguro para terminarlo sin romper la base funcional existente.

## Estado actual resumido

El proyecto ya tiene una base funcional:

- `extraccion_datos.py` ejecuta el ETL desde Yahoo Finance.
- `analisis_financiero.py` contiene los algoritmos de similitud, riesgo, patrones y correlacion.
- `visualizacion.py` genera graficas PNG.
- `reporte_pdf.py` arma un PDF tecnico.
- `api.py` expone la aplicacion Flask y conecta todos los servicios.
- `static/` contiene la interfaz web.

La siguiente fase no es "crear desde cero", sino ordenar, documentar, robustecer y preparar para entrega.

## Criterios de cierre

Antes de considerar el proyecto terminado, deberia cumplirse lo siguiente:

- Cada requerimiento del enunciado tiene un modulo o capa claramente identificable.
- El PDF puede generarse de forma reproducible desde la web y desde consola.
- La aplicacion puede ejecutarse localmente y en despliegue con una configuracion clara.
- Existe un documento tecnico que explica cada grafico, cada algoritmo y su fundamento matematico.
- La consola registra eventos relevantes del flujo ETL, analisis, PDF y errores.

## Fase 1. Organizacion modular por requerimientos

### Objetivo

Separar el proyecto por responsabilidades funcionales para que el codigo quede alineado con el enunciado y sea facil de mantener, probar y documentar.

### Resultado esperado

Una estructura modular donde cada requerimiento tenga su propio grupo de archivos o paquete.

### Propuesta de organizacion

Se recomienda migrar hacia una estructura como esta:

```text
analizador/
  app/
    __init__.py
    config.py
    routes/
      __init__.py
      web.py
      api.py
    services/
      __init__.py
      etl_service.py
      analysis_service.py
      visualization_service.py
      report_service.py
      logging_service.py
    domain/
      __init__.py
      datasets.py
      metrics.py
      patterns.py
      risk.py
    infrastructure/
      __init__.py
      yahoo_client.py
      csv_repository.py
      pdf_renderer.py
  static/
  docs/
  reports/
  dataset_maestro.csv
  run.py
```

### Distribucion por requerimiento

#### Requerimiento 1: ETL

Responsabilidad:

- Descarga de datos.
- Limpieza.
- Unificacion de calendarios.
- Persistencia del CSV maestro.

Modulo sugerido:

- `app/infrastructure/yahoo_client.py`
- `app/services/etl_service.py`
- `app/infrastructure/csv_repository.py`

#### Requerimiento 2: Similitud de series

Responsabilidad:

- Euclidiana.
- Pearson.
- DTW.
- Coseno.
- Alineacion de series y retornos.

Modulo sugerido:

- `app/services/analysis_service.py`
- `app/domain/metrics.py`

#### Requerimiento 3: Patrones y riesgo

Responsabilidad:

- Ventanas deslizantes.
- Conteo de patrones.
- Volatilidad.
- Categoria de riesgo.

Modulo sugerido:

- `app/domain/patterns.py`
- `app/domain/risk.py`
- `app/services/analysis_service.py`

#### Requerimiento 4: Visualizaciones y dashboard

Responsabilidad:

- Heatmap de correlacion.
- Velas con medias moviles.
- Graficas comparativas.
- Barras de riesgo.

Modulo sugerido:

- `app/services/visualization_service.py`
- `static/index.html`
- `static/app.js`
- `static/styles.css`

#### Requerimiento 5: Despliegue y documentacion

Responsabilidad:

- Configuracion para ejecucion local y produccion.
- Documento tecnico.
- Logs.

Modulo sugerido:

- `app/config.py`
- `app/services/logging_service.py`
- `docs/`
- `run.py`

### Tareas concretas de esta fase

1. Separar la logica de negocio de `api.py`.
2. Mover funciones de descarga a un cliente de infraestructura.
3. Mover funciones de calculo a servicios de analisis.
4. Dejar `api.py` solo como capa de orquestacion HTTP.
5. Mantener compatibilidad con el dashboard actual mientras se reorganiza.

### Entregable de esta fase

Una base de codigo modular con responsabilidades claras y sin logica critica mezclada en el archivo principal de la API.

## Fase 2. Organizacion de la exportacion del reporte PDF

### Objetivo

Convertir el PDF en un componente formal del proyecto, con entradas bien definidas, salida reproducible y contenido alineado con el analisis del sistema.

### Resultado esperado

Un servicio de reporte que pueda llamarse desde:

- la web,
- la consola,
- y eventualmente tareas automáticas.

### Estructura recomendada del PDF

1. Portada tecnica.
2. Resumen del dataset.
3. Metricas de similitud.
4. Ranking de riesgo.
5. Patrones detectados.
6. Correlacion entre activos.
7. Graficos seleccionados.
8. Seccion de formulas y complejidad.
9. Notas metodologicas y limitaciones.

### Reglas de diseno del servicio

- El reporte debe recibir un conjunto de parametros, no depender de estado global oculto.
- El contenido textual debe construirse a partir de datos calculados, no de texto manual disperso.
- El archivo generado debe guardarse en `reports/` con nombre unico y trazable por fecha.
- La API debe devolver la ruta o descargar el PDF, pero no mezclar composicion con transporte HTTP.

### Tareas concretas de esta fase

1. Extraer la composicion del PDF a una capa de servicio.
2. Definir una plantilla clara de secciones.
3. Crear funciones reutilizables para insertar texto, tablas y graficos.
4. Hacer que el endpoint `/report.pdf` solo invoque el servicio.
5. Agregar validacion de simbolos y parametros antes de generar el archivo.

### Entregable de esta fase

Un generador de reportes limpio, reutilizable y listo para demostracion.

## Fase 3. Despliegue de la aplicacion

### Objetivo

Dejar la aplicacion preparada para ejecucion repetible en entorno local y en un entorno de despliegue.

### Resultado esperado

Una aplicacion que pueda arrancar con instrucciones simples y configuracion clara.

### Estrategia recomendada

#### Entorno local

- Crear un punto de entrada unico, por ejemplo `run.py`.
- Centralizar configuraciones en `app/config.py`.
- Definir variables de entorno para puerto, debug y rutas.
- Mantener `requirements.txt` actualizado.

#### Entorno de produccion

Opciones recomendadas:

- `gunicorn` en Linux o WSL.
- `waitress` en Windows si se desea un servidor WSGI sencillo.
- Variables de entorno para activar `debug=False`.

#### Archivos de soporte

- `Procfile` si se desea un despliegue tipo PaaS.
- `runtime.txt` si la plataforma lo requiere.
- `README.md` con pasos de instalacion y ejecucion.

### Tareas concretas de esta fase

1. Crear un comando de arranque unico.
2. Separar configuracion de desarrollo y produccion.
3. Verificar que el proyecto arranque sin depender de rutas absolutas.
4. Definir si el despliegue sera local, en servidor institucional o en nube.
5. Documentar el flujo de arranque paso a paso.

### Entregable de esta fase

Una aplicacion lista para correr en un entorno controlado, con instrucciones reproducibles.

## Fase 4. Documento tecnico explicativo

### Objetivo

Producir un documento tecnico completo que explique el proyecto desde la perspectiva algoritmica, matematica y funcional.

### Resultado esperado

Un documento que sirva para sustentar el trabajo ante docente o jurado, con claridad sobre:

- que hace cada grafico,
- que mide cada algoritmo,
- por que cada formula es valida,
- como se conecta cada componente del sistema.

### Estructura sugerida del documento tecnico

#### 1. Introduccion

- Problema a resolver.
- Objetivo del analisis financiero.
- Alcance del sistema.

#### 2. Arquitectura del sistema

- Capas del sistema.
- Flujo ETL -> analisis -> visualizacion -> reporte.
- Roles de cada modulo.

#### 3. ETL y construccion del dataset

- Fuente de datos.
- Limpieza.
- Unificacion de calendarios.
- Tratamiento de faltantes.
- Justificacion del forward fill y sus efectos.

#### 4. Analisis de similitud

Para cada metodo:

- definicion matematica,
- idea algoritmica,
- complejidad temporal y espacial,
- interpretacion del resultado,
- limitaciones.

Metodos:

- Distancia euclidiana.
- Correlacion de Pearson.
- DTW.
- Similitud coseno.

#### 5. Riesgo y volatilidad

- Retornos diarios.
- Desviacion estandar muestral.
- Volatilidad anualizada.
- Categoria de riesgo.
- Ranking de activos.

#### 6. Patrones con ventanas deslizantes

- Definicion de cada patron.
- Ventana movil.
- Frecuencia de aparicion.
- Complejidad de deteccion.

#### 7. Visualizaciones

Debe explicarse una por una:

- Heatmap de correlacion.
- Velas japonesas con SMA.
- Serie comparativa de precios.
- Retornos diarios.
- Barras de volatilidad.

#### 8. Reporte PDF

- Que se incluye.
- Como se genera.
- Por que es reproducible.

#### 9. Evidencia de logs y operacion

- Que eventos se registran.
- Que errores se capturan.
- Como ayuda a depuracion y auditoria.

#### 10. Limitaciones y trabajo futuro

- Dependencia de la fuente externa.
- Diferencias por calendario bursatil.
- Posibles mejoras en cache, rendimiento y validacion.

### Para cada grafico se debe explicar

- Que representa.
- Que datos consume.
- Que formula usa.
- Que interpreta el usuario.
- Que algoritmo lo genera.
- Que supuestos matematicos hay detras.

### Entregable de esta fase

Un documento tecnico final, coherente con el codigo y con el enunciado del proyecto.

## Fase 5. Logs de la aplicacion en consola

### Objetivo

Agregar trazabilidad al flujo del sistema para que se pueda auditar ejecucion, detectar fallas y entender el comportamiento de la aplicacion.

### Resultado esperado

Mensajes estructurados en consola para:

- inicio y fin de ETL,
- descarga por activo,
- limpieza de datos,
- construccion del dataset,
- calculo de metricas,
- generacion de graficas,
- generacion de PDF,
- errores y excepciones.

### Recomendacion tecnica

Usar el modulo `logging` de Python con niveles:

- `DEBUG` para detalle interno.
- `INFO` para eventos de negocio.
- `WARNING` para situaciones no criticas.
- `ERROR` para fallos recuperables.
- `CRITICAL` para errores graves.

### Formato sugerido de los logs

```text
2026-04-30 22:15:10 | INFO  | ETL | Descargando VOO
2026-04-30 22:15:11 | INFO  | ETL | VOO descargado con 1308 registros
2026-04-30 22:15:15 | INFO  | ANALISIS | Calculando correlacion
2026-04-30 22:15:16 | INFO  | PDF | Reporte generado en reports/reporte_financiero_...
```

### Puntos donde debe instrumentarse

1. Inicio del servidor.
2. Inicio del build del dataset.
3. Descarga de cada simbolo.
4. Resultado de limpieza.
5. Persistencia de CSV y JSON de ETL.
6. Cada endpoint importante de analisis.
7. Generacion de imagenes.
8. Generacion de PDF.
9. Captura de errores de red y de datos.

### Entregable de esta fase

Una aplicacion observable y diagnosticable desde consola.

## Orden de ejecucion recomendado

El orden de trabajo mas seguro es este:

1. Modularizacion del codigo.
2. Logs de consola.
3. Refactor del reporte PDF.
4. Documento tecnico final.
5. Preparacion del despliegue.

Este orden reduce el riesgo porque primero estabiliza el codigo base y luego construye documentacion y despliegue sobre una arquitectura ya limpia.

## Plan de implementacion por etapas

### Etapa A. Base estructural

- Crear paquetes y separar responsabilidades.
- Dejar la API como capa de transporte.
- Encapsular ETL, analisis, visualizacion y reporte.

### Etapa B. Observabilidad

- Agregar logging centralizado.
- Registrar eventos clave y errores.
- Mantener mensajes utiles para depuracion.

### Etapa C. Reporteria

- Reorganizar la composicion del PDF.
- Alinear secciones con los requerimientos.
- Asegurar consistencia entre reporte y dashboard.

### Etapa D. Documentacion tecnica

- Escribir un documento tecnico amplio.
- Incluir formulas, teoria y complejidad.
- Vincular cada grafico con su algoritmo.

### Etapa E. Despliegue

- Preparar arranque unico.
- Definir configuracion por entorno.
- Documentar ejecucion y entrega.

## Riesgos y cuidados

- Dependencia de la fuente externa para descargar datos.
- Posibles cambios de formato en Yahoo Finance.
- Diferencias entre calendarios bursatiles.
- Tiempo de ejecucion elevado al reconstruir el ETL.
- PDF o graficas demasiado pesadas si se incluyen demasiados activos.

## Resultado final esperado

Al cerrar esta hoja de ruta, el proyecto quedaria con:

- codigo modular y entendible,
- dashboard operativo,
- PDF tecnico reproducible,
- despliegue documentado,
- logs en consola,
- y sustentacion matematica y algoritmica clara.

