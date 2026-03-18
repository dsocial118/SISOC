# Fix render de listado de expedientes de Celiaquía

## Contexto

Se detectó un error de render en `/celiaquia/expedientes/` asociado a checks de roles dentro del template.

## Cambio aplicado

- Se movieron al `ExpedienteListView` flags explícitas de rol/visibilidad para que el template no dependa de lógica legacy de grupos.
- `celiaquia/templates/celiaquia/expediente_list.html` ahora usa flags de contexto para título, columna de técnicos y acciones visibles.
- Se agregó un test de regresión que valida que el listado renderiza correctamente con el permiso `celiaquia.view_expediente`.

## Motivo

El patrón actual del repo para IAM es por permisos Django, no por `has_group`. Centralizar estas decisiones en la view reduce el riesgo de errores de compilación en templates y evita reintroducir helpers legacy.
