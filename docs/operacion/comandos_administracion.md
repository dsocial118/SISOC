# Management commands relevantes

## Core
- `load_fixtures`: carga fixtures en modo upsert (no borra) con opción `--force` o `--overwrite` para reaplicar datos existentes. Evidencia: core/management/commands/load_fixtures.py:8-77.
- `generate_webp_images`: genera WebP para ImageFields con opciones de filtro, calidad y estadísticas. Evidencia: core/management/commands/generate_webp_images.py:1-111.
- `debug_queries`: ejecuta depuración de queries para vistas (todas o Ciudadanos). Evidencia: core/management/commands/debug_queries.py:1-33.
- `run_benchmarks`: ejecuta benchmarks reproducibles en una DB efímera, serializa resultados JSON y compara contra baseline versionado; soporta `--rebuild-baseline`. Evidencia: core/management/commands/run_benchmarks.py:1-176.
- `load_fixtures`: carga fixtures en modo upsert (no borra) con opcion `--force` o `--overwrite` para reaplicar datos existentes. Evidencia: `core/management/commands/load_fixtures.py`.
- `generate_webp_images`: genera WebP para ImageFields con opciones de filtro, calidad y estadisticas. Evidencia: `core/management/commands/generate_webp_images.py`.
- `debug_queries`: ejecuta depuracion de queries para vistas (todas o Ciudadanos). Evidencia: `core/management/commands/debug_queries.py`.

## Users
- `create_groups`: crea grupos predeterminados y sincroniza permisos bootstrap segun la semilla declarativa de IAM (`users/bootstrap/groups_seed.py`). Evidencia: `users/management/commands/create_groups.py`.
- `sync_group_permissions_from_registry`: sincroniza permisos Django por grupo para grupos ya existentes. Util post-migracion en staging/prod. Evidencia: `users/management/commands/sync_group_permissions_from_registry.py`.
- `create_test_users`: genera usuarios de prueba cuando `DEBUG=True`. Evidencia: `users/management/commands/create_test_users.py`.
- `import_users_from_csv`: crea/actualiza usuarios replicando grupos desde un usuario de referencia. Evidencia: `users/management/commands/import_users_from_csv.py`.
- `assign_provincia_to_test_user`: asigna `provincia_id=1` al usuario `ProvinciaCeliaquia`. Evidencia: `users/management/commands/assign_provincia_to_test_user.py`.

## Relevamientos
- `import_relevamientos`: importa relevamientos desde CSV respetando signals/validaciones. Evidencia: `relevamientos/management/commands/import_relevamientos.py`.
- `delete_relevamientos`: elimina IDs en lotes disparando `pre_delete`/`post_delete`. Evidencia: `relevamientos/management/commands/delete_relevamientos.py`.

## Comedores
- `import_comedores_excel`: alta masiva desde Excel con normalizacion de estados. Evidencia: `comedores/management/commands/import_comedores_excel.py`.
- `validar_comedores_csv`: marca comedores listados en CSV como `Validado` y los lleva a `Activo / En ejecucion`; soporta `--dry-run`. Evidencia: `comedores/management/commands/validar_comedores_csv.py`.
- `update_programa_estado_comedores`: actualiza programa y estado general desde CSV por `comedor_id`, con override de programa/actividad/proceso/detalle y `--dry-run`. Evidencia: `comedores/management/commands/update_programa_estado_comedores.py`.
- `update_estados_comedores`: aplica estados desde CSV a historial. Evidencia: `comedores/management/commands/update_estados_comedores.py`.
- `update_estados_comedores_from_names`: crea historial de estados a partir de CSV con nombres (`Estado General`, `Subestado`, `Motivo`) y `comedor_id`; soporta `--dry-run`. Evidencia: `comedores/management/commands/update_estados_comedores_from_names.py`.
- `reset_validaciones`: resetea validaciones de comedores a Pendiente. Evidencia: `comedores/management/commands/reset_validaciones.py`.
- `update_comedores_dupla`: asigna duplas a comedores desde CSV, opcionalmente creando admisiones. Evidencia: `comedores/management/commands/update_comedores_dupla.py`.
- `sync_comedores_gestionar`: sincroniza payload completo de comedores contra GESTIONAR (`Add`/`Update`, multithread). Evidencia: `comedores/management/commands/sync_comedores_gestionar.py`.
- `sync_territoriales_cache`: sincroniza cache de territoriales, con opciones de stats, force y cleanup. Evidencia: `comedores/management/commands/sync_territoriales_cache.py`.

## Centro de familia
- `cargar_legajos`: crea ciudadanos/participantes desde Excel. Evidencia: `centrodefamilia/management/commands/cargar_legajos.py`.
- `reprocess_cabal`: reprocesa registros CABAL rechazados con confirmacion interactiva. Evidencia: `centrodefamilia/management/commands/reprocess_cabal.py`.

## Celiaquia
- `migrar_comentarios`: migra comentarios legados de expedientes al historial; soporta `--dry-run`. Evidencia: `celiaquia/management/commands/migrar_comentarios.py`.

## Auditoria
- `purge_auditlog`: borra registros de auditlog mas antiguos que N dias (soporta `--dry-run`). Evidencia: `audittrail/management/commands/purge_auditlog.py`.

## Nota
- Los comandos `test_*` presentes en algunas apps se consideran utilitarios de desarrollo/regresion y no forman parte del inventario operativo principal.
