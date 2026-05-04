# Mobile Convenio Alimentar Comunidad: Prestaciones y Monto Mensual

## Fecha
2026-05-04

## Objetivo
Alinear la card mobile de "Datos del Convenio" para espacios de programa Alimentar Comunidad con los valores de "Prestaciones mensuales" y "Monto prestación mensual" usados en web.

## Alcance
Se expusieron campos explícitos en el payload `datos_convenio_mobile` y se mantuvo compatibilidad con campos existentes.

## Archivos tocados
- comedores/api_serializers.py

## Cambios realizados
- En `_get_datos_convenio_alimentar` se agregaron campos explícitos:
- `prestaciones_mensuales`
- `monto_prestacion_mensual`
- Se conservaron los campos legacy:
- `prestaciones_gescom_total_mensual`
- `monto_total_convenio`
- El cálculo de ambos valores se mantiene sobre la misma fuente (`ComedorService.get_presupuestos`), evitando desalineación entre web y mobile.

## Supuestos
- La app mobile consumirá los nuevos campos explícitos cuando estén presentes.

## Validaciones ejecutadas
- `python -m compileall comedores/api_serializers.py`

## Pendientes / riesgos
- Verificar en entorno funcional que el frontend mobile priorice los campos explícitos en la card de convenio para Alimentar Comunidad.

