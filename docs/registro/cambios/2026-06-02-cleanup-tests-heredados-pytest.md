# 2026-06-02 — Cleanup de tests heredados que dejaban `pytest` en rojo en `development`

Rama: `chore/cleanup-tests-heredados-pytest` (base: `development`)

## Contexto

El job `pytest` de la CI estaba ROJO en `development` con 7 fallos que **no**
pertenecían a ningún PR de feature: eran tests desactualizados respecto de código ya
mergeado (Issue #1799) y un test con fecha hardcodeada que venció con el paso del
tiempo. Como el job `pytest` solo corre en `pull_request` (no en `push` a
`development`), estos tests se mergearon rotos y reaparecían en **cualquier** PR
abierto contra `development` (p.ej. #1822, #1823), bloqueando el deploy guard.

Triaje (confirmado corriendo la suite completa): los 7 son **tests viejos**, no
regresiones de producción. No se tocó lógica de negocio.

## Cambios aplicados

Solo archivos de test (+ este registro).

### `tests/test_admisiones_service_helpers_unit.py`

- `test_actualizar_numero_gde_ajax_validations`: el mock `SimpleNamespace` del
  `archivo` no tenía `archivo_organizacion_origen_id`. La producción
  (`AdmisionService.actualizar_numero_gde_ajax`) consulta ese atributo desde
  **#1799 Req 3** (commit `fbbe2976`) para bloquear la edición del GDE de documentos de
  origen organizacional; al faltar saltaba `AttributeError`, se lo capturaba el
  `try/except` del método y `success` quedaba `False`. Fix: agregar
  `archivo_organizacion_origen_id=None` al mock.
- `test_contextos_create_admision_y_instancia_paths`: `create_admision` llama a
  `congelar_documentacion_organizacional` (#1605) y, desde **#1799 Req 1**
  (commit `3b6de805`), también a `refrescar_snapshot_documentacion_organizacional`.
  Este último lee `admision.pk` directamente (`congelar_*` no fallaba porque usa
  `getattr` y corta temprano si la admisión mock no tiene `comedor`/`organizacion`).
  El objeto devuelto por el mock de `Admision.objects.create` era
  `SimpleNamespace(id=99)` sin `pk` → `AttributeError` → `create_admision` devolvía
  `None`. Fix: mockear ambos helpers (igual que el test vecino
  `test_get_admision_update_context_*` ya mockea `congelar_*`), aislando la
  orquestación de `create_admision` de la lógica de snapshot/freeze, que tiene sus
  propios tests.

### `VAT/tests.py`

- Helper `_step1_data` del wizard de comisión de curso: tenía
  `info-fecha_inicio = "2026-06-01"` hardcodeado (introducido el 2026-05-26, commit
  `0b16e237`, cuando era fecha futura). `ComisionCursoWizardStep1Form.clean()` exige
  `fecha_inicio >= hoy`; al pasar el 2026-06-01 la fecha quedó en el pasado, el paso 1
  dejó de validar y el wizard quedaba atascado en el step `info`. Eso rompía los 5
  tests que dependen de avanzar de step: `test_wizard_step2_duracion_menor_45min_es_rechazada`,
  `test_wizard_step2_duracion_mayor_4h_es_rechazada`,
  `test_wizard_step2_total_semanal_menor_2h_es_rechazado`,
  `test_wizard_step2_dias_duplicados_son_rechazados` y
  `test_wizard_flujo_completo_crea_comision_y_horario` (los AttributeError
  `'ComisionCursoWizardStep1Form' object has no attribute 'forms'/'non_form_errors'` y
  el `assert 'info' == 'horarios'` eran síntomas de eso). Fix: derivar
  `fecha_inicio = timezone.localdate() + 1 día` y `fecha_fin = fecha_inicio + 180 días`
  (imports `timedelta` y `django.utils.timezone`), eliminando la dependencia del reloj.
  Los tests vecinos que prueban fechas inválidas (`..._fecha_inicio_pasada`,
  `..._fecha_fin_igual_a_inicio`) ya sobreescriben las fechas y siguen pasando.

## Impacto esperado

- Ningún cambio de comportamiento de producción (cambios solo en tests).
- El job `pytest` pasa de 7 fallos a 0.

## Validación

Docker one-off contra el checkout, SQLite en memoria con migraciones (igual que el job
`pytest` de CI: `USE_SQLITE_FOR_TESTS=1`), `pytest -n auto`:

- Baseline (sin fix): `7 failed, 2558 passed, 1 skipped` — exactamente los 7 reportados
  por CI, ni uno más.
- Post-fix (suite completa): `2565 passed, 1 skipped, 0 failed` (exit 0).
- `python -m black --check` sobre los dos archivos tocados → limpio.

## Riesgos y rollback

- Riesgo a nivel producto: nulo (no se tocó código de producción).
- `_step1_data` ahora depende de `timezone.localdate()`; si en el futuro se agrega una
  validación de duración máxima entre `fecha_inicio` y `fecha_fin`, revisar el offset de
  180 días.
- Rollback: revertir el commit del PR.
