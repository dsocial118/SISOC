# Cambio: limpieza de `pylint` en Formulario CDI

Fecha: 2026-03-13

## Qué se ajusta
- Se explicita la reexportación pública de `FormularioCDIForm` y helpers en `centrodeinfancia/forms.py`.
- Se separan validaciones internas de `FormularioCDI.clean()` en helpers privados para reducir complejidad sin cambiar reglas.
- Se simplifica `_display_value()` en las vistas de Formulario CDI para evitar retornos múltiples innecesarios.
- Se cachea la obtención de la instancia en edición para evitar que `pylint` infiera retorno fijo `None` en la clase base.

## Impacto funcional
- No cambia el contrato público de vistas ni formularios.
- No se agregan campos, endpoints ni validaciones nuevas.

## Validación prevista
- `pytest` focalizado en `centrodeinfancia/tests/test_formulario_cdi_form.py`
- `pytest` focalizado en `centrodeinfancia/tests/test_formulario_cdi_views.py`
- `pylint` sobre `centrodeinfancia/forms.py`, `centrodeinfancia/models.py` y `centrodeinfancia/views_formulario_cdi.py`
