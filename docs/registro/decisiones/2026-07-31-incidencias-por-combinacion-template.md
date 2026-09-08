# Agrupación de incidencias por combinación de template

Fecha: 2026-07-31

## Decisión

Cada incidencia conserva la clave estructurada de condiciones evaluadas y una `clave_abierta` única mientras su estado es Pendiente o En análisis. Esto permite agrupar nuevos reportes de la misma combinación sin depender de restricciones únicas condicionales, que MySQL no implementa.

Al marcar una incidencia como Resuelta o Descartada, su `clave_abierta` queda vacía. Un reporte posterior crea una nueva incidencia y enlaza la incidencia anterior, preservando la historia de reincidencias.

## Consecuencias

- Un doble reporte del mismo caso no incrementa la cantidad de casos.
- Un caso distinto de la misma combinación se agrega a la incidencia abierta.
- El buzón es operativo: registra estado y observaciones, sin mensajes, notificaciones ni respuestas automáticas.
