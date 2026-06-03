# 2026-06-01 - Tests de nómina PWA robustos al borde de mes

## Contexto

Tres tests de `tests/test_pwa_nomina_api.py` dependían del día real de
ejecución y fallaban según la fecha:

- `test_nomina_list_includes_monthly_attendance_history`
- `test_nomina_register_attendance_current_month_is_idempotent`
- `test_nomina_bulk_attendance_alimentaria_syncs_current_period`

Solo es un cambio de **tests**: no se modifica comportamiento de producto
(`pwa/` queda intacto).

## Causa raíz

El "período mensual actual" y la habilitación de la carga de asistencia derivan
de `timezone.localdate()` en `pwa/services/nomina_service.py`:

- `get_periodo_mensual_actual()` ya quedó simplificado a
  `timezone.localdate().replace(day=1)` (commit `190db7aa`), por lo que el
  desfase de período en el borde de mes (días 1-10 apuntando al mes anterior)
  **ya no ocurre**: el test de historial mensual pasa cualquier día.
- Pero `asistencia_nomina_habilitada()` mantiene la ventana de carga real
  (`día >= 25 or día <= 10`). Los endpoints de alta (`registrar-asistencia/`,
  `asistencia-alimentaria/`) llaman a `validar_asistencia_nomina_habilitada()`,
  así que **entre el día 11 y el 24 devuelven `400`** y los dos tests que hacen
  `POST` fallaban (`assert 400 == 200`).

Verificado empíricamente congelando `timezone.localdate` al día 15: el test de
historial pasa, pero los dos `POST` fallan con `400`.

## Decisión

Arreglar los **tests** (no el código): la ventana cruzada de mes es
comportamiento intencional del producto, no un bug. Construir fechas relativas
no alcanza porque no abre la ventana; hay que controlar "hoy".

No hay `freezegun`/`time_machine` en `requirements/`, así que se usa el patrón
ya establecido en el repo con `pytest-mock`: una fixture `fecha_fija_en_ventana`
que parchea `django.utils.timezone.localdate` a una fecha fija **día 1**
(`2026-06-01`).

El día 1 mantiene la ventana abierta (`día <= 10`) y, además, reproduce el borde
de mes: si alguien reintrodujera el cálculo de período desfasado de los primeros
días, el test de historial volvería a romper (sirve de guarda de regresión).

## Cambios aplicados

- `tests/test_pwa_nomina_api.py`:
  - Nueva constante `_FECHA_FIJA_VENTANA = date(2026, 6, 1)` + fixture
    `fecha_fija_en_ventana` (parchea `timezone.localdate`).
  - Se inyecta la fixture en los 3 tests afectados. Los cuerpos no cambian: las
    expresiones `timezone.localdate().replace(day=1)` ahora resuelven a la fecha
    congelada de forma determinista.

## Validación

- `black --check tests/test_pwa_nomina_api.py`: OK.
- Imagen Docker del repo con `USE_SQLITE_FOR_TESTS=1` y `--no-migrations`
  (SQLite):
  - `tests/test_pwa_nomina_api.py`: **10 passed** (con la fecha fija en día 1).
  - Resto de la suite PWA (`test_pwa_actividades_*`, `auditoria_auth`,
    `colaboradores`, `comedores`, `formacion`, `mensajes`, `push`,
    `signals_unit`): **71 passed**.
  - Demostración previa con la fecha fija en día 15 (ventana cerrada): el test de
    historial pasa y los dos `POST` fallan con `400`, confirmando la causa raíz.
- La corrida con migraciones queda delegada a la CI del PR.
