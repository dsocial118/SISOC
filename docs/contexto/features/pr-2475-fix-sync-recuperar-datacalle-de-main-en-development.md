# Contexto de feature PR #2475 - fix(sync): recuperar DataCalle de main en development

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2475
- Base: `development`
- Rama origen: `codex/restore-main-sync`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: datacalle/templates/datacalle/encuesta_detail.html, datacalle/templates/datacalle/relevamiento_confirm_delete.html, datacalle/templates/datacalle/relevamiento_detail.html, datacalle/templates/datacalle/relevamiento_form.html, datacalle/templates/datacalle/relevamiento_list.html, static/custom/css/datacalle.css, static/custom/js/user_mobile_access.js, templates/includes/sidebar/opciones.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2475.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `comedores/api_serializers.py`
- `comedores/api_views_territorial.py`
- `comedores/models.py`
- `config/settings.py`
- `config/urls.py`
- `datacalle/__init__.py`
- `datacalle/api_permissions.py`
- `datacalle/api_serializers.py`
- `datacalle/api_urls.py`
- `datacalle/api_views.py`
- `datacalle/apps.py`
- `datacalle/forms.py`
- `datacalle/instrumento/README.md`
- `datacalle/instrumento/catalogos.json`
- `datacalle/instrumento/cuestionario.json`
- `datacalle/instrumento/diccionario-respuestas.json`
- `datacalle/migrations/0001_initial.py`
- `datacalle/migrations/0002_relevamiento_localidades.py`
- ... y 58 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2452-feat-datacalle-modulo-de-relevamientos-de-situacion-de-calle-y-api-para-la-app.md`
- `docs/contexto/features/pr-2453-fix-datacalle-500-en-el-detalle-de-relevamiento-por-out-of-sort-memory-de-mysql.md`
- `docs/contexto/features/pr-2474-feat-deploy-preparar-activacion-web-de-datacalle-y-gestionar.md`
- `docs/contexto/features/pr-2475-fix-sync-recuperar-datacalle-de-main-en-development.md`
- `docs/operacion/deploy_pwas.md`
- `docs/operacion/nginx/README.md`
- `docs/operacion/nginx/sisoc-pwas.conf`
- `docs/registro/cambios/2026-09-01-datacalle-rol-relevador-calle.md`
- `docs/registro/cambios/2026-09-03-datacalle-modulo-relevamientos.md`
- `docs/registro/cambios/2026-09-06-datacalle-casos-y-api.md`
- `docs/registro/cambios/2026-09-08-activacion-pwa-web.md`
- `docs/registro/cambios/2026-09-08-sincronizacion-datacalle-main.md`
- `docs/registro/prs/PR-2452.md`
- `docs/registro/prs/PR-2453.md`
- `docs/registro/prs/PR-2474.md`
- `docs/registro/prs/PR-2475.md`
- `docs/registro/releases/pending/2026-09-09-pr-2452.md`
- `docs/registro/releases/pending/2026-09-09-pr-2453.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
