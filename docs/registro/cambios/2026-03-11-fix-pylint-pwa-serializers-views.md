# Fix pylint en serializers y views PWA

Fecha: 2026-03-11

## Contexto

Se corrigieron advertencias de `pylint` en `pwa/api_serializers.py` y `pwa/api_views.py` para recuperar score `10.00/10` sin cambios funcionales del dominio.

## Cambios realizados

1. `pwa/api_serializers.py`
- Se reordenaron imports para respetar `wrong-import-order`.
- Se eliminó import no usado de `NominaEspacioPWA`.
- Se agregaron métodos `create` y `update` en:
  - `NominaEspacioPWACreateUpdateSerializer`
  - `NominaRenaperPreviewSerializer`
  Ambos métodos levantan `NotImplementedError` para explicitar que son serializers de validación de entrada y evitar `abstract-method`.

2. `pwa/api_views.py`
- Se agruparon imports de `core.models` en una sola sentencia (`Dia, Sexo`) para cumplir `ungrouped-imports`.
- Se refactorizó `preview_dni` extrayendo helpers privados:
  - `_renaper_unavailable_message`
  - `_serialize_ciudadano_local`
  - `_normalize_renaper_error_message`
  - `_resolve_sexo_label`
  - `_serialize_renaper_data`
- El refactor reduce complejidad de método (`too-many-locals`, `too-many-branches`) sin cambiar contrato de respuesta.

## Validación ejecutada

```bash
PYLINTHOME=/tmp/pylint-cache pylint pwa/api_serializers.py pwa/api_views.py --rcfile=.pylintrc
```

Resultado:
- `Your code has been rated at 10.00/10`
