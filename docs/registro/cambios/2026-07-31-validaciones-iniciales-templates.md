# Validaciones iniciales para templates de Informe Técnico

Fecha: 2026-07-31

## Alcance

Se incorporan en la admisión los datos de clasificación que utilizará el futuro
Gestor de templates para elegir el borrador DOCX del Informe Técnico.

- Incorporación: `Es Ex PNUD` y, cuando corresponde, el estado del convenio PNUD.
- Renovación: tipo de renovación y estado del financiamiento.

Los datos se solicitan junto a la selección inicial de convenio y pueden
corregirse desde la admisión mientras no se haya generado el Informe Técnico.

## Comportamiento preservado

No se modifica la procedencia de `tipo_convenio`, que continúa heredándose del
Legajo de la Organización, ni el refresco de la documentación requerida por la
admisión. Tampoco se modifican los templates actuales de Disposición y Convenio.

## Validación

- Migración `0069` aplicada en el entorno local.
- Pruebas de las validaciones y regresión de documentación: 15 aprobadas.
- `black --check` y `makemigrations --check --dry-run` aprobados.
