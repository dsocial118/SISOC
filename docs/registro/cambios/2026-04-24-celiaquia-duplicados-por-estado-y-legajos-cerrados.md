# Celiaquia: duplicados por estado de legajo y bloqueo de legajos cerrados

Fecha: 2026-04-24

## Contexto

Se ajustaron reglas de negocio de Celiaquia para que:

- la validacion de duplicados entre expedientes dependa del estado del legajo y no del estado del expediente;
- los legajos `APROBADO` y `RECHAZADO` no puedan volver a modificarse;
- la comunicacion al usuario muestre el estado del legajo que bloquea la duplicacion.

Ademas, se extendio ese criterio al modal de edicion de datos del legajo para no dejar una via lateral de modificacion sobre legajos cerrados.

## Cambio realizado

- `celiaquia/services/importacion_service/impl.py`
  - reemplaza la regla de conflicto basada en estados del expediente por una basada en `revision_tecnico`;
  - bloquea duplicados cuando existe otro legajo en `PENDIENTE`, `APROBADO`, `SUBSANAR` o `SUBSANADO`;
  - mantiene permitido el reingreso cuando el antecedente relevante esta en `RECHAZADO`;
  - conserva la logica actual de responsables y el bloqueo por inclusion en programa (`estado_cupo=DENTRO`).
- `celiaquia/views/expediente.py`
  - bloquea nuevas revisiones sobre legajos `APROBADO` o `RECHAZADO`;
  - permite revisar desde `PENDIENTE` y `SUBSANADO`, manteniendo multiples ciclos de subsanacion;
  - ajusta mensajes y previews para mostrar `Estado legajo: ...` en conflictos de duplicacion.
- `celiaquia/views/legajo_editar.py`
  - rechaza `GET` y `POST` del modal de edicion cuando el legajo esta en `APROBADO` o `RECHAZADO`.
- `celiaquia/templates/celiaquia/expediente_detail.html`
  - oculta el boton de editar para legajos cerrados.
- `celiaquia/signals.py`
  - alinea la restauracion de expedientes con la misma regla de conflicto por estado de legajo.

## Resultado esperado

- un ciudadano con legajo `RECHAZADO` puede volver a integrar un nuevo expediente;
- un ciudadano con legajo `PENDIENTE`, `APROBADO`, `SUBSANAR` o `SUBSANADO` no puede duplicarse en otro expediente;
- los legajos `APROBADO` y `RECHAZADO` no admiten ni revision tecnica adicional ni edicion de datos;
- las alertas de importacion/subsanacion informan el estado del legajo que bloquea la operacion, en lugar del estado del expediente origen.

## Validacion prevista

Pruebas focalizadas dentro de Docker:

```powershell
docker compose -f BACKOFFICE\docker-compose.yml exec -T django pytest celiaquia/tests/test_legajo_editar.py tests/test_celiaquia_expediente_view_helpers_unit.py tests/test_expediente_service_unit.py -q
```
