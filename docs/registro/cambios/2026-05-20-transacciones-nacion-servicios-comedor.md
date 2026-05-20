# Transacciones Nacion Servicios en legajo de comedor

## Contexto

Se ajusto la presentacion de la informacion de Transacciones Nacion Servicios
en el legajo de comedor y en su vista de detalle.

## Cambios

- La tarjeta del legajo usa el mismo ancho que la tarjeta de asistencia por
  rango etareo y queda alineada con el bloque de informacion principal.
- Se removieron colores destacados e iconografia del resumen para mantener una
  presentacion consistente con Detalles de Admision.
- La vista `/comedores/<pk>/transacciones` muestra los registros en grilla con
  el estilo de detalle de expedientes de pagos, sin acciones por fila.
- La grilla de transacciones aumenta el espaciado vertical de filas para mejorar
  lectura.

## Validacion

- `python manage.py check` en Docker sin issues.

