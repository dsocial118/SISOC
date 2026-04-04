# VAT - edición de centros con el mismo formulario de alta

Fecha: 2026-04-03

## Qué cambió

- Se unificó la pantalla de edición de centros VAT con la pantalla de alta.
- La ruta `/vat/centros/<id>/editar/` ahora reutiliza el formulario extendido de alta, incluyendo:
  - datos institucionales,
  - ubicación,
  - contacto institucional,
  - contactos adicionales,
  - datos de autoridad responsable.
- La actualización persiste también los datos relacionados que en alta se cargan junto con el centro: autoridad, identificador CUE, ubicación principal y contactos adicionales.
- La edición preserva el estado `activo` existente del centro y no lo reactiva por reutilizar el formulario de alta.

## Motivo

- La edición estaba mostrando un formulario simplificado distinto al flujo de alta, lo que generaba una experiencia inconsistente y dejaba fuera campos que el usuario esperaba editar desde la misma pantalla.

## Validación prevista

- Test de render de la vista de edición con el formulario extendido.
- Test de actualización de entidades relacionadas desde la edición.
