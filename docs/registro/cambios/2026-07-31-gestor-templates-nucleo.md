# Núcleo del Gestor de templates de Informes Técnicos

Fecha: 2026-07-31

## Alcance de esta etapa

Se incorporó el primer recorte operativo del Gestor de templates:

- plantilla lógica para una combinación de condiciones de admisión;
- código automático;
- versiones en borrador, publicadas e inactivas;
- publicación de una versión y creación de un nuevo borrador desde una versión
  existente;
- inactivación de una plantilla;
- listado y pantallas de gestión protegidas por el nuevo rol `Gestor de
  templates`;
- creación automática del grupo y asignación de su permiso durante la
  migración.

La pantalla se encuentra en `Configuración de Comedores → Gestor de templates`,
como ubicación de navegación. El módulo sólo administra templates de Informe
Técnico.

## Reglas aplicadas

- Las condiciones pertenecen a la plantilla lógica y no se editan en sus
  versiones.
- Sólo puede mantenerse una versión publicada por plantilla lógica.
- Sólo puede publicarse una plantilla para una combinación de condiciones.
- Publicar una nueva versión inactiva la versión publicada anterior.

## Pendiente de la siguiente etapa

La selección contra una admisión y la generación del DOCX todavía usan el
comportamiento existente. El editor visual, variables, componentes, vista
previa e incidencias también quedan pendientes.

## Validación

- Migración `0070` aplicada en el entorno local.
- Pruebas de creación, versiones, publicación, duplicidad, inactivación y
  permisos: aprobadas.
- `black --check`, carga de templates y `makemigrations --check --dry-run`:
  aprobados.
