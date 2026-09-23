# Contexto de feature PR #2562 - Celiaquia tk 2521

## Resumen

- PR: https://github.com/secretarianaf/SISOC/pull/2562
- Base: `development`
- Rama origen: `CeliaquiaTk_2521`
- Autor: `MariaNavarro90`

## Contexto funcional

- Celiaquía — revisión técnica de expedientes. El Técnico necesita acceder al Excel original de la Provincia para contrastarlo contra los legajos que revisa; hasta ahora dependía de que un Coordinador se lo enviara por fuera del sistema.

## Arquitectura tocada

- No se detectó un patrón arquitectónico dominante más allá del diff observado.

## Decisiones y supuestos detectados

- Tipo de cambio declarado: Feature — ampliación de permisos por rol, con endurecimiento del control de acceso asociado en la vista de descarga.
- Área principal declarada: celiaquia (views/expediente.py y tests).
- Impacto usuario declarado: Los Técnicos dejan de depender de un Coordinador para acceder al archivo de origen del expediente, acortando el circuito de revisión de legajos.
- Riesgos / rollback: Riesgo bajo. No hay migraciones, cambios de modelo ni modificaciones de templates. El cambio consiste en una condición de permiso y una validación de alcance.

## Design system y UI

- Sin cambios visibles de UI o design system detectados en el diff.

## Memoria operativa para agentes

- Empezar por `docs/registro/prs/PR-2562.md` para contexto resumido del PR.
- Revisar primero estos archivos del diff:
- `celiaquia/tests/test_expediente_excel_audit.py`
- `celiaquia/views/expediente.py`
- `docs/registro/cambios/2026-09-23-2521-tecnico-descarga-excel-provincia.md`
- Documentación sugerida para ampliar contexto:
- `docs/indice.md`
- `docs/ia/CONTEXT_HYGIENE.md`
- `docs/ia/ARCHITECTURE.md`
- `docs/ia/TESTING.md`

## Trazabilidad

- Documento generado automáticamente desde el evento de `pull_request`.
- Si este PR cambia de título, el archivo se renombrará para mantener el slug alineado.
