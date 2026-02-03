# Management commands relevantes

## Core
- `load_fixtures`: carga fixtures en modo upsert (no borra) con opción `--force`. Evidencia: core/management/commands/load_fixtures.py:8-77.
- `generate_webp_images`: genera WebP para ImageFields con opciones de filtro, calidad y estadísticas. Evidencia: core/management/commands/generate_webp_images.py:1-111.
- `debug_queries`: ejecuta depuración de queries para vistas (todas o Ciudadanos). Evidencia: core/management/commands/debug_queries.py:1-33.

## Users
- `create_groups`: crea grupos predeterminados. Evidencia: users/management/commands/create_groups.py:1-61.
- `create_test_users`: genera usuarios de prueba cuando `DEBUG=True`. Evidencia: users/management/commands/create_test_users.py:1-80.
- `import_users_from_csv`: crea/actualiza usuarios replicando grupos desde un usuario de referencia. Evidencia: users/management/commands/import_users_from_csv.py:1-35.
- `assign_provincia_to_test_user`: asigna provincia_id=1 al usuario `ProvinciaCeliaquia`. Evidencia: users/management/commands/assign_provincia_to_test_user.py:1-32.

## Relevamientos
- `import_relevamientos`: importa relevamientos desde CSV respetando signals/validaciones. Evidencia: relevamientos/management/commands/import_relevamientos.py:1-73.
- `delete_relevamientos`: elimina IDs en lotes disparando signals pre_delete/post_delete. Evidencia: relevamientos/management/commands/delete_relevamientos.py:1-61.

## Comedores
- `import_comedores_excel`: alta masiva desde Excel con normalización de estados. Evidencia: comedores/management/commands/import_comedores_excel.py:1-70.
- `update_estados_comedores`: aplica estados desde CSV a historial. Evidencia: comedores/management/commands/update_estados_comedores.py:1-52.
- `reset_validaciones`: resetea validaciones de comedores a Pendiente. Evidencia: comedores/management/commands/reset_validaciones.py:1-14.
- `update_comedores_dupla`: asigna duplas a comedores desde CSV, opcionalmente creando admisiones. Evidencia: comedores/management/commands/update_comedores_dupla.py:1-46.
- `sync_comedores_gestionar`: sincroniza payload completo de comedores contra GESTIONAR (Add/Update, multithread). Evidencia: comedores/management/commands/sync_comedores_gestionar.py:1-94.
- `sync_territoriales_cache`: sincroniza cache de territoriales, con opciones de stats, force y cleanup. Evidencia: comedores/management/commands/sync_territoriales_cache.py:1-117.

## Centro de familia
- `cargar_legajos`: crea ciudadanos/participantes desde Excel. Evidencia: centrodefamilia/management/commands/cargar_legajos.py:1-46.
- `reprocess_cabal`: reprocesa registros CABAL rechazados con confirmación interactiva. Evidencia: centrodefamilia/management/commands/reprocess_cabal.py:1-49.

## Auditoría
- `purge_auditlog`: borra registros de auditlog más antiguos que N días (soporta `--dry-run`). Evidencia: audittrail/management/commands/purge_auditlog.py:1-38.
