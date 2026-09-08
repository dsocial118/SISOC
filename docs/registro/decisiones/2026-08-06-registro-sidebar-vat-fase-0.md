# 2026-08-06 - Registro de acceso de sidebar para VAT

## Contexto

El template tag global `is_vat_sidebar_only` importaba la regla de alcance de
VAT en tiempo de ejecucion. Eso acoplaba `core` con una app de dominio para
resolver una opcion de navegacion compartida.

## Decision

Se agrega `core.services.sidebar_access` como un registro minimo de predicados
de sidebar. VAT conserva la implementacion de `es_usuario_solo_vat` y la
registra durante `VATConfig.ready()`.

## Consecuencias

- El template tag mantiene su nombre y resultado visible.
- `core` ya no importa `VAT.services.access_scope`.
- Se retira una excepcion runtime de `.importlinter`.
- El registro es idempotente y no consulta datos durante el arranque.

## Validacion

- `black --check core/services/sidebar_access.py VAT/sidebar_access.py VAT/apps.py core/templatetags/custom_filters.py tests/test_vat_sidebar_access_unit.py`.
- `pytest tests/test_vat_sidebar_access_unit.py -q`.
- `python manage.py check`.
- `lint-imports`.
