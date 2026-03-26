# Contexto de feature PR #1369 - Codex/fix renaper timeout worker exit

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1369
- Base: `main`
- Rama origen: `codex/fix-renaper-timeout-worker-exit`
- Autor: `dsocial118`

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
- Archivos visuales relevantes: VAT/templates/vat/catalogo/modalidadcursada_confirm_delete.html, VAT/templates/vat/catalogo/modalidadcursada_detail.html, VAT/templates/vat/catalogo/modalidadcursada_form.html, VAT/templates/vat/catalogo/modalidadcursada_list.html, VAT/templates/vat/catalogo/planversioncurricular_confirm_delete.html, VAT/templates/vat/catalogo/planversioncurricular_detail.html, VAT/templates/vat/catalogo/planversioncurricular_form.html, VAT/templates/vat/catalogo/planversioncurricular_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1369.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.claude/settings.local.json`
- `VAT/admin.py`
- `VAT/api_urls.py`
- `VAT/api_views.py`
- `VAT/api_web_views.py`
- `VAT/fixtures/modalidad_institucional_inicial.json`
- `VAT/forms.py`
- `VAT/management/commands/recargar_vouchers.py`
- `VAT/migrations/0001_initial.py`
- `VAT/migrations/0006_autoridadinstitucional_comision_comisionhorario_and_more.py`
- `VAT/migrations/0007_voucherparametria_voucher_parametria.py`
- `VAT/migrations/0008_voucherparametria_renovacion.py`
- `VAT/migrations/0009_voucher_asignado_por.py`
- `VAT/migrations/0010_remove_ofertainstitucional_aprobacion_inet_and_more.py`
- `VAT/migrations/0011_ofertainstitucional_costo.py`
- `VAT/migrations/0012_asistenciasesion.py`
- `VAT/migrations/0013_voucherparametria_inscripcion_unica_activa.py`
- `VAT/models.py`
- `VAT/serializers.py`
- `VAT/services/actividad_service/__init__.py`
- ... y 181 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-03-25-vat-api-web.md`
- `docs/registro/cambios/2026-03-25-vat-legajo-ciudadano-detalle.md`
- `docs/registro/cambios/2026-03-26-cdi-actualizacion-matriz-textos-formulario.md`
- `docs/registro/cambios/2026-03-26-cdi-centros-desarrollo-infantil-formulario.md`
- `docs/registro/cambios/2026-03-26-comedores-renaper-fail-fast-timeout.md`
- `docs/registro/cambios/2026-03-26-fix-celiaquia-merge-payload-registro-erroneo.md`
- `docs/registro/cambios/2026-03-26-vat-fix-errores-inscripcion-api.md`
- `docs/vat/IMPLEMENTACION_DER_V4.md`
- `docs/vat/PLAN_FASES_4_5.md`
- `docs/vat/VOUCHER_SETUP.md`
- `docs/vat/api_web.md`
- `docs/vat/guia_desarrollo.md`
- `docs/vat/manual_usuario.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
