# 2026-08-24 - Variables documentales para renovaciones del issue 1213

## Contexto

- Los templates de renovación requieren referencias históricas y totales de prestaciones que no estaban disponibles en el catálogo.

## Cambios aplicados

- Se incorporó el campo opcional `IF IT Complementario` al formulario del Informe Técnico cuando la admisión tiene modificación de prestaciones.
- Se agregaron variables de catálogo para antecedentes de incorporación y renovaciones, expedientes y totales semanales de prestaciones.
- Los antecedentes se resuelven desde admisiones previas activas del mismo comedor; las descartadas o inactivadas no participan.
- Los datos ausentes se entregan vacíos para permitir su completado manual en el documento.

## Impacto esperado

- Las nuevas versiones de templates podrán usar las variables documentales sin copiar información histórica en el Informe Técnico actual.
- Este cambio no publica ni modifica versiones de templates existentes.

## Riesgos y rollback

- La migración agrega un campo nullable y registros de catálogo. Revertir la migración elimina ambos registros de catálogo y el campo.
