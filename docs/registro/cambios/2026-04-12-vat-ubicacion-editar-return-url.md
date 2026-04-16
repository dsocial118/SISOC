# Fix edición de ubicación VAT

Fecha: 2026-04-12

## Qué cambió

- Se corrigió el template `vat/institucion/ubicacion_form.html` para que los botones de volver y cancelar usen `return_url` cuando la vista lo provee.
- Si `return_url` no está presente, el template ahora resuelve el fallback directamente con `{% url 'vat_institucion_ubicacion_list' %}`.

## Problema resuelto

- La pantalla `/vat/institucion/ubicaciones/<pk>/editar/` podía fallar con `VariableDoesNotExist` al intentar renderizar `ubicacion_list_url` sin haberla definido.

## Decisión

- Se mantuvo la navegación especial de la edición hacia el detalle del centro y se eliminó la dependencia del template a una variable auxiliar implícita.
