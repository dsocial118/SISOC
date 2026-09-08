# Issue #2005: rendiciones presentadas en Organizaciones

## Cambio funcional

El legajo de una Organización incorpora la pestaña **Rendiciones Presentadas**. La
pestaña reúne las rendiciones de sus comedores, permite filtrarlas por código de
proyecto cuando existe más de uno y ofrece un detalle de lectura con acceso al
módulo operativo de la rendición para usuarios autorizados.

El detalle expone convenio, número, período, monto, hitos y fechas de revisión,
documentos de auditoría, observaciones y regularización.

## Decisiones de compatibilidad

- Hasta completar el Issue #1961, los códigos de proyecto se obtienen del campo
  legado `Comedor.codigo_de_proyecto`. La consulta queda encapsulada en
  `RendicionCuentaMensualService` para poder sustituirla por la futura relación
  `ProyectoOrganizacion`.
- Se incorporan a `RendicionCuentaMensual` los campos de lectura requeridos por
  #2005 y compatibles con las etapas propuestas en #2079.
- Este cambio no implementa las acciones ni la máquina completa de transiciones
  de Auditoría de #2079. Las fechas de cada hito son la fuente explícita para los
  indicadores mostrados y serán completadas por ese flujo operativo.

## Seguridad

El listado reutiliza el alcance de organizaciones visible para el usuario. El
detalle valida simultáneamente la organización de la URL, la relación real de la
rendición y ese alcance, evitando consultar rendiciones de otra organización. El
botón **Ir a Rendición** solo se muestra con el permiso propio del módulo.

## Despliegue

Ejecutar la migración `rendicioncuentasmensual.0014_issue_2005_datos_auditoria`.
Los campos nuevos son retrocompatibles y admiten valores vacíos para rendiciones
existentes.
