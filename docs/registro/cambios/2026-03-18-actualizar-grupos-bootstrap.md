# Actualización de las semillas de grupos (2026-03-18)

## Contexto
- El catálogo original de `listado_permisos.csv` con grupos como `Comedores total`, `Celiaquia Total`, `Visualización total`, `Centros de Infancia Total` y el comentario “1 por cada tablero” ya no vive en un archivo externo; se incrusta directamente en `users/bootstrap/groups_seed.py` como `_LISTADO_PERMISOS_CSV`.
- La semilla bootstrap sigue siendo la fuente de verdad para los comandos `create_groups`, `sync_group_permissions_from_registry` y cualquier código que consulte `permission_codes_for_bootstrap_group`.

## Qué se hizo
- `users/bootstrap/groups_seed.py` parsea ahora ese CSV embebido, genera los `BootstrapGroupSeed` de cada fila, y agrega el conjunto resultante (incluido el grupo “Tableros Total”) al final de `BOOTSTRAP_GROUPS`, sin eliminar los grupos heredados de `COMEDORES_*`, `Centro de Infancia`, `COMUNICADOS_*`, etc.
- El rol `Admin` se recalcula como la unión de todos los permisos definidos más los derechos clásicos sobre usuarios y grupos, de modo que sigue “viendo todo” sin ser superusuario.
- La "nota" de “1 por cada tablero (por separado)” se mantiene junto con los grupos de `DATACALLE_GROUPS`, que ya crean un grupo para cada dashboard.
- Eliminamos el archivo `listado_permisos.csv` del repo porque toda la información ahora vive en el script, evitando dependencias externas.

## Riesgos / seguimiento
- Si el CSV se elimina o modifica el nombre de alguna columna, la inicialización fallará con `FileNotFoundError`. Mantener `docs/registro/cambios` sincronizado con cualquier ajuste al CSV.
