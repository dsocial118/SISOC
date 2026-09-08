# Contexto de feature PR #2266 - refactor(core): centralizar integración RENAPER

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2266
- Base: `development`
- Rama origen: `codex/issue-2243-shared-renaper`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2266.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `VAT/services/consulta_renaper/__init__.py`
- `VAT/services/consulta_renaper/impl.py`
- `celiaquia/views/validacion_renaper.py`
- `centrodefamilia/apps.py`
- `centrodefamilia/services/beneficiarios_service/impl.py`
- `centrodefamilia/services/consulta_renaper/__init__.py`
- `centrodefamilia/services/consulta_renaper/impl.py`
- `comedores/services/comedor_service/impl.py`
- `config/settings.py`
- `core/api_views.py`
- `core/integrations/__init__.py`
- `core/integrations/renaper.py`
- `core/services/renaper.py`
- `docs/contexto/arquitectura.md`
- `docs/contexto/panorama.md`
- `docs/flujos/consulta_renaper.md`
- `docs/ia/MODULAR_BOUNDARIES.md`
- ... y 8 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/arquitectura.md`
- `docs/contexto/panorama.md`
- `docs/flujos/consulta_renaper.md`
- `docs/ia/MODULAR_BOUNDARIES.md`
- `docs/operacion/integraciones.md`
- `docs/registro/decisiones/2026-08-10-integracion-renaper-compartida.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
