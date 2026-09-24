# Contexto de feature PR #2569 - Celiaquia tk 2523

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2569
- Base: `development`
- Rama origen: `CeliaquiaTk_2523`
- Autor: `MariaNavarro90`

## Contexto funcional

- Módulo Celiaquía, revisión técnica de legajos por parte de Nación. Amplía el catálogo de observaciones de ANSES y permite acompañar la solicitud de subsanación con documentación de respaldo que la Provincia pueda consultar.

## Arquitectura tocada

- El PR toca lógica en `services/`, por lo que impacta reglas de negocio u orquestación.
- Se modifican templates, con posible impacto visual o de composición UI.
- Existen cambios de persistencia o migraciones que requieren revisión de datos.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Evolutivo funcional con migración de esquema. Incluye tres correcciones de UX detectadas durante QA.
- Área principal declarada: celiaquia (comentarios técnicos y subsanaciones). Toca también el componente compartido templates/components/legajo_archivos_requeridos.html.
- Impacto usuario declarado: Medio y visible para Nación y Provincia en el módulo Celiaquía. Nación ve dos opciones más en el desplegable de ANSES y un campo de archivos nuevo en el modal de Subsanar; la Provincia ve un bloque nuevo con la documentación que adjuntó Nación. No cambian las reglas de visibilidad, publicación ni el flujo de estados existente, y el resto de los módulos no percibe cambios.
- Riesgos / rollback: Riesgo bajo. La migración 0008 es un AddField con default, reversible con migrate celiaquia 0007 y sin pérdida de datos más allá de la columna. El punto a vigilar es el gate de evidencia de la Provincia: si el filtro por origen fallara, la Provincia podría confirmar una subsanación sin haber respondido — está cubierto por test y verificado en QA. La migración tiene que correr antes de que alguien abra el modal de Subsanar.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: celiaquia/templates/celiaquia/expediente_detail.html, static/custom/js/expediente_detail.js, templates/components/legajo_archivos_requeridos.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2569.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/comentarios_tecnicos.py`
- `celiaquia/migrations/0008_subsanacionarchivo_origen.py`
- `celiaquia/models.py`
- `celiaquia/services/subsanacion_service/impl.py`
- `celiaquia/templates/celiaquia/expediente_detail.html`
- `celiaquia/tests/test_comentarios_tecnicos_service.py`
- `celiaquia/tests/test_subsanacion_documentacion_complementaria.py`
- `celiaquia/validators.py`
- `celiaquia/views/expediente.py`
- `celiaquia/views/subsanacion.py`
- `docs/registro/cambios/2026-09-23-2523-observaciones-anses-y-doc-complementaria.md`
- `static/custom/js/expediente_detail.js`
- `templates/components/legajo_archivos_requeridos.html`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
