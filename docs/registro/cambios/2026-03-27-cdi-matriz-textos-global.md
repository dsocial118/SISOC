# CDI: aplicación global de textos de matriz

Fecha: 2026-03-27

## Contexto

Se detectó que algunos textos actualizados del formulario CDI quedaban sólo en el `Form`,
mientras que otras capas seguían mostrando etiquetas/opciones antiguas.

## Cambios realizados

- Se creó `centrodeinfancia/formulario_cdi_text_overrides.py` como fuente única de:
  - `CHOICE_LABEL_OVERRIDES`
  - `MULTI_CHOICE_LABEL_OVERRIDES`
  - `FIELD_LABEL_OVERRIDES`
- `centrodeinfancia/forms_formulario_cdi.py` ahora importa esos overrides (se eliminó duplicación local).
- `centrodeinfancia/formulario_cdi_schema.py` aplica esos overrides sobre `CHOICE_FIELDS`,
  `MULTI_CHOICE_FIELDS` y `FIELD_LABELS`, para que los textos de matriz queden unificados
  en alta, edición, detalle y usos basados en schema.
- Se agregó test de regresión en `centrodeinfancia/tests/test_formulario_cdi_form.py`
  para validar que el schema también refleja los textos de matriz.

## Validación

- `docker compose exec django pytest -q centrodeinfancia/tests/test_formulario_cdi_form.py`
  - Resultado: `10 passed`
