# Contexto de feature PR #2565 - fix(importaciones): recuperar workers y acelerar lotes masivos (#2560, #2561)

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2565
- Base: `development`
- Rama origen: `juanikitro/Importacion-masiva`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2565.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `AGENT_REPO_MAP.md`
- `ciudadanos/migrations/0033_ciudadanosimportjob_lease_token.py`
- `ciudadanos/models.py`
- `ciudadanos/services_importacion_masiva.py`
- `ciudadanos/services_importacion_masiva_jobs.py`
- `comunicados/services_mailing_jobs.py`
- `config/settings.py`
- `core/integrations/renaper.py`
- `core/integrations/renaper_rate_limit.py`
- `core/migrations/0009_renaper_consulta_rate_limit.py`
- `core/models.py`
- `core/services/renaper.py`
- `docker-compose.produccion.yml`
- `docs/flujos/consulta_renaper.md`
- `docs/registro/cambios/2026-09-23-workers-importacion-2560-2561.md`
- `docs/registro/decisiones/2026-09-23-renaper-importacion-token-y-tasa.md`
- `encuestas/services.py`
- `ocr/services_ocr_jobs.py`
- `scripts/infra/healthcheck_prod.sh`
- ... y 8 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
