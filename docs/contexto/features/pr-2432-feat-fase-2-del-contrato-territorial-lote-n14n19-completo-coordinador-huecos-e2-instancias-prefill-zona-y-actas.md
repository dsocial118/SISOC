# Contexto de feature PR #2432 - feat: fase 2 del contrato territorial — lote N14–N19 completo (coordinador, huecos E2, instancias, prefill, zona y actas)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2432
- Base: `main`
- Rama origen: `pwanueva-v2`
- Autor: `Mkdir-arg`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

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
- Archivos visuales relevantes: relevamientos/templates/relevamiento_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2432.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `comedores/api_serializers.py`
- `comedores/api_urls_territorial.py`
- `comedores/api_views_territorial.py`
- `comedores/migrations/0057_huecos_seguimiento_n19.py`
- `comedores/models.py`
- `docs/contexto/features/pr-2432-feat-fase-2-del-contrato-territorial-lote-n14n19-completo-coordinador-huecos-e2-instancias-prefill-zona-y-actas.md`
- `docs/registro/prs/PR-2432.md`
- `docs/registro/releases/pending/2026-09-09-pr-2432.md`
- `relevamientos/migrations/0014_validacion_coordinador.py`
- `relevamientos/migrations/0015_huecos_seguimiento_n19.py`
- `relevamientos/migrations/0016_instancias_seguimiento_n14.py`
- `relevamientos/migrations/0017_altas_desde_app_n15_n18.py`
- `relevamientos/models.py`
- `relevamientos/serializer.py`
- `relevamientos/signals.py`
- `relevamientos/templates/relevamiento_detail.html`
- `relevamientos/urls/api_urls.py`
- `relevamientos/urls/web_urls.py`
- `relevamientos/views/api_views.py`
- ... y 8 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-2432-feat-fase-2-del-contrato-territorial-lote-n14n19-completo-coordinador-huecos-e2-instancias-prefill-zona-y-actas.md`
- `docs/registro/prs/PR-2432.md`
- `docs/registro/releases/pending/2026-09-09-pr-2432.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
