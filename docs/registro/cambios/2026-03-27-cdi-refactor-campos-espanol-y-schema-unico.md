# Refactor CDI: campos persistidos en español y consolidación del schema

Fecha: 2026-03-27

## Alcance

Se realizó un refactor integral del módulo `centrodeinfancia` para dejar el formulario CDI con nombres persistidos en español, reducir duplicación interna y normalizar textos visibles en UTF-8.

## Cambios principales

- Se renombraron los campos persistidos de `FormularioCDI` al español mediante migración explícita `0015_refactor_formulario_cdi_campos_en_espanol.py`.
- Se renombraron también campos persistidos de modelos auxiliares del formulario:
  - `FormularioCDIRoomDistribution`
  - `FormularioCDIWaitlistByAgeGroup`
  - `FormularioCDIArticulationFrequency`
- Se renombró `CentroDeInfancia.cdi_code` a `codigo_cdi`.
- Se consolidó la matriz de textos dentro de `formulario_cdi_schema.py` y se eliminó `formulario_cdi_text_overrides.py` para dejar una sola fuente de verdad.
- Se actualizaron forms, vistas, templates, admin y tests del módulo para usar los nuevos nombres.
- Se regeneró la migración de sincronización `0016_alter_formulariocdi_options_and_more.py` para alinear choices, constraints, related names y opciones de modelos.
- Se agregó una corrección de datos en `0016` para mapear el valor histórico `periodica_todas_necesidades_y_patrones_y_personal_capacitado` al nuevo valor `periodica_todas_necesidades_y_patrones_y_personas`.
- Se normalizaron textos con mojibake/encoding roto en `centrodeinfancia` para dejar UI, modelos, forms y tests en UTF-8 consistente.

## Decisiones

- No se renombraron los nombres de modelos Django (`FormularioCDIArticulationFrequency`, etc.) para evitar una migración de `RenameModel` innecesariamente riesgosa en esta fase.
- Sí se renombraron los campos persistidos y los contratos internos del formulario, que era el objetivo principal del refactor.

## Validación

- `docker compose exec django python manage.py check`
- `docker compose exec django pytest -q centrodeinfancia/tests/test_formulario_cdi_form.py centrodeinfancia/tests/test_formulario_cdi_views.py`
- `docker compose exec django python manage.py makemigrations centrodeinfancia --dry-run --noinput`

Resultado:

- `check` sin errores.
- Suite focalizada CDI: `18 passed`.
- Sin drift pendiente de migraciones para `centrodeinfancia`.
