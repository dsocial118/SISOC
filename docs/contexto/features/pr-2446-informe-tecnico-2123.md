# Contexto de feature PR #2446 - Informe técnico #2123

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2446
- Base: `development`
- Rama origen: `Informe-Técnico-#2123`
- Autor: `nehuen871`

## Contexto funcional

- Admisiones — flujo de Técnicos. Carga del Informe Técnico y caratulación del expediente.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Feature + Fix
- Área principal declarada: admisiones
- Impacto usuario declarado: El técnico deja de navegar entre pantallas para cargar el Informe Técnico. Los campos que reflejan un número de GDE se completan solos y quedan sincronizados con los documentos. Se corrige que constancia_subsidios_dnsa y nota_gde_if no se cargaran en varios tipos de convenio.
- Riesgos / rollback: Riesgo:* el partial del informe se comparte entre la página de admisiones y la standalone, así que un error ahí afecta a las dos. La página de admisiones queda notablemente más larga (mitigado con los colapsables). Riesgo:* mientras el informe está en borrador el documento es la fuente de verdad de esos 5 campos, así que una edición manual se sobrescribe si después se toca el GDE del documento. Es el comportamiento pedido, pero es un cambio de criterio. Riesgo:* el mapeo se indexa por nombre de documento; si se renombra uno en el catálogo la réplica deja de aplicarse en silencio (es justo el bug corregido acá). Un mapeo por ID de Documentacion sería más robusto, pero hay una fila por tipo de convenio. Rollback:* revertir el commit. No hay migraciones; el partial es un extracto literal y los valores ya replicados en informes quedan como están.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/admisiones_tecnicos_form.html, admisiones/templates/admisiones/caratula_expediente_form.html, admisiones/templates/admisiones/informe_tecnico_form.html, admisiones/templates/admisiones/partials/informe_tecnico_campos.html, static/custom/css/informeTecnicoSecciones.css, static/custom/js/admisionesactualizarestado.js, static/custom/js/informeTecnicoSecciones.js

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2446.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `admisiones/forms/admisiones_forms.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/informes_service/impl.py`
- `admisiones/templates/admisiones/admisiones_tecnicos_form.html`
- `admisiones/templates/admisiones/caratula_expediente_form.html`
- `admisiones/templates/admisiones/informe_tecnico_form.html`
- `admisiones/templates/admisiones/partials/informe_tecnico_campos.html`
- `admisiones/utils.py`
- `admisiones/views/web_views.py`
- `docs/registro/cambios/2026-08-31-admisiones-informe-tecnico-y-caratula-en-formulario.md`
- `docs/registro/cambios/2026-09-04-gde-documento-replica-en-informe-tecnico.md`
- `static/custom/css/informeTecnicoSecciones.css`
- `static/custom/js/admisionesactualizarestado.js`
- `static/custom/js/informeTecnicoSecciones.js`
- `tests/test_admisiones_forms_unit.py`
- `tests/test_admisiones_gde_informe_sync_db.py`
- `tests/test_admisiones_web_views_unit.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-08-31-admisiones-informe-tecnico-y-caratula-en-formulario.md`
- `docs/registro/cambios/2026-09-04-gde-documento-replica-en-informe-tecnico.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
