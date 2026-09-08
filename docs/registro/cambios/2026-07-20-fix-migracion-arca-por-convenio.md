# Corrección de la migración ARCA por tipo de convenio

## Fecha

2026-07-20

## Objetivo

Permitir que `organizaciones.0016_issue_2083_documentacion_organizacion` se
ejecute con catálogos históricos que contienen más de una Constancia de ARCA
para un mismo tipo de convenio.

## Cambio realizado

- Cada `ArchivoAdmision` materializado usa la documentación ARCA asociada al
  `tipo_convenio` de su admisión.
- Ante documentos ARCA duplicados para el mismo convenio, la migración elige
  de forma determinista el de menor `orden` e `id`, igual que los listados de
  admisiones.
- Si no existe documentación ARCA para el convenio, crea una y la asocia a
  ese convenio; no reutiliza documentación de otro tipo.
- Para admisiones históricas sin `tipo_convenio`, conserva un documento ARCA
  sin asociación de convenio.

## Validación

- Tests de regresión para los catálogos jurídico/eclesiástico, documentos
  duplicados en el mismo convenio, ausencia de catálogo y admisiones sin
  convenio.
- Formato Black sobre la migración y el test.

## Riesgos

- La migración no elimina los documentos duplicados históricos: usa el
  primero por `orden, id` para preservar datos y evitar una limpieza de
  catálogo fuera de alcance.
