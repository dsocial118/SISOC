# Contexto de feature PR #2535 - release: promocion a produccion sin features pospuestas (2026-09-16)

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2535
- Base: `main`
- Rama origen: `release/2026-09-16-sin-bloqueados`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en capa API/DRF y conviene revisar contratos de request/response.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.
- El alcance incluye automatización o tooling de CI/CD.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/buscador/ciudadano.html, admisiones/templates/admisiones/informe_tecnico_form.html, centrodeinfancia/templates/centrodeinfancia/destinatario_form.html, centrodeinfancia/templates/centrodeinfancia/reportes.html, centrodeinfancia/templates/centrodeinfancia/trabajador_detail.html, core/templates/core/mapa_arquitectura.html, dashboard/templates/dashboard_tablero.html, datacalle/templates/datacalle/relevamiento_form.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2535.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.env.example`
- `.github/workflows/pr-docs.yml`
- `.gitignore`
- `AGENT_REPO_MAP.md`
- `CHANGELOG.md`
- `VAT/services/buscador_ciudadano_service.py`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/services/vat_inscripciones_base.py`
- `VAT/templates/vat/buscador/ciudadano.html`
- `VAT/test_buscador_ciudadano.py`
- `VAT/urls.py`
- `VAT/views/buscador_ciudadano.py`
- `admisiones/forms/admisiones_forms.py`
- `admisiones/templates/admisiones/informe_tecnico_form.html`
- `admisiones/tests/test_variables_documentales_renovacion.py`
- `centrodeinfancia/management/commands/validar_renaper_nominas_cdi.py`
- `centrodeinfancia/services_nomina_ninos_pdf.py`
- `centrodeinfancia/services_renaper_estado.py`
- `centrodeinfancia/services_reportes.py`
- `centrodeinfancia/templates/centrodeinfancia/destinatario_form.html`
- ... y 244 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
