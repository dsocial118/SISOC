# Contexto de feature PR #2506 - PAS: Mejoras Ux DDJJ

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2506
- Base: `development`
- Rama origen: `task/Mejoras-Pas-UxDDJJ`
- Autor: `Esteban-Royo`

## Contexto funcional

- Supervivencia RENAPER, padrón y DDJJ PAS.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Feature, corrección funcional, migración e interfaz.
- Área principal declarada: PAS.
- Impacto usuario declarado: Circuito de bajas consistente y formulario responsive simplificado.
- Riesgos / rollback: La migración 0008 elimina la firma histórica del JSON de respuestas.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: pas/templates/pas/ddjj_formulario.html, pas/templates/pas/persona_detail.html, pas/templates/pas/persona_form.html, pas/templates/pas/titulares_import.html, static/custom/css/pas_ddjj.css, static/custom/img/formando_capital_humano_marca.png, static/custom/js/pas_ddjj.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2506.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/contexto/features/pr-2506-pas-mejoras-ux-ddjj.md`
- `docs/implementaciones/pas.md`
- `docs/implementaciones/pas_control_mensual_celery.md`
- `docs/registro/cambios/2026-09-10-pas-renaper-genero-domicilio.md`
- `docs/registro/prs/PR-2506.md`
- `pas/forms.py`
- `pas/migrations/0007_paspersona_genero_calle_altura.py`
- `pas/migrations/0008_remove_ddjj_firma_respuestas.py`
- `pas/models.py`
- `pas/services/ddjj_service.py`
- `pas/services/supervivencia_jobs.py`
- `pas/services/supervivencia_service.py`
- `pas/services/titulares_import_service.py`
- `pas/templates/pas/ddjj_formulario.html`
- `pas/templates/pas/persona_detail.html`
- `pas/templates/pas/persona_form.html`
- `pas/templates/pas/titulares_import.html`
- `pas/tests/test_cruces.py`
- `pas/tests/test_ddjj.py`
- `pas/tests/test_pas_persona_service.py`
- ... y 7 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
