# Contexto de feature PR #2258 - feat(celiaquia): contrato público de integración

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2258
- Base: `development`
- Rama origen: `codex/issue-2242-celiaquia-public-contract`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: ciudadanos/templates/ciudadanos/ciudadano_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2258.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.github/workflows/architecture.yml`
- `.importlinter`
- `.importlinter_celiaquia_config`
- `AGENT_REPO_MAP.md`
- `celiaquia/api.py`
- `celiaquia/apps.py`
- `celiaquia/ciudadano_detail.py`
- `celiaquia/global_urls.py`
- `celiaquia/services/ciudadano_resumen_service/__init__.py`
- `celiaquia/services/ciudadano_resumen_service/impl.py`
- `celiaquia/tests/test_public_api.py`
- `ciudadanos/templates/ciudadanos/ciudadano_detail.html`
- `ciudadanos/views.py`
- `config/urls.py`
- `docs/ia/MODULAR_BOUNDARIES.md`
- `docs/registro/decisiones/2026-08-07-contrato-publico-celiaquia.md`
- `tests/test_ciudadanos_templates_unit.py`
- `tests/test_ciudadanos_views_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/ia/MODULAR_BOUNDARIES.md`
- `docs/registro/decisiones/2026-08-07-contrato-publico-celiaquia.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
