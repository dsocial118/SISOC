# Contexto de feature PR #2097 - Task/ver todos los expedientes

## Resumen

- PR: https://github.com/dsocial118/SISOC/pull/2097
- Base: `development`
- Rama origen: `task/ver-todos-los-expedientes`
- Autor: `Esteban-Royo`

## Contexto funcional

- Gestión compartida de importaciones de expedientes y actualización selectiva de fechas de acreditación.

## Arquitectura tocada

- Hay cambios en vistas web y puede existir impacto en permisos o renderizado.
- Se modifican templates, con posible impacto visual o de composición UI.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Mejora funcional y corrección de permisos.
- Área principal declarada: importarexpediente.
- Impacto usuario declarado: Usuarios autorizados acceden a todos los lotes; se evita sobrescribir acreditaciones de comedores no incluidos.
- Riesgos / rollback: El acceso queda restringido a usuarios con permiso de lectura. Rollback: revertir los cambios de rutas, consultas y actualización selectiva.

## Design system y UI

- El PR toca piezas de UI y conviene revisar consistencia visual con el patrón existente.
- Archivos visuales relevantes: importarexpediente/templates/importarexpediente_acreditacion_upload.html

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2097.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `docs/registro/cambios/2026-07-17-importaciones-visibilidad-global.md`
- `importarexpediente/services.py`
- `importarexpediente/templates/importarexpediente_acreditacion_upload.html`
- `importarexpediente/tests/test_ajax_endpoints.py`
- `importarexpediente/tests/test_import_flow.py`
- `importarexpediente/tests/test_legacy_views.py`
- `importarexpediente/urls.py`
- `importarexpediente/views.py`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`
- `docs/registro/cambios/2026-07-17-importaciones-visibilidad-global.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
