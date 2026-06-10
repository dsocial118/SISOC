# 2026-06-10 - Saneamiento de CI para el predeploy (PR #1872)

> Landeado en `development` vía PR #1884. Este registro documenta el saneamiento.

## Resumen
- El PR de predeploy `development -> main` (#1872) tenía en rojo los jobs `pytest`, `black`, `pylint`, `autofix` y `djlint`.
- Este cambio sanea esos fallos en `development` sin tocar la lógica de negocio: arregla tests desactualizados, formatea con black, limpia mensajes de pylint y corrige un bug del workflow de djlint.
- El job `autofix` no podía auto-corregir el formato porque `development` está protegido y rechaza el push del bot; por eso el formateo se aplica manualmente acá.

## Cambios realizados

### Tests (13 fallos heredados)
El job `pytest` solo corre en PRs (no en push), por lo que estos tests se mergearon rotos a `development` sin detectarse.

- `tests/test_pwa_actividades_api.py`: el endpoint de actividades sólo aplica a comedores PNUD (`_get_pnud_scoped_comedor_or_404` devuelve 404 si no lo es). El fixture `comedor` ahora crea un `Programas` con nombre "PNUD" para que las pruebas lleguen a la vista.
- `tests/test_pwa_actividades_models.py`: el assert del seed esperaba `Cultura / Taller de pintura`; se alinea con el catálogo real sembrado por la migración `0017` (`Culturales y/o artísticas / Taller de pintura/dibujo`).
- `tests/test_nomina_views_unit.py`: `NominaDetailView` ahora calcula `is_pnud_comedor(admision.comedor)` y pasa `nomina_tab` a `get_nomina_detail`. El test usa un comedor stub no-PNUD (`programa_id=None`), verifica `mostrar_tabs_nomina is False` y actualiza la aserción de la llamada para incluir `nomina_tab="todas"`.
- `tests/test_relevamientos_web_views_unit.py`: el listado agrega `sincronizado_gestionar` a cada item; se agrega el atributo a los stubs y a las aserciones.
- `VAT/tests.py`:
  - `..._centro_update`: se usa un CUE válido de 9 dígitos (el campo `codigo` queda bloqueado/re-inyectado desde la instancia para INET_PROVINCIA y el form exige 9 caracteres) y se envía un referente válido (el form ahora exige al menos uno).
  - `..._comision_update`: la oferta "tampered" usa `ciclo_lectivo=2025` para no chocar con el `unique(centro, plan_curricular, ciclo_lectivo)` de `OfertaInstitucional`.

### Formato (black)
- `centrodefamilia/admin.py`, `ciudadanos/admin.py`, `comedores/admin.py`, `core/admin.py`, `users/admin.py`: reformateo automático (sólo formato, sin cambios de lógica). Esto además destraba el job `autofix`, que no puede pushear el autoformato a `development` por branch protection.

### Lint (pylint)
- `VAT/urls.py` y `celiaquia/models.py`: `# pylint: disable=too-many-lines` (convención ya usada en el repo).
- `config/settings_preview.py`: `# pylint: disable=wildcard-import,unused-wildcard-import` en el `from config.settings import *` (patrón estándar de settings override).

### Seguridad (CSP)
- `comedores/templates/comedor/actividades_pnud_form.html`: el `<script>` inline ahora incluye `nonce="{{ request.csp_nonce }}"` (lo exige `test_all_inline_script_tags_have_nonce`).

### CI (djlint)
- `.github/workflows/lint.yml`: se quita el flag `--workers` del job `djlint --check` (djlint 1.34.2 no lo soporta → `No such option '--workers'`, exit 2 → el job falla en cualquier PR con templates cambiados). El fix previo `78ee17512` sólo lo había quitado del paso `autofix`/`--reformat`, no del job `--check`.

## Validación local (Docker, SQLite, igual que CI)
- `pytest -n auto`: 2797 passed, 8 skipped, 0 failed.
- `black --check`: sin drift en los archivos tocados.
- `pylint **/*.py --rcfile=.pylintrc`: 10.00/10, exit 0.
- `djlint --check` del template editado: sin cambios.
- CI del PR #1884 confirmada: 14/14 checks en verde.
