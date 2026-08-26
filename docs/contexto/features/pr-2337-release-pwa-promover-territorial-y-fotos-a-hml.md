# Contexto de feature PR #2337 - release(pwa): promover territorial y fotos a HML

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2337
- Base: `homologacion`
- Rama origen: `codex/release-pwanueva-hml`
- Autor: `juanikitro`

## Contexto funcional

- Promoción a HML de la PWA territorial y el flujo de imágenes de comedor, incluyendo la migración compatible con el estado histórico de QA y producción.

## Arquitectura tocada

- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Release candidate; sin merge ni despliegue automático.
- Área principal declarada: comedores, users y sus migraciones Django.
- Impacto usuario declarado: Habilita validar en HML los cambios PWA aprobados en QA y no altera datos cuando las estructuras históricas ya existen.
- Riesgos / rollback: La 0056 es idempotente solo hacia adelante. Ante reversión, restaurar el despliegue; no ejecutar una reversión destructiva de la migración con origen histórico incierto.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: users/templates/user/user_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2337.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `comedores/api_serializers.py`
- `comedores/api_urls_territorial.py`
- `comedores/api_views_territorial.py`
- `comedores/migrations/0056_imagencomedor_client_uuid_imagencomedor_relevamiento_and_more.py`
- `comedores/models.py`
- `comedores/views_territorial.py`
- `config/urls.py`
- `docs/contexto/features/pr-2335-release-pwa-promover-territorial-y-fotos-a-qa.md`
- `docs/contexto/features/pr-2337-release-pwa-promover-territorial-y-fotos-a-hml.md`
- `docs/registro/cambios/2026-07-17-usuario-territorial-comedor.md`
- `docs/registro/cambios/2026-08-25-pwanueva-migraciones-pwa.md`
- `docs/registro/prs/PR-2335.md`
- `docs/registro/prs/PR-2337.md`
- `relevamientos/views/api_views.py`
- `tests/test_comedores_migration_0056.py`
- `tests/test_relevamiento_api_patch.py`
- `tests/test_territorial_api.py`
- `tests/test_users_api_login.py`
- `tests/test_users_pwa_forms.py`
- `users/api_permissions.py`
- ... y 8 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2335-release-pwa-promover-territorial-y-fotos-a-qa.md`
- `docs/contexto/features/pr-2337-release-pwa-promover-territorial-y-fotos-a-hml.md`
- `docs/registro/cambios/2026-07-17-usuario-territorial-comedor.md`
- `docs/registro/cambios/2026-08-25-pwanueva-migraciones-pwa.md`
- `docs/registro/prs/PR-2335.md`
- `docs/registro/prs/PR-2337.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
