# Contexto de feature PR #2253 - refactor(architecture): completar ratchet de Fase 0

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2253
- Base: `development`
- Rama origen: `codex/issue-2241-kernel-ratchet`
- Autor: `juanikitro`

## Contexto funcional

- boundary arquitectónico del monolito modular.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: refactor sin migraciones.
- Área principal declarada: core, ciudadanos y users.
- Impacto usuario declarado: ninguno esperado; se preservan permisos, accesos PWA y flujos existentes.
- Riesgos / rollback: bajo; revertir el commit restaura los imports directos. Los registros fallan explícitamente si falta un proveedor.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2253.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.importlinter`
- `AGENT_REPO_MAP.md`
- `VAT/apps.py`
- `VAT/ciudadano_detail.py`
- `VAT/favorite_filters.py`
- `VAT/sidebar_access.py`
- `acompanamientos/apps.py`
- `acompanamientos/favorite_filters.py`
- `admisiones/apps.py`
- `admisiones/favorite_filters.py`
- `celiaquia/apps.py`
- `celiaquia/ciudadano_detail.py`
- `centrodefamilia/apps.py`
- `centrodefamilia/ciudadano_detail.py`
- `centrodefamilia/favorite_filters.py`
- `ciudadanos/detail_contributions.py`
- `ciudadanos/services_importacion_masiva.py`
- `ciudadanos/test_territorial_scope.py`
- `ciudadanos/views.py`
- `comedores/apps.py`
- ... y 79 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/decisiones/2026-08-06-capacidad-comedores-pwa-fase-0.md`
- `docs/registro/decisiones/2026-08-06-catalogos-formularios-users-fase-0.md`
- `docs/registro/decisiones/2026-08-06-cierre-ratchet-fase-0.md`
- `docs/registro/decisiones/2026-08-06-contribuciones-ciudadano-360-fase-0.md`
- `docs/registro/decisiones/2026-08-06-endpoint-organizaciones-fase-0.md`
- `docs/registro/decisiones/2026-08-06-puerto-auditoria-auth-pwa-fase-0.md`
- `docs/registro/decisiones/2026-08-06-puerto-renaper-fase-0.md`
- `docs/registro/decisiones/2026-08-06-registro-filtros-favoritos-fase-0.md`
- `docs/registro/decisiones/2026-08-06-registro-post-fixture-intervenciones-fase-0.md`
- `docs/registro/decisiones/2026-08-06-registro-sidebar-vat-fase-0.md`
- `docs/registro/decisiones/2026-08-06-registro-soft-delete-vat-fase-0.md`
- `docs/registro/decisiones/2026-08-06-resolvedor-importacion-pwa-fase-0.md`
- `docs/registro/decisiones/2026-08-06-senal-coordinador-duplas-fase-0.md`
- `docs/registro/decisiones/2026-08-06-tests-alcance-territorial-ciudadanos-fase-0.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
