# Ajustes de nomenclatura y validación en módulo CDI

## Fecha
- 2026-03-26

## Contexto
- Se solicitó unificar la referencia textual de "Centro(s) de Infancia" hacia "Centro(s) de Desarrollo Infantil" en el módulo CDI.
- En el formulario de alta/edición de centro se necesitaba Select2 en el campo organización.
- Se reportó inconsistencia visual al revalidar campos obligatorios durante edición.

## Cambios implementados
- Se actualizaron textos visibles del módulo CDI (títulos, breadcrumbs, listados y mensajes) para usar "Centro(s) de Desarrollo Infantil".
- Se actualizaron `verbose_name` y `verbose_name_plural` en los modelos de CDI para reflejar la nueva denominación.
- Se agregó migración `0014_update_verbose_names_centros_desarrollo_infantil.py` para mantener consistencia con `makemigrations --check`.
- En `centrodeinfancia_form.html`:
  - Se inicializa Select2 directamente para `organizacion`.
  - Se agregó validación de campos requeridos en submit/input/change para mantener el marcado visual de error también en edición.
  - Se agregó marcado de error visual para el contenedor Select2 cuando el campo obligatorio está vacío.

## Validación
- Se agregó test de regresión en `centrodeinfancia/tests/test_centrodeinfancia_form.py` para asegurar que el campo obligatorio `nombre` sigue validándose también en edición.
