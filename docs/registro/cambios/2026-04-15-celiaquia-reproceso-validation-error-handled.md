# Celiaquia reproceso de registros erroneos: ValidationError handled

Fecha: 2026-04-15

## Que cambio

- En `celiaquia/views/expediente.py`, el reproceso de registros erroneos ahora captura `ValidationError` en un bloque dedicado antes del `except Exception`.
- Los errores de validacion esperables, como `Faltan campos obligatorios: altura`, pasan a registrarse como `warning` con el evento `celiaquia.expediente.reprocess.handled_validation_error`.
- En `celiaquia/services/importacion_service/impl.py`, el registro de errores por fila durante importacion/reproceso deja de usar `logger.error(...)` y pasa a `logger.warning(...)` cuando se persiste el detalle en `detalles_errores`.
- Se mantiene el comportamiento funcional para la UI:
  - el reproceso sigue devolviendo `success: true` cuando el lote termina,
  - los registros invalidos siguen sumando en `errores` y `errores_detalle`,
  - y el detalle queda persistido en `registro.mensaje_error`.
- Se agrego una prueba unitaria de regresion en `tests/test_celiaquia_expediente_view_helpers_unit.py` para verificar que una `ValidationError` del reproceso no se loguea como error inesperado.

## Decision principal

- Se separaron los errores esperables de validacion de los errores inesperados de ejecucion.
- No se cambio la notificacion visible al usuario en la UI.
- No se modifico la regla funcional que exige `altura` en la importacion; solo se ajusto la clasificacion y el tratamiento operativo del error.

## Impacto operativo

- Los faltantes de datos en reproceso dejan de aparecer en `error.log` como fallas tecnicas no manejadas.
- El equipo puede seguir viendo el motivo concreto del rechazo en la tabla de registros erroneos y en `errores_detalle`.
- Los casos esperables de validacion quedan concentrados en `warning.log`.
- Los errores realmente inesperados siguen quedando en `logger.error` para investigacion.

## Validacion prevista

- Intentar reprocesar un registro erroneo que siga sin `altura`.
- Verificar que la UI mantenga el mensaje general actual de reproceso y que el detalle del registro siga mostrando el error.
- Verificar en logs que el caso quede registrado como `warning` bajo `celiaquia.expediente.reprocess.handled_validation_error`.
- Verificar que no aparezca `impl ERROR django: Error fila ...` en `error.log` para ese mismo caso.
- Verificar que no se creen legajos parciales para ese registro.
