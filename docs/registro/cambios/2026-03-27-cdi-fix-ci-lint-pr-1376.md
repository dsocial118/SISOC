# Fix CI PR 1376 en CDI

## Contexto

El refactor grande del módulo `centrodeinfancia` dejó el formulario CDI funcional, pero introdujo fallas de CI en los jobs de lint del PR `#1376`.

## Causa raíz

- `black`: había archivos Python del módulo CDI sin formatear luego del refactor.
- `djlint`: quedaron templates con diferencias de formato y finales de archivo inconsistentes.
- `pylint`: `centrodeinfancia/formulario_cdi_schema.py` concentraba estructura y catálogo textual en un solo módulo, lo que generó:
  - `too-many-lines`
  - múltiples `line-too-long`
- `pylint`: `MezclaEtiquetaFilaFija` disparaba `no-member` por la herencia mixta con `forms.ModelForm`.
- Además, había mezcla de finales de línea `LF/CRLF` en archivos editados durante el ajuste.

## Cambios aplicados

- Se corrió `black` sobre `centrodeinfancia` y `audittrail`.
- Se reformataron los templates de `centrodeinfancia` con `djlint`.
- Se extrajo el catálogo textual del formulario CDI a `centrodeinfancia/formulario_cdi_textos.py`.
- `centrodeinfancia/formulario_cdi_schema.py` quedó nuevamente enfocado en la estructura del formulario y en la composición de opciones/etiquetas.
- El campo `estado_botiquin_primeros_auxilios` volvió a construirse desde códigos + catálogo textual centralizado.
- Se ajustó `MezclaEtiquetaFilaFija` para evitar falsos positivos de `pylint`.
- Se normalizaron finales de línea en los archivos afectados.

## Validación ejecutada

- `docker compose exec django black --check centrodeinfancia audittrail --config pyproject.toml`
- `docker compose exec django djlint centrodeinfancia/templates --check --configuration=.djlintrc`
- `docker compose exec django pylint centrodeinfancia/*.py audittrail/*.py --rcfile=.pylintrc`
- `docker compose exec django python manage.py check`
- `docker compose exec django python manage.py makemigrations centrodeinfancia --dry-run --noinput`
- `docker compose exec django pytest -q centrodeinfancia/tests/test_formulario_cdi_form.py centrodeinfancia/tests/test_formulario_cdi_views.py`

## Resultado

Los checks de lint reproducidos localmente quedaron en verde y no se detectaron regresiones del módulo CDI ni drift de migraciones en `centrodeinfancia`.
