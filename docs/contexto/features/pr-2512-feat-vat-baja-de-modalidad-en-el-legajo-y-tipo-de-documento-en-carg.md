# Contexto de feature PR #2512 - feat(vat): baja de Modalidad en el legajo y tipo de documento en carg…

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2512
- Base: `development`
- Rama origen: `Task/inet-mejoras-septiembre`
- Autor: `juancruzventura-ai`

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
- Archivos visuales relevantes: VAT/templates/vat/centros/centro_detail.html, VAT/templates/vat/centros/partials/centro_cursos_panel.html, VAT/templates/vat/comision_curso_wizard/step1_info.html, VAT/templates/vat/curso/comision_curso_detail.html, VAT/templates/vat/curso/curso_detail.html, VAT/templates/vat/oferta_institucional/comision_detail.html, VAT/templates/vat/reportes/inscripciones_asistencia.html, ciudadanos/templates/ciudadanos/ciudadano_detail.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2512.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/forms.py`
- `VAT/services/nomina_export.py`
- `VAT/services/reportes_inscripciones_asistencia.py`
- `VAT/templates/vat/centros/centro_detail.html`
- `VAT/templates/vat/centros/partials/centro_cursos_panel.html`
- `VAT/templates/vat/comision_curso_wizard/step1_info.html`
- `VAT/templates/vat/curso/comision_curso_detail.html`
- `VAT/templates/vat/curso/curso_detail.html`
- `VAT/templates/vat/oferta_institucional/comision_detail.html`
- `VAT/templates/vat/reportes/inscripciones_asistencia.html`
- `VAT/test_inscripcion_rapida_documento.py`
- `VAT/tests.py`
- `VAT/views/reporte.py`
- `ciudadanos/api_views.py`
- `ciudadanos/forms.py`
- `ciudadanos/migrations/0032_ciudadano_documento_pasaporte_ciudadano_pais_emisor.py`
- `ciudadanos/models.py`
- `ciudadanos/templates/ciudadanos/ciudadano_detail.html`
- `docs/contexto/features/pr-2512-feat-vat-baja-de-modalidad-en-el-legajo-y-tipo-de-documento-en-carg.md`
- `docs/registro/cambios/2026-09-14-inet-modalidad-oculta-y-tipo-documento.md`
- ... y 2 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
