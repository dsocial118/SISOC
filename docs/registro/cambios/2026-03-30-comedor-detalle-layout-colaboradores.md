# Ajuste de layout en detalle de comedor

## Fecha
- 2026-03-30

## Contexto
- El detalle de `comedor` mostraba la UI rota debajo de la línea de tiempo/admisión.
- La tarjeta de resumen "Número de Convenio" había quedado envolviendo bloques completos del detalle por un merge incorrecto en `comedores/templates/comedor/comedor_detail.html`.

## Cambio realizado
- Se restauró la fila superior de cuatro métricas para que "Número de Convenio" vuelva a renderizarse como tarjeta compacta.
- Se reubicó la tabla de "Colaboradores del espacio" dentro del cuerpo del detalle, después del bloque central y antes de las pestañas de intervenciones/observaciones.
- Se eliminó del header roto el bloque accidental que estaba absorbiendo contenido de observaciones y se recuperó la estructura original de filas/columnas.

## Impacto esperado
- El detalle vuelve a respetar la grilla previa.
- Los bloques de nómina, observaciones e intervenciones dejan de apilarse dentro de una cuarta columna estrecha.
