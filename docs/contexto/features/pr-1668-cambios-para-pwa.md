# Contexto de feature PR #1668 - Cambios para PWA

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/1668
- Base: `main`
- Rama origen: `Cambios-Mobile-04-05-26`
- Autor: `PabloCao1`

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
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html, centrodeinfancia/templates/centrodeinfancia/nomina_detail.html, centrodeinfancia/templates/centrodeinfancia/nomina_form_edit.html, ciudadanos/templates/ciudadanos/ciudadano_list.html, comedores/templates/comedor/nomina_form.html, organizaciones/templates/organizacion_form.html, static/custom/js/nomina_detail.js, templates/components/pagination.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-1668.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `VAT/api_urls.py`
- `VAT/api_web_views.py`
- `VAT/serializers.py`
- `VAT/services/inscripcion_service.py`
- `VAT/tests.py`
- `celiaquia/admin.py`
- `celiaquia/services/familia_service/impl.py`
- `celiaquia/services/legajo_service/impl.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_admin.py`
- `celiaquia/tests/test_expediente_detail.py`
- `celiaquia/views/expediente.py`
- `centrodeinfancia/forms.py`
- `centrodeinfancia/formulario_cdi_schema.py`
- `centrodeinfancia/migrations/0024_alter_centrodeinfancia_nombre.py`
- `centrodeinfancia/migrations/0025_alter_centrodeinfancia_fecha_inicio_and_more.py`
- `centrodeinfancia/migrations/0026_oferta_servicio_multiple.py`
- `centrodeinfancia/migrations/0027_merge_20260427_1431.py`
- `centrodeinfancia/migrations/0028_alter_formulariocdi_condiciones_almacenamiento_leche_humana.py`
- `centrodeinfancia/models.py`
- ... y 50 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/operacion/codex_desktop.md`
- `docs/registro/cambios/2026-04-20-centrodeinfancia-oferta-servicios-multiples.md`
- `docs/registro/cambios/2026-04-27-ciudadanos-filtro-estado-revision.md`
- `docs/registro/cambios/2026-04-28-celiaquia-relaciones-familiares-expediente.md`
- `docs/registro/cambios/2026-05-04-mobile-convenio-alimentar-prestaciones.md`
- `docs/vat/api_web.md`
- `docs/vat/documento-funcional-mi-argentina-inscripcion-vat.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
