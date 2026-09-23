# Contexto de feature PR #2565 - fix(importaciones): recuperar workers y acelerar lotes masivos (#2560, #2561)

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2565
- Base: `development`
- Rama origen: `juanikitro/Importacion-masiva`
- Autor: `juanikitro`

## Contexto funcional

- Recuperación de workers persistentes tras cortes MySQL y procesamiento de lotes extensos con cupo RENAPER compartido.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: fix
- Área principal declarada: importaciones masivas y RENAPER
- Impacto usuario declarado: Los lotes interrumpidos por reinicio se reanudan solos y un lote extenso cede turno a otros; la meta de siete días sigue pendiente de medición.
- Riesgos / rollback: Aplicar las tres migraciones antes del código; conservar la configuración anterior y volver al tag previo si hay regresión, sin borrar filas ni credenciales. El correo ya enviado puede requerir revisión manual tras una caída.

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
- `docs/contexto/features/pr-2565-fix-importaciones-recuperar-workers-y-acelerar-lotes-masivos-2560-2561.md`
- `docs/flujos/consulta_renaper.md`
- `docs/registro/cambios/2026-09-23-workers-importacion-2560-2561.md`
- `docs/registro/decisiones/2026-09-23-renaper-importacion-token-y-tasa.md`
- `docs/registro/prs/PR-2565.md`
- `encuestas/services.py`
- ... y 10 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
