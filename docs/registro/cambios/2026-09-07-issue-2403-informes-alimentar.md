# 2026-09-07 - Issue 2403: Informes Alimentar Comunidad

## Contexto

El legajo de Comedor necesitaba centralizar el responsable de tarjeta para
Alimentar Comunidad, y las renovaciones debían reutilizar datos existentes sin
exponer la sección histórica de resolución de pago.

## Cambios aplicados

- Se incorporó la carga parcial del responsable de tarjeta en `Comedor`,
  visible y editable solo para el grupo `Tecnico Comedor` dentro de Alimentar
  Comunidad. El detalle del comedor ahora presenta una tarjeta-resumen con
  esos datos y acceso directo a su edición.
- Los siete campos geográficos del Informe Técnico ahora usan el catálogo
  territorial; los valores históricos que ya no existan en el catálogo se
  mantienen explícitamente al editar el informe.
- Los informes de renovación nuevos precargan responsable y prestaciones de la
  última admisión anterior activa con informe finalizado, aplicando el
  complementario validado cuando corresponde.
- Los antecedentes de renovación seleccionados como excluidos no se incluyen en
  las variables documentales ni en el contexto DOCX.
- Se agregó el criterio `D - Equivalencias` y se ocultaron los campos de
  resolución de pago en formularios, visualización, PDF y ambas plantillas
  DOCX, sin borrar las columnas históricas.

## Validación

- `git diff --check`.
- Parseo sintáctico de Python y `node --check` del JavaScript nuevo.
- Validación del empaquetador DOCX y búsqueda de placeholders de pago en ambas
  plantillas.
- `comedores/tests/test_responsable_tarjeta_form.py`, incluyendo el resumen del
  responsable dentro del detalle del comedor.

## Riesgos y rollback

- El catálogo se guarda como texto en el Informe Técnico para preservar su
  contrato histórico; la selección de una localidad depende de la provincia
  elegida en la interfaz.
- La migración `0057_issue_2403_responsable_tarjeta` agrega campos opcionales y
  es reversible con el rollback de la migración antes de aplicar cambios de
  datos.
