# Hoja de ruta completa del proyecto

## Proposito

Este documento resume como va el proyecto hoy, que partes ya estan alineadas con el enunciado y que falta para dejarlo al 100%.

La idea no es reinventar el sistema, sino responder tres preguntas de forma clara:

1. Que ya esta cubierto.
2. Que esta cubierto solo parcialmente.
3. Que falta ajustar para cumplir todo el alcance esperado.

## Lectura rapida del estado actual

El repositorio ya tiene una base solida para el proyecto financiero principal:

- ETL automatico desde Yahoo Finance por HTTP directo.
- Limpieza y unificacion de series de tiempo.
- Analisis de similitud entre activos.
- Analisis de patrones y volatilidad.
- Visualizaciones en PNG.
- Generacion de reporte PDF.
- API Flask para consumir todo desde web.

Tambien existe una linea separada de trabajo para ordenamiento en `experiments/ordenamiento.py`, pero esa parte no esta integrada al flujo principal del dashboard financiero.

## Cobertura actual frente al enunciado

### Requerimiento 1. ETL

### Estado: casi completo

Lo que ya esta:

- Descarga automatica de datos con `requests`.
- Fuente publica sin usar `yfinance` ni `pandas_datareader`.
- Construccion de dataset maestro.
- Limpieza de registros invalidos.
- Unificacion de calendarios bursatiles.
- Marcacion de faltantes con `*_Missing`.
- Persistencia en JSON y CSV.

Lo que falta revisar o fortalecer:

- Confirmar que el portafolio activo en ejecucion siempre cubra al menos 20 activos validos.
- Verificar que el horizonte historico real alcance 5 anos completos para todos los activos que se usan en entrega.
- Documentar mejor el criterio de imputacion y su impacto.
- Dejar una evidencia reproducible del dataset final que se va a mostrar al docente.

Archivos clave:

- [`src/extraccion_datos.py`](../src/extraccion_datos.py)
- [`src/api.py`](../src/api.py)

### Requerimiento 2. Similitud de series de tiempo

### Estado: completo

Lo que ya esta:

- Distancia euclidiana.
- Correlacion de Pearson.
- Dynamic Time Warping.
- Similitud coseno.
- Comparacion entre dos activos.
- Grafico de series y retornos.
- Explicacion matematica y de complejidad en el codigo tecnico.

Lo que falta para dejarlo mejor cerrado:

- Revisar que la interfaz web muestre de forma mas clara los resultados y su interpretacion.
- Asegurar que el PDF final exponga la complejidad y lectura de cada metrica de manera formal.

Archivos clave:

- [`src/analisis_financiero.py`](../src/analisis_financiero.py)
- [`src/visualizacion.py`](../src/visualizacion.py)
- [`src/reporte_pdf.py`](../src/reporte_pdf.py)

### Requerimiento 3. Patrones y volatilidad

### Estado: completo

Lo que ya esta:

- Conteo de patrones con ventana deslizante.
- Racha alcista.
- Rebote despues de caida.
- Consolidacion de baja volatilidad.
- Calculo de volatilidad anualizada.
- Clasificacion de riesgo por categoria.
- Ranking de activos por volatilidad.

Lo que falta revisar:

- Hacer mas visible en la documentacion final la formalizacion matematica de cada patron.
- Alinear la explicacion del riesgo con el criterio usado en la app.

Archivos clave:

- [`src/analisis_financiero.py`](../src/analisis_financiero.py)
- [`src/api.py`](../src/api.py)
- [`src/reporte_pdf.py`](../src/reporte_pdf.py)

### Requerimiento 4. Visualizacion y dashboard bursatil

### Estado: completo

Lo que ya esta:

- Heatmap de correlacion.
- Velas japonesas con medias moviles simples.
- Grafico comparativo de precios.
- Grafico de retornos.
- Barras de riesgo.
- Exportacion PDF con graficas y resumen tecnico.

Lo que falta revisar:

- Mejorar el orden visual de la interfaz web si quieren una entrega mas pulida.
- Validar que las rutas del dashboard esten bien descritas en el README final.

Archivos clave:

- [`src/visualizacion.py`](../src/visualizacion.py)
- [`src/reporte_pdf.py`](../src/reporte_pdf.py)
- [`static/`](../static)

### Requerimiento 5. Despliegue y documentacion tecnica

### Estado: parcial

Lo que ya esta:

- La aplicacion corre con Flask.
- Existen variables para directorios de datos y reportes.
- Hay documentacion tecnica base.
- Hay un `Procfile`.

Lo que falta para considerarlo cerrado:

- Redactar una documentacion final unificada y consistente con el codigo real.
- Confirmar instrucciones de ejecucion local y de despliegue.
- Revisar dependencias para que el entorno sea reproducible.
- Asegurar que la aplicacion arranque sin depender de rutas manuales.
- Agregar una seccion formal de uso de IA, si el curso la exige.

Archivos clave:

- [`docs/DOCUMENTACION_TECNICA.md`](../docs/DOCUMENTACION_TECNICA.md)
- [`README.md`](../README.md)
- [`Procfile`](../Procfile)
- [`src/paths.py`](../src/paths.py)

## Lo que ya esta muy bien alineado

1. El proyecto si responde al enunciado financiero principal.
2. La ETL no depende de librerias prohibidas para la descarga principal.
3. Los algoritmos de similitud estan implementados de forma explicita.
4. El dashboard ya produce resultados visibles y reutilizables.
5. El PDF consolida analisis numerico y visual.

## Lo que impide decir "100%" sin matices

1. La documentacion no estaba completamente sincronizada con el codigo real.
2. El alcance de despliegue necesita una version final mas formal.
3. El portafolio por defecto debe verificarse para asegurar que realmente cumple el minimo de activos exigido en la entrega.
4. El horizonte historico debe quedar validado con evidencia clara.
5. La parte de ordenamiento existe, pero sigue como linea experimental separada y no como parte del flujo principal del dashboard.

## Lo que falta para cerrar al 100%

### Pendientes de alto impacto

1. Validar y fijar el portafolio final de activos.
2. Revisar y ajustar el rango historico de descarga.
3. Unificar la documentacion tecnica y el README con el estado real del sistema.
4. Dejar una evidencia de ejecucion completa del ETL, analisis, graficas y PDF.
5. Decidir si la linea de ordenamiento se integra al producto final o se deja como anexo experimental.

### Pendientes de calidad de entrega

1. Mejorar redaccion academica de los documentos.
2. Ordenar mejor la narrativa de requerimientos y resultados.
3. Refinar la interfaz para que la demo sea mas clara.
4. Verificar que los nombres de rutas, simbolos y salidas coincidan entre codigo y documentos.

## Orden recomendado de trabajo

### Fase 1. Cerrar brechas funcionales

- Confirmar activos y cobertura historica.
- Revisar el dataset maestro final.
- Validar que los endpoints devuelvan resultados consistentes.

### Fase 2. Cerrar brechas documentales

- Actualizar documentacion tecnica.
- Alinear README con el codigo.
- Escribir la declaracion de uso de IA si aplica.

### Fase 3. Cerrar brechas de entrega

- Revisar despliegue.
- Probar ejecucion limpia.
- Generar evidencia final de PDF y graficas.

## Estado por archivo

### Ya estan aportando al objetivo

- [`src/extraccion_datos.py`](../src/extraccion_datos.py): ETL y dataset maestro.
- [`src/analisis_financiero.py`](../src/analisis_financiero.py): similitud, patrones, riesgo y correlacion.
- [`src/visualizacion.py`](../src/visualizacion.py): graficas.
- [`src/reporte_pdf.py`](../src/reporte_pdf.py): reporte tecnico.
- [`src/api.py`](../src/api.py): API Flask y endpoints.
- [`src/paths.py`](../src/paths.py): rutas seguras y configurables.

### Deben revisarse antes de entrega

- [`docs/DOCUMENTACION_TECNICA.md`](../docs/DOCUMENTACION_TECNICA.md): debe quedar sincronizado con el codigo.
- [`README.md`](../README.md): debe reflejar el estado final.
- [`experiments/ordenamiento.py`](../experiments/ordenamiento.py): decidir si se integra como modulo formal o se deja como anexo.

## Conclusiones

Hoy el proyecto si esta bien alineado con el **proyecto principal de analisis financiero**.

Lo que falta no es tanto construir todo de nuevo, sino cerrar tres cosas:

- validar cobertura real de activos y tiempo historico,
- dejar la documentacion 100% consistente,
- y definir el papel final del bloque de ordenamiento.

Si hacen esos ajustes, ya se puede decir con mucha mas seguridad que el proyecto esta listo para entrega final.
