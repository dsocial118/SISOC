# VAT: exportación de nóminas en detalle de comisión

## Resumen

Se agregó, dentro del detalle de comisión de cursos (`/vat/cursos/comisiones/<pk>/`), la descarga en Excel de:

- nómina de preinscriptos
- nómina de inscriptos

Ambas opciones quedan visibles en la tarjeta lateral "Ocupación de cupo".

## Alcance funcional

- "Descargar nómina de preinscriptos" exporta todas las inscripciones persistidas de la comisión, incluyendo inscriptos y lista de espera.
- "Descargar nómina de inscriptos" exporta la misma estructura de columnas, pero filtrando solo registros con `estado = inscripta`.
- El archivo incluye:
  - Apellido
  - Nombre
  - DNI / CUIL
  - Fecha de Nacimiento
  - Género
  - Comisión
  - Curso
  - Centro de Formación
  - Estado de Inscripción
  - Fecha de Inscripción
  - Canal de Inscripción
  - Email
  - Teléfono

## Decisión de implementación

- Se centralizó la construcción del Excel en `VAT/services/nomina_export.py` para evitar duplicar lógica entre ambas descargas.
- Se reutilizó el scope existente de comisiones (`_scoped_comisiones_curso_queryset`) para mantener el mismo criterio de acceso que el detalle de comisión.

## Supuesto explícito

- Para "preinscriptos" se tomó como fuente la totalidad de registros `Inscripcion` asociados a `comision_curso`, porque hoy inscriptos y lista de espera ya conviven en la misma tabla y se diferencian por estado.

## Validación

- Se agregaron tests de regresión para:
  - presencia de ambos enlaces en el detalle
  - exportación Excel de preinscriptos
  - exportación Excel de inscriptos filtrando solo `inscripta`
