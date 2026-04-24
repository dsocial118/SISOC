# Celiaquia: subsanacion valida conflictos con expedientes activos y reduce ruido de logs

Fecha: 2026-04-23

## Problema

El reproceso de registros erroneos en Celiaquia no reutilizaba la misma validacion de importacion para detectar ciudadanos ya presentes en otro expediente activo.

Eso permitia un caso incorrecto:

- la importacion original excluia beneficiarios por conflicto en otro expediente;
- un registro con error se corregia;
- el reproceso podia crear el legajo aunque el ciudadano siguiera en conflicto.

Ademas, el log `No hay legajos para crear - lista vacía` se emitia en nivel `warning`, generando ruido operativo y potencial observabilidad innecesaria.

## Decision

Se reutilizo la misma logica de importacion para validar conflictos durante el reproceso/subsanacion.

Si el ciudadano corregido:

- ya esta dentro del programa en otro expediente, o
- ya pertenece a otro expediente abierto,

entonces el registro deja de tratarse como error y pasa a computarse como `excluido`, igual que en la importacion original.

En paralelo:

- se persiste `excluidos_detalle` dentro de `observaciones` del historial para poder recalcular alertas posteriores;
- se baja el log `No hay legajos para crear - lista vacía` de `warning` a `info`.

Con ese cambio no hace falta configuracion extra para Sentry: al no emitirse como warning, deja de calificar como evento reportable por el esquema actual del proyecto.

## Cambio implementado

- `celiaquia/views/expediente.py`
  - el reproceso precarga conflictos del expediente;
  - valida cada beneficiario corregido con `_beneficiario_tiene_conflicto_importacion(...)`;
  - convierte conflictos en `excluidos_detalle`;
  - actualiza la alerta persistente sumando nuevos excluidos.
- `celiaquia/services/expediente_service/impl.py`
  - guarda `excluidos_detalle` en el payload persistido del historial;
  - centraliza helpers para reconstruir resumen y detalle de excluidos.
- `celiaquia/services/importacion_service/impl.py`
  - reduce a `info` el mensaje `No hay legajos para crear - lista vacía`.

## Resultado funcional

Ejemplo esperado:

- importacion inicial: `0 legajos creados, 1 error, 3 legajos ya existen en otro expediente`
- luego de subsanar el error, si ese beneficiario tambien existe en otro expediente:
  - resultado consolidado: `0 legajos creados, 0 errores, 4 legajos ya existen en otro expediente`

## Testing

Se reforzaron regresiones para cubrir:

- persistencia de `excluidos_detalle` en observaciones de importacion;
- recalculo del payload persistente cuando un error corregido pasa a excluido;
- reproceso que convierte un registro subsanado en excluido por conflicto activo.

Validacion ejecutada:

```powershell
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest tests/test_expediente_service_unit.py -q
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest tests/test_celiaquia_expediente_view_helpers_unit.py -q
```

Resultado:

- `36 passed`

## Riesgo residual

La regla de exclusiones compartida entre importacion y reproceso depende del mismo precargado de conflictos. Si en el futuro cambia la definicion de expediente activo o de inclusion en programa, conviene mantener sincronizada una unica fuente de verdad para ambos flujos.
