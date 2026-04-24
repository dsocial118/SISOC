# Resolución de merge PR 1537: identidad de ciudadano y lookups por DNI

**Fecha:** 2026-04-16

## Qué se ajustó

- Se resolvió el merge entre `nomina_1329` y `development` preservando la paginación optimizada sin `COUNT(*)` en listados de ciudadanos.
- Se reintegraron los filtros de identidad del PR:
  - búsqueda textual por apellido, nombre e identificador interno;
  - filtro por `tipo_registro_identidad`;
  - badges de estado de identidad en la grilla.
- Se endureció la normalización de identidad al crear y editar ciudadanos:
  - `SIN_DNI` limpia `documento` y motivos de no validación RENAPER;
  - `DNI_NO_VALIDADO_RENAPER` limpia motivos de `SIN_DNI`;
  - `ESTANDAR` limpia ambos grupos de motivos y recompone `documento_unico_key`.
- Se corrigió el fallback de lookup por DNI en comedores y celiaquía para priorizar explícitamente registros `ESTANDAR` antes de caer al resto de los duplicados legacy.
- Se actualizaron tests unitarios para cubrir:
  - saneamiento de `documento` en `SIN_DNI`;
  - prioridad explícita de `ESTANDAR` en lookups;
  - coexistencia de filtros + paginación optimizada en ciudadanos.

## Decisión clave

Cuando no existe `documento_unico_key`, el sistema ya no elige por orden lexicográfico de
`tipo_registro_identidad`. Ese criterio era accidental y podía devolver un registro manual
en lugar del ciudadano estándar. El fallback ahora expresa la prioridad de negocio de forma
directa.

## Riesgo mitigado

- Evitar que una edición deje `documento_unico_key` o `requiere_revision_manual` desfasados.
- Evitar que un registro `SIN_DNI` siga participando en búsquedas por documento.
- Evitar que RENAPER, comedores o celiaquía vinculen al ciudadano equivocado ante duplicados legacy.
