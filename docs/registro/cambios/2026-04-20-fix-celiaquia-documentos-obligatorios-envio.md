# Fix Celiaquia: documentos obligatorios para confirmar envio

## Problema

En Celiaquia, el flujo de confirmacion de envio del expediente seguia usando la validacion legacy de `archivo2` y `archivo3` para decidir si un legajo tenia la documentacion completa.

Eso dejaba pasar un caso incorrecto:

- `beneficiario_y_responsable` requiere `archivo1`, `archivo2` y `archivo3`
- la confirmacion del expediente solo miraba `archivo2` y `archivo3`
- una provincia podia avanzar con un legajo incompleto

## Decision

Se centralizo la regla de "documentacion completa" en `LegajoService`, reutilizando `get_archivos_requeridos_por_legajo(...)` como fuente de verdad para:

- calcular faltantes por legajo
- recalcular `archivos_ok`
- validar si todos los legajos del expediente estan completos
- bloquear la confirmacion del envio cuando falta al menos un documento obligatorio segun el tipo de ciudadano

## Cambio implementado

- `celiaquia/services/legajo_service/impl.py`
  - agrega helpers para obtener faltantes reales por legajo
  - deja de asumir que siempre alcanza con `archivo2` y `archivo3`
- `celiaquia/services/expediente_service/impl.py`
  - recalcula `archivos_ok` con la regla por tipo de ciudadano antes de confirmar envio
- `celiaquia/views/confirm_envio.py`
  - usa faltantes dinamicos para devolver error de negocio consistente
- `celiaquia/views/expediente.py`
  - alinea `faltan_archivos` con la misma regla centralizada
- `celiaquia/models.py`
  - evita que el `save()` del legajo vuelva a pisar `archivos_ok` con la regla vieja

## Validacion

Se ejecuto:

```powershell
$env:USE_SQLITE_FOR_TESTS='1'
& 'C:\Users\Juanito\Desktop\Repos-Codex\worktrees\bulk-credentials-mail-fallback-user-email\.venv\Scripts\python.exe' -m pytest tests/test_legajo_service_unit.py tests/test_expediente_service_unit.py celiaquia/tests/test_validation_errors.py tests/test_celiaquia_expediente_view_helpers_unit.py -q
```

Resultado:

- `47 passed`

## Supuesto explicitado

Se mantuvo como fuente de verdad el esquema actual basado en `archivo1`/`archivo2`/`archivo3` para este flujo de confirmacion. No se cambio el sistema normalizado de `DocumentoLegajo` ni otros flujos fuera del alcance del envio del expediente.
