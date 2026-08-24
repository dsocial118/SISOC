# Variables documentales para renovaciones

## Decisiones aprobadas

- Las referencias se resuelven al generar el documento, sin copiar datos en el informe.
- La admisión anterior es la más reciente del mismo comedor, previa a la actual, excluyendo las descartadas e inactivadas.
- Los totales se calculan desde cantidades aprobadas por día del Informe Técnico.
- El detalle de renovaciones anteriores incluye disposición, convenio y expediente, de la más antigua a la más reciente.
- Los datos faltantes se resuelven como texto vacío para completar manualmente.
- Los expedientes se exponen solo para los templates de financiamiento vigente; Personería/PJE y Base usan variables distintas.

## Alcance técnico

- Campo opcional de referencia IF IT Complementario en `InformeTecnico`.
- Servicio central de contexto para las variables documentales.
- Migración de esquema y migración de datos para registrar las variables activas del catálogo.
- Pruebas de selección de antecedentes, cálculo de totales, formato y faltantes.

## Fuera de alcance

- Publicar versiones de templates.
- Reemplazar marcadores de los borradores ya cargados en SISOC.
- Backfill de datos históricos.
