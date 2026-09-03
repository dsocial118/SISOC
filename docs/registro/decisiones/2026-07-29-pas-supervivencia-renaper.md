# PAS: control diario de supervivencia RENAPER

## Decisión

El padrón PAS se contrasta diariamente con el cliente RENAPER existente mediante
el comando `sincronizar_supervivencia_pas`, programado a las 04:00 en
`scripts/crontab`.

Como `PasPersona` no posee sexo, la consulta prueba `M` y luego `F` únicamente
cuando RENAPER responde sin coincidencia. Los errores técnicos no disparan una
segunda consulta ni se interpretan como incompatibilidad.

## Persistencia e impacto

- Cada persona tiene como máximo un control por fecha.
- Se persiste resultado, sexo utilizado y tipo de error, pero no el payload
  personal completo de RENAPER.
- Una respuesta de fallecimiento crea una incompatibilidad de categoría
  `Supervivencia`, pendiente y efectiva desde el primer día del mes siguiente.
- No se modifica automáticamente el estado del titular. La consecuencia
  administrativa debe resolverse en el flujo de incompatibilidades.
- Reejecutar el comando el mismo día omite controles existentes, salvo que se
  indique `--forzar`.

## Operación

```bash
python manage.py sincronizar_supervivencia_pas
python manage.py sincronizar_supervivencia_pas --fecha 2026-07-29 --limite 20
python manage.py sincronizar_supervivencia_pas --forzar
```

El despliegue debe instalar o sincronizar el crontab del host. Incorporar la
línea al repositorio no modifica por sí solo los crontabs ya instalados.

## Ejecución manual

La pantalla `/pas/cruces` incorpora el botón `Actualizar` en la tarjeta
Supervivencia. La acción requiere `pas.change_paspersona`, confirmación del
operador y ejecuta el mismo servicio con reproceso forzado para la fecha actual.
Al finalizar vuelve a la bandeja y muestra el resumen de personas vivas,
fallecidas, sin coincidencia y errores.
