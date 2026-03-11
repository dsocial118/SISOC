# 2026-03-12 - Fix CI pytest: seed de catálogo PWA en tests con SQLite

## Resumen

Se corrigió una regresión de CI en tests PWA: el catálogo inicial de actividades quedaba vacío cuando los tests corrían con SQLite y `TEST.MIGRATE=False`.

## Causa raíz

- `CatalogoActividadPWA` se poblaba solo por `RunPython` en la migración `pwa/0005_actividades_pwa.py`.
- En tests con `USE_SQLITE_FOR_TESTS=1`, la configuración usa `TEST.MIGRATE=False`, por lo que ese `RunPython` no se ejecuta.
- Resultado: `CatalogoActividadPWA` vacío, `catalogo_actividad_id=None` y fallos de integridad/not-null en tests API/nomina PWA.

## Cambios implementados

- `pwa/catalogo_seed.py`
  - nuevo bootstrap idempotente `bootstrap_catalogo_actividades(...)` con el catálogo inicial.
- `pwa/apps.py`
  - se conecta `post_migrate` en `PwaConfig.ready()` para ejecutar el bootstrap también en setups sin migraciones.
- `pwa/signals.py`
  - handler `seed_catalogo_actividades(...)` que delega al bootstrap.
- `tests/test_pwa_actividades_api.py`
  - ajuste de dos tests para crear `Nomina` con `admision` (contrato real del modelo) en lugar de `comedor`.

## Validación ejecutada

Comando:

```bash
docker compose exec -T -e USE_SQLITE_FOR_TESTS=1 django pytest -q tests/test_pwa_actividades_models.py tests/test_pwa_actividades_api.py tests/test_pwa_nomina_api.py
```

Resultado:

- `12 passed`

## Impacto

- Mantiene compatibilidad con migraciones existentes.
- Alinea el comportamiento de seed entre DB creada con migraciones y DB de tests creada sin migraciones.
