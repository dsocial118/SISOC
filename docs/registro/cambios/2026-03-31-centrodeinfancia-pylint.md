# 2026-03-31 - Ajuste de pylint en `centrodeinfancia`

## Cambios
- Se extrajeron modelos de relaciones de formulario CDI a `centrodeinfancia/models_cdi_relaciones.py` para reducir el tamaño de `centrodeinfancia/models.py`.
- Se simplificó `_configurar_grupo_geo()` en `centrodeinfancia/forms_formulario_cdi.py` para bajar la cantidad de variables locales.

## Motivo
- Resolver los avisos de pylint `too-many-locals` y `too-many-lines` sin cambiar el comportamiento del formulario ni los imports públicos de la app.

## Riesgo
- Bajo. El cambio es estructural y conserva los nombres exportados por `centrodeinfancia.models`.
