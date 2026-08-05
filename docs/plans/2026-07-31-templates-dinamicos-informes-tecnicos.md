# Roadmap: templates dinámicos de Informes Técnicos

## Alcance acordado

La primera versión reemplazará la selección hardcodeada del DOCX borrador del
Informe Técnico de Comedores. Conserva el circuito posterior existente:
descarga, edición por el técnico y revisión jurídica.

No modifica la documentación requerida por cada tipo de convenio ni los
modelos de Disposición y Convenio.

## Decisiones funcionales confirmadas

- Las validaciones se cargan al iniciar la admisión, junto con la confirmación
  del tipo de convenio heredado desde el Legajo Organización.
- Tipo de convenio y tipo de entidad no se editan desde estas validaciones.
- Los datos nuevos se pueden corregir hasta generar el DOCX borrador del
  Informe Técnico.
- Incorporación: Ex PNUD; si corresponde, estado de convenio PNUD vigente o
  finalizado.
- Renovación: primera o segunda/posterior; financiamiento vigente o finalizado.
- Si no existe una configuración de template aplicable, no se genera el DOCX,
  el Informe Técnico permanece editable y se podrá reportar la incidencia.
- El rol de administración se denomina Gestor de templates.

## Etapas

1. Persistir, validar y permitir corregir las validaciones iniciales sin
   cambiar la documentación heredada.
2. Crear el núcleo de templates: plantilla lógica, versiones, condiciones y
   permisos del Gestor de templates.
3. Registrar la matriz inicial y reemplazar la selección hardcodeada del DOCX
   borrador por la resolución configurable.
4. Incorporar vista previa, reporte de configuraciones faltantes y trazabilidad
   de plantilla y versión usadas.
5. Incorporar editor avanzado, componentes reutilizables y publicación masiva.

## Matriz inicial conocida

Hay catorce combinaciones: seis de Incorporación y ocho de Renovación. Doce
tienen un modelo identificado; las dos pendientes corresponden a Organización
Base + Ex PNUD, con convenio PNUD vigente o finalizado.

Personería Jurídica y Personería Jurídica Eclesiástica comparten modelos hoy,
pero deben conservarse como valores distinguibles para poder configurarlas por
separado si cambia esa regla.
