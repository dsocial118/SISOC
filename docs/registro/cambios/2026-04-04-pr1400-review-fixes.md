# PR 1400: fixes de review en usuarios, mensajes y documentos

## Resumen

Se corrigieron tres hallazgos detectados durante la revisión del PR `#1400`:

1. El indicador de solicitudes pendientes de reset mobile en el listado de usuarios ahora solo se expone a usuarios con capacidad de gestión (`auth.change_user`).
2. Los contadores de mensajes no leídos en la API PWA se calculan sobre el conjunto completo antes de paginar, evitando badges inconsistentes entre páginas.
3. El filtro `hasta` del endpoint de documentos de comedores ahora incluye archivos cargados durante todo el día indicado.

## Archivos principales

- `users/services.py`
- `pwa/api_views.py`
- `comedores/api_views.py`
- `tests/test_users_auth_flows.py`
- `tests/test_pwa_mensajes_api.py`
- `tests/test_pwa_comedores_api.py`

## Validación

Se agregaron tests puntuales de regresión para:

- visibilidad del indicador de reset según permisos;
- consistencia de contadores globales con paginación en mensajes PWA;
- inclusión de documentos cargados el mismo día en el filtro `hasta`.

Para validar localmente en esta worktree se usó un `ROOT_URLCONF` mínimo de prueba en los tests nuevos, porque el `config.urls` completo importa dependencias nativas de `weasyprint` no disponibles en este entorno Windows.
