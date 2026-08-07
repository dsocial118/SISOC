# 2026-08-06 - Registro de efectos soft delete para VAT

## Contexto

El comando de sincronizacion de soft delete en `core` importaba directamente el
handler de invalidacion de cache de VAT para reprocesar filas legacy.

## Decision

El registro existente de `core.soft_delete` conserva sus modelos y elecciones
de papelera, y suma un registro idempotente de handlers de backfill. VAT aporta
su invalidador de cache durante `AppConfig.ready()`. Cada handler lleva un
nombre estable y se ejecuta en orden lexicográfico, sin depender del orden de
carga de las aplicaciones.

## Consecuencias

- `core.soft_delete.state_sync` deja de importar VAT.
- La invalidacion del cache de planes VAT se mantiene durante el backfill.
- Se retira una excepcion runtime de `.importlinter`.
- No se consultan datos durante el registro de arranque.

## Validacion

- `pytest tests/test_soft_delete_state_sync_command.py tests/test_soft_delete_flows.py -q`.
- `lint-imports`.
