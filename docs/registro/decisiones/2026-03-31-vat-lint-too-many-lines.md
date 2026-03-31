# 2026-03-31 - Mantener `too-many-lines` suprimido en VAT mientras se corrigen avisos locales

## Estado

- aceptada

## Contexto

`VAT/forms.py` y `VAT/models.py` siguen siendo módulos legacy muy grandes. Para
reducir el riesgo de un cambio amplio solo por lint, se prefirió resolver los
avisos locales reales y dejar una supresión acotada para el límite de líneas
del módulo.

## Decisión

- Mantener `# pylint: disable=too-many-lines` en `VAT/forms.py` y
  `VAT/models.py`.
- Corregir los avisos locales asociados:
  - `can_delete` en el formset,
  - reimport de `Centro`,
  - reimport de `re` / redefinición de `re`.

## Consecuencias

- Se eliminan los errores de `pylint` reportados sin forzar una refactorización
  masiva.
- Queda deuda técnica explícita para una eventual partición futura de los
  módulos VAT.

## Referencias

- `VAT/forms.py`
- `VAT/models.py`
