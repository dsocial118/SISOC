# 2026-06-03 - Cleanup: tests de celiaquía rotos por el scope territorial (#1793)

## Contexto

El commit `31ed6d93` (`fix(celiaquia): aisla expedientes por provincia en carga y listado (#1793)`, 2026-06-02, ya en `development`) endureció el scope de expedientes: removió `include_own` de `_apply_provincial_expediente_scope` e introdujo `_get_provincial_expediente_or_404`. Dejó **2 tests desactualizados** que el job `pytest` (solo en PRs) recién flagueó al abrir un PR nuevo (deuda heredada, no causada por el PR que la expone — ver [[reference-sisoc-validation]]).

El código de producción es **correcto**; los tests no se habían adaptado al nuevo comportamiento.

## Fallas y fix

1. **`celiaquia/tests/test_expediente_detail.py::test_expediente_detail_expone_motivo_rechazo_para_provincia`**
   — fallaba con `assert 404 == 200`. El usuario provincial (Buenos Aires) ya no ve el
   expediente porque su único ciudadano no tenía provincia, y el nuevo scope exige que
   al menos un ciudadano caiga dentro del alcance. **Fix:** el `Ciudadano` del legajo se
   crea con `provincia=provincia` (la del usuario), reflejando el comportamiento real.

2. **`tests/test_celiaquia_expediente_view_helpers_unit.py::test_reprocesar_registros_erroneos_convierte_conflicto_en_excluido`**
   — fallaba con `TypeError: Field 'id' expected a number but got namespace()`. El test
   mockeaba `get_object_or_404`, pero la rama provincial de `ReprocesarRegistrosErroneosView.post`
   ahora resuelve el expediente con `_get_provincial_expediente_or_404`, que aplica
   `.filter(usuario_provincia=user)` sobre el `SimpleNamespace` de prueba. **Fix:** se
   mockea también `_get_provincial_expediente_or_404` para devolver el expediente simulado.

## Validación

- `pytest celiaquia/tests/test_expediente_detail.py tests/test_celiaquia_expediente_view_helpers_unit.py`: **36 passed** (Docker one-off, SQLite, `--no-migrations`). Antes: 2 failed / 34 passed.
- `black`: sin cambios. `pylint`: exit 0 (sin mensajes).
- Cambio **solo de tests**; sin tocar código de producción, modelos ni migraciones.
