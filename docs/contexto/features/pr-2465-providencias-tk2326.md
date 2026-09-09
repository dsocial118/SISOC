# Contexto de feature PR #2465 - Providencias tk2326

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2465
- Base: `development`
- Rama origen: `providencias_tk2326`
- Autor: `MariaNavarro90`

## Contexto funcional

- Admisiones - Legales. Reemplazo del trámite de Disposición por Primera y Segunda Providencia.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: feature (con eliminación de un circuito existente y migración de esquema aditiva).
- Área principal declarada: admisiones (impacto menor en acompanamientos por el destrabe del botón de Acompañamiento).
- Impacto usuario declarado: Alto para el equipo de Legales: cambian los botones, los modales y los documentos del tramo entre IF Convenio Asignado e Intervención Jurídicos, y desaparece la carga de Disposición posterior a Jurídicos. Los datos de disposiciones históricas se siguen viendo. El resto de los usuarios no percibe cambios.
- Riesgos / rollback: La migración es aditiva (crea una tabla y cambia choices; no borra columnas ni tablas), por lo que el rollback de código no implica pérdida de datos. Riesgo principal: expedientes que queden en estados del circuito viejo al momento del deploy, mitigado dejando habilitado su botón siguiente. Se coordinó con el área funcional cerrar los 7 expedientes pendientes antes de desplegar.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: admisiones/templates/admisiones/admisiones_legales_detalle.html, admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_base.docx, admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_cinco_comedores.docx, admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_judicializados.docx, admisiones/templates/admisiones/docx/incorporacion_docx_proyecto_disposicion.docx, admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_base.docx, admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_cinco_comedores.docx, admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_judicializados.docx

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2465.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `.gitignore`
- `admisiones/admin.py`
- `admisiones/forms/admisiones_forms.py`
- `admisiones/migrations/0080_issue_2326_providencias.py`
- `admisiones/migrations/0081_issue_2326_ampliar_numero_pv.py`
- `admisiones/models/admisiones.py`
- `admisiones/services/admisiones_service/impl.py`
- `admisiones/services/docx_service/impl.py`
- `admisiones/services/legales_service/impl.py`
- `admisiones/templates/admisiones/admisiones_legales_detalle.html`
- `admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_base.docx`
- `admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_cinco_comedores.docx`
- `admisiones/templates/admisiones/docx/incorporacion_docx_primera_providencia_judicializados.docx`
- `admisiones/templates/admisiones/docx/incorporacion_docx_proyecto_disposicion.docx`
- `admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_base.docx`
- `admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_cinco_comedores.docx`
- `admisiones/templates/admisiones/docx/renovacion_docx_primera_providencia_judicializados.docx`
- `admisiones/templates/admisiones/docx/renovacion_docx_proyecto_disposicion.docx`
- `admisiones/templates/admisiones/docx/segunda_providencia.docx`
- `admisiones/templates/admisiones/partials/numero_pv_estructurado.html`
- ... y 13 archivo(s) adicional(es) relacionados.
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
