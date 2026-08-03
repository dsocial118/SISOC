# Templates dinámicos de Informes Técnicos: entrega por etapas

Fecha: 2026-07-31

## Decisión

Implementar el evolutivo por etapas. La primera registra las validaciones de
origen de una admisión. La selección configurable, el renderizado de DOCX, la
vista previa, incidencias y el editor de templates se implementarán en etapas
posteriores.

## Motivo

La documentación requerida actualmente depende de reglas ya consolidadas sobre
el tipo de convenio. Separar estas nuevas variables evita que la futura
clasificación de templates altere ese circuito.

## Consecuencias

- `tipo_convenio` sigue siendo un dato heredado y no editable desde las nuevas
  validaciones.
- El primer alcance del motor cubre solamente el borrador DOCX de Informe
  Técnico.
- Los templates de Disposición y Convenio siguen usando su comportamiento
  actual hasta que exista una definición funcional específica.
