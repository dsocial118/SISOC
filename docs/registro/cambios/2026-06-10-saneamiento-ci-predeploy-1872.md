# 2026-06-10 - Saneamiento de CI para el predeploy (PR #1872)

## Resumen
- El PR de predeploy `development -> main` (#1872) tenía en rojo los jobs `pytest`, `black` y `pylint`.
- Este cambio sanea esos fallos en `development` sin tocar la lógica de negocio: arregla tests desactualizados, formatea con black y limpia mensajes de pylint.
- El job `autofix` no podía auto-corregir el formato porque `development` está protegido y rechaza el push del bot; por eso el formateo se aplica manualmente acá.

## Cambios realizados

### Tests (13 fallos heredados)
- `tests/test_pwa_actividades_api.py`: el endpoint de actividades sólo aplica a comedores PNUD (`_get_pnud_scoped_comedor_or_404` devuelve 404 si no lo es). El fixture `comedor` ahora crea un `Programas` con nombre "PNUD" para que las pruebas lleguen a la vista.
- `tests/test_pwa_actividades_models.py`: el assert del seed esperaba `Cultura / Taller de pintura`; se alinea con el catálogo real sembrado por la migración `0017` (`Culturales y/o artísticas / Taller de pintura/dibujo`).
- `tests/test_nomina_views_unit.py`: `NominaDetailView` ahora calcula `is_pnud_comedor(admision.comedor)` y pasa `nomina_tab` a `get_nomina_detail`. El test mockea `is_pnud_comedor` y actualiza la aserción de la llamada.
- `tests/test_relevamientos_web_views_unit.py`: el listado agrega `sincronizado_gestionar` a cada item; se agrega el atributo a los stubs y a las aserciones.
- `VAT/tests.py`:
  - `..._centro_update`: se usa un CUE válido de 9 dígitos (el campo `codigo` queda bloqueado/re-inyectado para INET_PROVINCIA y el form exige 9 numéricos) y se envía un referente válido (el form ahora exige al menos uno).
  - `..._comision_update`: la oferta "tampered" usa `ciclo_lectivo=2027` para no chocar con el `unique(centro, plan_curricular, ciclo_lectivo)` de `OfertaInstitucional`.

### Formato (black)
- `centrodefamilia/admin.py`, `ciudadanos/admin.py`, `comedores/admin.py`, `core/admin.py`, `users/admin.py`: reformateo automático (sólo formato, sin cambios de lógica).

### Lint (pylint)
- `VAT/urls.py` y `celiaquia/models.py`: `# pylint: disable=too-many-lines` (convención ya usada en el repo).
- `config/settings_preview.py`: `# pylint: disable=wildcard-import,unused-wildcard-import` en el `from config.settings import *` (patrón estándar de settings override).

### Seguridad (CSP)
- `comedores/templates/comedor/actividades_pnud_form.html`: el `<script>` inline ahora incluye `nonce="{{ request.csp_nonce }}"` (lo exige `test_all_inline_script_tags_have_nonce`).

## Validación local (Docker, SQLite, igual que CI)
- `pytest -n auto`: 2797 passed, 8 skipped, 0 failed.
- `black --check`: sin drift en los archivos tocados.
- `pylint **/*.py --rcfile=.pylintrc`: 10.00/10, exit 0.
- `djlint --check` del template editado: sin cambios.
