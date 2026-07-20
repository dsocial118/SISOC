# Corrección de la migración ARCA por tipo de convenio

## Fecha

2026-07-20

## Objetivo

Permitir que `organizaciones.0016_issue_2083_documentacion_organizacion` se
ejecute cuando el catálogo de admisiones contiene una Constancia de ARCA por
cada tipo de convenio.

## Cambio realizado

- La migración deja de buscar o crear documentación solo por nombre.
- Cada `ArchivoAdmision` materializado usa la documentación ARCA asociada al
  `tipo_convenio` de su admisión.
- Si falta o se duplica la documentación para un mismo convenio, la migración
  falla antes de elegir un destino incorrecto.

## Validación

- Test de regresión con los catálogos jurídico y eclesiástico de ARCA.
- Formato Black sobre la migración y el test.

## Riesgos

- La migración requiere que toda admisión vinculada tenga un `tipo_convenio`
  con una única Constancia de ARCA asociada, que es el contrato del catálogo
  vigente.
