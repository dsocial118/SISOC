# CDI: corrección de texto en opciones de botiquín

Fecha: 2026-03-27

## Contexto

Se detectó que en el desplegable **Existencia de Botiquín** seguía apareciendo el texto corto
`Completo todas salas ok vigente fuera alcance` en lugar del texto largo definido en la matriz.

## Cambios aplicados

- Se actualizaron las opciones de `first_aid_kit_status` en
  `centrodeinfancia/formulario_cdi_schema.py` para usar directamente los textos largos finales.
- Se ajustó la etiqueta del campo a `Existencia de Botiquín` en `FIELD_LABELS`.
- Se agregó test de regresión:
  `test_formulario_cdi_opciones_botiquin_muestran_texto_largo`
  en `centrodeinfancia/tests/test_formulario_cdi_form.py`.
- Se normalizaron expectativas de tests con acentos válidos (UTF-8) para evitar falsas fallas por mojibake.

## Validación

- `docker compose exec django pytest -q centrodeinfancia/tests/test_formulario_cdi_form.py`
  - Resultado: `9 passed`
