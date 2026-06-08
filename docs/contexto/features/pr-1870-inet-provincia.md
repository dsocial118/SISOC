# Contexto de feature PR #1870 - Inet provincia

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1870
- Base: `main`
- Rama origen: `INET-Provincia`
- Autor: `juanikitro`

## Contexto funcional

- No informado explícitamente; inferir desde el título del PR y el diff.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: No informado
- Área principal declarada: No informada
- Impacto usuario declarado: No informado
- Riesgos / rollback: No informado

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: VAT/templates/vat/catalogo/planversioncurricular_confirm_delete.html, VAT/templates/vat/catalogo/planversioncurricular_detail.html, VAT/templates/vat/catalogo/planversioncurricular_form.html, VAT/templates/vat/catalogo/planversioncurricular_list.html, VAT/templates/vat/centros/centro_create_form.html, VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/centros/centro_form.html, VAT/templates/vat/centros/centro_list.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1870.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `CHANGELOG.md`
- `VAT/forms.py`
- `VAT/migrations/0049_comisioncurso_cupo_lista_espera.py`
- `VAT/models.py`
- `VAT/serializers.py`
- `VAT/services/access_scope.py`
- `VAT/services/inscripcion_service.py`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/templates/vat/catalogo/planversioncurricular_confirm_delete.html`
- `VAT/templates/vat/catalogo/planversioncurricular_detail.html`
- `VAT/templates/vat/catalogo/planversioncurricular_form.html`
- `VAT/templates/vat/catalogo/planversioncurricular_list.html`
- `VAT/templates/vat/centros/centro_create_form.html`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/centro_form.html`
- `VAT/templates/vat/centros/centro_list.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/templates/vat/comision_curso_wizard/step1_info.html`
- `VAT/templates/vat/curso/comision_curso_form.html`
- `VAT/templates/vat/curso/curso_form.html`
- ... y 35 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/contexto/features/pr-1870-inet-provincia.md`
- `docs/registro/prs/PR-1870.md`
- `docs/registro/releases/pending/2026-06-10-pr-1870.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
