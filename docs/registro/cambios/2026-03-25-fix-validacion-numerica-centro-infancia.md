# Fix validación numérica en alta/edición de Centro de Infancia

## Fecha
- 2026-03-25

## Contexto
- En el formulario de creación/edición de `CentroDeInfancia` se aceptaban textos en campos numéricos.
- Además, se necesitaba admitir teléfono como número plano (sin formato con guiones).

## Cambios implementados
- Se agregó validación en `CentroDeInfanciaForm` para:
  - `numero`: solo dígitos.
  - `telefono` y `telefono_referente`: solo números, permitiendo guiones como separadores opcionales.
- Se agregaron atributos de widget para reforzar la UX en el frontend:
  - `numero`: `inputmode="numeric"` y `pattern="\d*"`.
  - `telefono` y `telefono_referente`: `inputmode="numeric"` sin `pattern`, para no bloquear guiones opcionales.

## Impacto funcional
- El formulario rechaza valores con letras, espacios u otros signos no válidos.
- `numero` no admite guiones.
- `telefono` y `telefono_referente` aceptan:
  - número plano (ejemplo: `5491140333588`)
  - número con guiones opcionales (ejemplo: `11-1234-1234`)

## Validación
- Se agregaron tests de regresión en `centrodeinfancia/tests/test_centrodeinfancia_form.py` para:
  - rechazo de texto en campos numéricos,
  - aceptación de teléfono numérico plano.
  - aceptación de teléfono con guiones opcionales.
