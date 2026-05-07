# VAT revisor y descarga de nominas de comisiones de curso

## Contexto

El usuario CFPRevisor visualiza centros asignados sin permisos de gestion. En el detalle de comision de curso, la descarga de nominas estaba atada al scope de gestion, por lo que el revisor no podia usar los botones de Excel aunque el caso de uso es de lectura.

## Decision

- La descarga de nominas de comisiones de curso se considera lectura.
- CFPRevisor mantiene permisos sin `add_`, `change_` ni `delete_`, pero suma `VAT.view_comisioncurso` para acceder al detalle y a los endpoints de exportacion.
- Los endpoints de exportacion usan el scope de lectura de comisiones de curso.
- La tarjeta "Acciones rapidas" solo se renderiza cuando hay acciones de gestion disponibles.

## Impacto

- Un revisor asignado al centro puede descargar nomina de preinscriptos e inscriptos.
- El revisor no gana permisos de alta, edicion, baja, asistencia ni gestion de inscripciones.
- La UI deja de mostrar una tarjeta vacia para perfiles solo lectura.
