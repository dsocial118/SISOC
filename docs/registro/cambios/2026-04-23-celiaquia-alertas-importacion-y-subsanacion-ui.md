# Celiaquia: alertas persistentes y temporales en importacion y subsanacion

Fecha: 2026-04-23

## Contexto

En el detalle de expedientes de Celiaquia, el feedback posterior a la importacion y al reproceso de registros erroneos tenia dos problemas de UX:

- los mensajes mezclaban resumen operativo y detalle de legajos excluidos sin un orden semantico estable;
- los mensajes de exito y warning no respetaban una regla consistente entre primera visualizacion, recarga y reingreso al expediente.

Esto hacia dificil interpretar rapido que parte del resultado era informativa y que parte seguia requiriendo accion o seguimiento.

## Cambio realizado

Se ordeno el render de alertas persistentes del detalle de expediente para separar:

- `resumen` de importacion/reproceso;
- `excluidos` por legajos activos en otros expedientes.

Ademas:

- cuando aplica `PARTE A` y `PARTE B`, el resumen siempre se muestra primero;
- los mensajes de warning persisten mientras el expediente siga en `EN_ESPERA`;
- el mensaje de exito de `PARTE A` se mantiene como alerta temporal reutilizable durante 2 minutos en el navegador, incluyendo recargas y reapertura de la misma pantalla dentro de ese lapso.

## Decision de UX

Se definio esta regla:

- `warning` persistente para informacion de negocio que sigue vigente al reingresar;
- `success` temporal para confirmacion operativa inmediata posterior a importacion o subsanacion;
- orden visual por significado del bloque y no por color del cartel.

Motivo:

- mejorar legibilidad;
- evitar que el usuario pierda el resumen inmediato de exito;
- mantener persistente solo la informacion que sigue siendo relevante hasta el cambio de estado.

## Archivos tocados

- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/views/expediente.py`
- `static/custom/js/expediente_detail.js`
- `static/custom/js/registros_erroneos.js`

## Validacion

Se validaron helpers y services asociados al flujo del detalle de expediente y a la persistencia de alertas:

```powershell
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest tests/test_expediente_service_unit.py -q
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest tests/test_celiaquia_expediente_view_helpers_unit.py -q
```

Resultado:

- `36 passed`

## Impacto esperado

- el usuario ve primero el resumen de importacion/subsanacion;
- los warnings relevantes siguen visibles al volver a entrar al expediente;
- los success de resumen no quedan pegados indefinidamente, pero tampoco desaparecen por una recarga inmediata durante el tiempo definido para pruebas y operacion.
