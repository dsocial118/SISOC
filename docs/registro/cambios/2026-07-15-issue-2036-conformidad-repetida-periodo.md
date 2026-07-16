# Issue 2036: conformidad de prestaciones repetida por período

## Cambio

La PWA permite registrar más de una conformidad de prestaciones para un mismo
espacio y período, independientemente del programa del espacio. Cada registro se
conserva en el historial con su respuesta, observaciones, usuario y fecha.

## Implementación

- Se eliminó la validación de duplicados del endpoint de conformidad.
- Se eliminó la restricción única de base de datos sobre espacio y período.
- La pantalla móvil mantiene visible la última validación del período y vuelve a
  ofrecer las acciones para registrar una nueva.
- Se actualizaron las pruebas de API para Alimentar Comunidad y para otros
  programas.

## Despliegue

Requiere aplicar la migración `comedores.0047_remove_conformidad_periodo_unique`.
