# Mapa de modulos

Este directorio organiza el proyecto por requerimientos funcionales para que sea facil ubicar:

- que hace cada modulo,
- que archivos lo sostienen,
- que endpoints lo alimentan,
- y que evidencia usar al sustentar el proyecto.

## Estructura

- `modules/etl/`: extraccion, limpieza, unificacion y vista previa del dataset.
- `modules/similarity/`: comparacion de activos y medidas de similitud.
- `modules/patterns/`: patrones con ventanas deslizantes y riesgo.
- `modules/visualization/`: graficas tecnicas, correlacion y reporte PDF.
- `modules/docs/`: arquitectura, formulas, despliegue y sustentacion.

## Estado general

- ETL: implementado y operando desde `src/extraccion_datos.py`.
- Similitud: implementado en `src/analisis_financiero.py` y expuesto en la web.
- Patrones y riesgo: implementado en `src/analisis_financiero.py` y consumido por la UI.
- Visualizacion y PDF: implementado en `src/visualizacion.py` y `src/reporte_pdf.py`.
- Documentacion y despliegue: en organizacion activa dentro de `modules/docs/` y `docs/`.

## Criterio de uso

Cada carpeta debe responder tres preguntas:

1. Que problema resuelve.
2. De donde salen sus datos.
3. Que archivo o endpoint permite demostrarlo.
